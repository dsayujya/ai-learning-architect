"""
PathInferenceEngine - LangGraph-orchestrated ML pipeline.

Manages the complete inference flow:
  Goal -> Embedding -> Graph Search -> GNN Sequencing -> Resource Enrichment -> JSON Output

All logic is model-driven. Zero hardcoded paths, zero if-statement routing.
The LangGraph StateGraph ensures deterministic, inspectable stage transitions.
"""

from typing import TypedDict, List, Dict, Optional
import os

from langgraph.graph import StateGraph, END
from app.engine.self_trained_encoder import SelfTrainedEncoder

from app.engine.intent_parser import IntentParser
from app.engine.knowledge_graph import KnowledgeGraph
from app.engine.gnn_sequencer import GNNSequencer, GNNTrainer
from app.engine.sequence_optimizer import SequenceOptimizer


class AgentState(TypedDict):
    """Full pipeline state flowing through LangGraph stages."""
    goal: str
    current_skills: List[str]
    # Stage 1: Intent resolution
    target_nodes: List[str]
    confidence_scores: List[float]
    extracted_skills: List[str]
    # Stage 2: Graph navigation
    path_nodes: List[str]
    known_nodes: List[str]
    # Stage 3: GNN sequencing
    ordered_nodes: List[str]
    readiness_scores: List[float]
    priorities: List[str]
    # Stage 4: Enriched output
    roadmap: List[dict]


