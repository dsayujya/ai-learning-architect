"""
Graph Neural Network Sequencer for optimal learning path prediction.

Implements a 2-layer Graph Attention Network (GAT) in pure PyTorch that predicts:
1. Node readiness scores - how suitable each topic is as the next learning step
2. Priority classification - Critical/High/Medium based on learned graph structure

The model is self-supervised: topological ordering of the curriculum graph provides
implicit training signal, so prerequisite nodes naturally score higher readiness
than advanced topics. At inference time, the GNN runs on the user-specific subgraph,
adapting dynamically to what the learner already knows.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import networkx as nx
import numpy as np
from typing import List, Dict, Tuple


PRIORITY_LABELS = ["Medium", "High", "Critical"]


class GraphAttentionLayer(nn.Module):
    """GAT-style attention layer for message passing over curriculum graphs."""

    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.W = nn.Linear(in_features, out_features, bias=False)
        self.attn = nn.Linear(2 * out_features, 1, bias=False)
        self.leaky_relu = nn.LeakyReLU(0.2)

    def forward(self, h: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        Args:
            h: Node features [N, in_features]
            adj: Adjacency matrix [N, N] with self-loops (1=edge, 0=no edge)
        Returns:
            Updated node features [N, out_features]
        """
        Wh = self.W(h)
        N = Wh.size(0)

        # Pairwise attention: compute score for every (i, j) pair
        Wh_i = Wh.unsqueeze(1).expand(-1, N, -1)  # [N, N, out_features]
        Wh_j = Wh.unsqueeze(0).expand(N, -1, -1)   # [N, N, out_features]
        e = self.leaky_relu(
            self.attn(torch.cat([Wh_i, Wh_j], dim=-1)).squeeze(-1)
        )  # [N, N]

        # Mask non-edges with -inf so they get zero attention after softmax
        e = e.masked_fill(adj == 0, float('-inf'))

        # Attention weights with numerical stability for isolated nodes
        alpha = F.softmax(e, dim=-1)
        alpha = torch.nan_to_num(alpha, nan=0.0)

        # Aggregate neighbor messages weighted by attention
        return F.elu(torch.matmul(alpha, Wh))