class PathInferenceEngine:
    """
    Encapsulates the entire ML pipeline:
      Goal -> Embedding -> Graph Search -> GNN Sequencing -> Enriched JSON Output

    Components:
      1. SentenceTransformer (shared) - 384-dim embeddings for all text
      2. IntentParser          - FAISS index for goal -> node resolution
      3. KnowledgeGraph        - Dijkstra on embedding-weighted edges
      4. GNNSequencer          - GAT for readiness scoring and priority prediction
      5. SequenceOptimizer     - CrossEncoder for YouTube resource ranking
    """

    def __init__(self, cur_graph_path: str):
        print("=" * 60)
        print("  PathInferenceEngine - Initializing ML Pipeline")
        print("=" * 60)

        # 1. Self-trained LSA semantic encoder (replaces SentenceTransformer)
        print("\n[1/5] Initializing SelfTrainedEncoder...")
        self.model = SelfTrainedEncoder(n_components=12)
        self.model.train_on_curriculum(cur_graph_path)

        # 2. FAISS-based intent resolver
        print("[2/5] Building FAISS intent index...")
        self.intent_parser = IntentParser(model=self.model)
        self.intent_parser.build_index(cur_graph_path)

        # 3. Weighted knowledge graph with embedding-based edge costs
        print("[3/5] Loading weighted knowledge graph...")
        self.kg = KnowledgeGraph(cur_graph_path, model=self.model)

        # 4. GNN sequencer with self-supervised pre-training
        print("[4/5] Initializing GNN sequencer...")
        self.gnn = GNNSequencer(in_dim=13, hidden_dim=128)
        self._pretrain_gnn()

        # 5. Semantic resource ranker (uses custom encoder)
        print("[5/5] Initializing Resource Optimizer...")
        self.optimizer = SequenceOptimizer(model=self.model)

        # 6. Build LangGraph state machine
        self.graph = self._build_graph()

        print("\n" + "=" * 60)
        print("  Pipeline ready. All models loaded.")
        print("=" * 60)

    def _pretrain_gnn(self):
        """Self-supervised GNN pre-training on the full curriculum graph."""
        trainer = GNNTrainer(self.gnn, lr=0.005)

        node_list = list(self.kg.graph.nodes())
        features, adj, target_readiness, target_priority = (
            trainer.prepare_training_data(
                self.kg.graph, self.kg.node_embeddings, node_list
            )
        )
        trainer.train(
            features, adj, target_readiness, target_priority, epochs=300
        )

    def _build_graph(self):
        """Build the 4-stage LangGraph pipeline."""
        workflow = StateGraph(AgentState)

        workflow.add_node("embed_intent", self.embed_intent)
        workflow.add_node("navigate_graph", self.navigate_graph)
        workflow.add_node("gnn_sequence", self.gnn_sequence)
        workflow.add_node("enrich_resources", self.enrich_resources)

        workflow.set_entry_point("embed_intent")
        workflow.add_edge("embed_intent", "navigate_graph")
        workflow.add_edge("navigate_graph", "gnn_sequence")
        workflow.add_edge("gnn_sequence", "enrich_resources")
        workflow.add_edge("enrich_resources", END)

        return workflow.compile()

    # ── LangGraph Stage Handlers ────────────────────────────────────

    def embed_intent(self, state: AgentState):
        """Stage 1: Resolve user goal to target nodes via FAISS embedding search."""
        results = self.intent_parser.resolve_intent(state["goal"])

        return {
            "target_nodes": [r[0] for r in results],
            "extracted_skills": [r[1] for r in results],
            "confidence_scores": [r[2] for r in results],
        }

    def navigate_graph(self, state: AgentState):
        """Stage 2: Find optimal paths through weighted knowledge graph via Dijkstra."""
        # Match user's skill descriptions to graph nodes via embedding similarity
        known_nodes = self.kg.match_skills_to_nodes(state["current_skills"])

        # Dijkstra pathfinding with learned edge weights
        path_nodes = self.kg.find_optimal_paths(
            state["target_nodes"], known_nodes
        )

        return {
            "path_nodes": list(path_nodes),
            "known_nodes": list(known_nodes),
        }

    def gnn_sequence(self, state: AgentState):
        """Stage 3: GNN predicts optimal learning order and priority classification."""
        path_nodes = state["path_nodes"]

        if not path_nodes:
            return {
                "ordered_nodes": [],
                "readiness_scores": [],
                "priorities": [],
            }

        # 1. Run GNN on the full graph to ensure stable predictions matching training distribution
        node_list_full = list(self.kg.graph.nodes())
        trainer = GNNTrainer(self.gnn)
        features_full, adj_full, _, _ = trainer.prepare_training_data(
            self.kg.graph, self.kg.node_embeddings, node_list_full
        )

        readiness_scores_full, priorities_full = self.gnn.predict(features_full, adj_full)
        node_to_idx_full = {node: i for i, node in enumerate(node_list_full)}

        # Create mapping of node -> score/priority
        readiness_map = {node: readiness_scores_full[node_to_idx_full[node]] for node in path_nodes}
        priority_map = {node: priorities_full[node_to_idx_full[node]] for node in path_nodes}

        # 2. Perform GNN-guided Kahn's topological sort to guarantee strict dependency ordering
        subgraph = self.kg.graph.subgraph(path_nodes).copy()
        
        in_degree = {u: 0 for u in subgraph.nodes()}
        for u, v in subgraph.edges():
            in_degree[v] += 1

        queue = [u for u in subgraph.nodes() if in_degree[u] == 0]
        # Sort queue: highest readiness score first
        queue.sort(key=lambda x: readiness_map[x], reverse=True)

        ordered_nodes = []
        while queue:
            curr = queue.pop(0)
            ordered_nodes.append(curr)

            for succ in list(subgraph.successors(curr)):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

            # Re-sort queue to pick the highest readiness node next
            queue.sort(key=lambda x: readiness_map[x], reverse=True)

        # Safety fallback: ensure no nodes are lost if a cycle is ever introduced
        if len(ordered_nodes) < len(path_nodes):
            remaining = [n for n in path_nodes if n not in ordered_nodes]
            remaining.sort(key=lambda x: readiness_map[x], reverse=True)
            ordered_nodes.extend(remaining)

        # Retrieve scores and priorities in the final topological order
        ordered_readiness = [readiness_map[node] for node in ordered_nodes]
        ordered_priorities = [priority_map[node] for node in ordered_nodes]

        return {
            "ordered_nodes": ordered_nodes,
            "readiness_scores": ordered_readiness,
            "priorities": ordered_priorities,
        }

    def enrich_resources(self, state: AgentState):
        """Stage 4: Cross-Encoder ranks YouTube resources for each node."""
        if not state["ordered_nodes"]:
            return {"roadmap": []}

        subgraph = self.kg.graph.subgraph(state["path_nodes"]).copy()

        roadmap = self.optimizer.enrich_roadmap(
            subgraph,
            state["ordered_nodes"],
            state["readiness_scores"],
            state["priorities"],
        )

        return {"roadmap": roadmap}

    # ── Public API ──────────────────────────────────────────────────

    def generate_roadmap(self, goal: str, current_skills: List[str]):
        """
        Run the complete ML pipeline.

        Args:
            goal: Free-text career/learning goal
            current_skills: List of skill descriptions the user already knows

        Returns:
            Final AgentState dict with all pipeline outputs
        """
        initial_state: AgentState = {
            "goal": goal,
            "current_skills": current_skills,
            "target_nodes": [],
            "confidence_scores": [],
            "extracted_skills": [],
            "path_nodes": [],
            "known_nodes": [],
            "ordered_nodes": [],
            "readiness_scores": [],
            "priorities": [],
            "roadmap": [],
        }
        return self.graph.invoke(initial_state)


# Backward compatibility alias for ui.py
LearningOrchestrator = PathInferenceEngine