class GNNSequencer(nn.Module):
    """
    2-layer Graph Attention Network for learning-path sequencing.

    Input features per node: 385 dimensions
        - 384 from sentence-transformer topic embedding
        - 1 normalized complexity scalar

    Outputs:
        - readiness: [N] scores in [0,1] - higher means "learn this sooner"
        - priority_logits: [N, 3] - classification into Medium / High / Critical
    """

    def __init__(self, in_dim: int = 385, hidden_dim: int = 128):
        super().__init__()
        self.layer1 = GraphAttentionLayer(in_dim, hidden_dim)
        self.layer2 = GraphAttentionLayer(hidden_dim, hidden_dim)

        self.readiness_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

        self.priority_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 3)
        )

    def forward(
        self, h: torch.Tensor, adj: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.layer1(h, adj)
        h = F.dropout(h, p=0.1, training=self.training)
        h = self.layer2(h, adj)

        readiness = self.readiness_head(h).squeeze(-1)   # [N]
        priority_logits = self.priority_head(h)            # [N, 3]

        return readiness, priority_logits

    @torch.no_grad()
    def predict(
        self, h: torch.Tensor, adj: torch.Tensor
    ) -> Tuple[List[float], List[str]]:
        """Run inference and return human-readable results."""
        self.eval()
        readiness, priority_logits = self(h, adj)

        scores = readiness.cpu().tolist()
        priorities = [
            PRIORITY_LABELS[i]
            for i in priority_logits.argmax(dim=-1).cpu().tolist()
        ]

        return scores, priorities


class GNNTrainer:
    """
    Self-supervised trainer for the GNN sequencer.

    Training signals derived entirely from graph structure:
    1. Topological ordering -> readiness targets (earlier = higher readiness)
    2. Node complexity -> priority classification targets
    3. Graph connectivity -> attention patterns learned implicitly by GAT layers
    """

    def __init__(self, model: GNNSequencer, lr: float = 0.005):
        self.model = model
        self.optimizer = torch.optim.Adam(
            model.parameters(), lr=lr, weight_decay=1e-4
        )

    def prepare_training_data(
        self,
        graph: nx.DiGraph,
        node_embeddings: Dict[str, np.ndarray],
        node_list: List[str]
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Convert NetworkX graph + embeddings into PyTorch tensors.

        Returns: (features, adjacency, target_readiness, target_priority)
        """
        n = len(node_list)
        node_to_idx = {node: i for i, node in enumerate(node_list)}

        # Build feature matrix: [embedding(384) | normalized_complexity(1)]
        features = []
        for node in node_list:
            emb = node_embeddings[node]
            complexity = graph.nodes[node].get('complexity', 1) / 10.0
            features.append(np.concatenate([emb, [complexity]]))
        features = torch.tensor(np.array(features), dtype=torch.float32)

        # Adjacency with self-loops and bidirectional edges for message passing
        adj = torch.eye(n)
        for u, v in graph.edges():
            if u in node_to_idx and v in node_to_idx:
                adj[node_to_idx[u], node_to_idx[v]] = 1.0
                adj[node_to_idx[v], node_to_idx[u]] = 1.0

        # Target readiness: inverse of topological position
        try:
            topo_order = list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            topo_order = node_list

        target_readiness = torch.zeros(n)
        topo_in_list = [node for node in topo_order if node in node_to_idx]
        for i, node in enumerate(topo_in_list):
            idx = node_to_idx[node]
            target_readiness[idx] = 1.0 - (i / max(len(topo_in_list) - 1, 1))

        # Target priority from complexity thresholds
        target_priority = torch.zeros(n, dtype=torch.long)
        for i, node in enumerate(node_list):
            c = graph.nodes[node].get('complexity', 1)
            if c >= 8:
                target_priority[i] = 2   # Critical
            elif c >= 5:
                target_priority[i] = 1   # High
            # else 0 = Medium

        return features, adj, target_readiness, target_priority

    def train(
        self,
        features: torch.Tensor,
        adj: torch.Tensor,
        target_readiness: torch.Tensor,
        target_priority: torch.Tensor,
        epochs: int = 300
    ):
        """Run self-supervised pre-training loop."""
        self.model.train()

        for epoch in range(epochs):
            self.optimizer.zero_grad()
            readiness, priority_logits = self.model(features, adj)

            loss_readiness = F.mse_loss(readiness, target_readiness)
            loss_priority = F.cross_entropy(priority_logits, target_priority)
            loss = loss_readiness + 0.5 * loss_priority

            loss.backward()
            self.optimizer.step()

            if (epoch + 1) % 100 == 0:
                print(
                    f"[GNN Pre-training] Epoch {epoch+1}/{epochs} | "
                    f"Loss: {loss.item():.4f} "
                    f"(readiness: {loss_readiness.item():.4f}, "
                    f"priority: {loss_priority.item():.4f})"
                )

    @staticmethod
    def build_subgraph_tensors(
        subgraph: nx.DiGraph,
        node_embeddings: Dict[str, np.ndarray],
        node_list: List[str]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Build feature and adjacency tensors for a user-specific subgraph at inference time."""
        n = len(node_list)
        node_to_idx = {node: i for i, node in enumerate(node_list)}

        features = []
        for node in node_list:
            emb = node_embeddings[node]
            complexity = subgraph.nodes[node].get('complexity', 1) / 10.0
            features.append(np.concatenate([emb, [complexity]]))
        features = torch.tensor(np.array(features), dtype=torch.float32)

        adj = torch.eye(n)
        for u, v in subgraph.edges():
            if u in node_to_idx and v in node_to_idx:
                adj[node_to_idx[u], node_to_idx[v]] = 1.0
                adj[node_to_idx[v], node_to_idx[u]] = 1.0

        return features, adj
