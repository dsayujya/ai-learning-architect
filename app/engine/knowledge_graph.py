"""
Weighted Knowledge Graph with embedding-based edge costs and Dijkstra pathfinding.

Edge weights are computed from a combination of complexity differential and
semantic distance between connected topics. This allows the graph navigator
to discover optimal learning paths that minimize cognitive load, rather than
blindly collecting all ancestors.

Path expansion ensures comprehensive roadmaps by collecting full dependency
trees and semantically related neighbors when paths are too short.
"""

import json
import numpy as np
import networkx as nx
from typing import List, Set, Dict


class KnowledgeGraph:
    """
    Curriculum graph with model-driven edge weights and Dijkstra navigation.

    Each edge weight = alpha * |delta_complexity| + beta * (1 - cosine_sim)
    where cosine_sim is computed from sentence-transformer embeddings.
    """

    # Minimum number of nodes for a useful roadmap
    MIN_PATH_SIZE = 6
    # Maximum path size to prevent overwhelming roadmaps
    MAX_PATH_SIZE = 20

    def __init__(self, data_path: str, model=None):
        """
        Args:
            data_path: Path to the curriculum JSON file
            model: Shared SelfTrainedEncoder for computing node embeddings
        """
        self.graph = nx.DiGraph()
        self.node_embeddings: Dict[str, np.ndarray] = {}
        self._model = model
        self._load_graph(data_path)

    def _load_graph(self, data_path: str):
        """Load graph structure, compute embeddings, and set edge weights."""
        with open(data_path, 'r') as f:
            data = json.load(f)

        # Add all nodes
        for item in data:
            self.graph.add_node(
                item['id'],
                topic=item['topic'],
                complexity=item['complexity']
            )

        # Compute node embeddings if a transformer model is available
        # Use search_text for richer semantic representations
        if self._model is not None:
            texts = [
                item.get('search_text', item['topic']) for item in data
            ]
            ids = [item['id'] for item in data]
            embeddings = self._model.encode(texts)
            for node_id, emb in zip(ids, embeddings):
                self.node_embeddings[node_id] = emb
            print(f"[Knowledge Graph] Computed embeddings for {len(ids)} nodes")

        # Add edges with learned weights
        for item in data:
            for prereq in item.get('prerequisites', []):
                weight = self._compute_edge_weight(prereq, item['id'])
                self.graph.add_edge(prereq, item['id'], weight=weight)

        print(
            f"[Knowledge Graph] Loaded {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} weighted edges"
        )

    def _compute_edge_weight(self, source: str, target: str) -> float:
        """
        Compute edge weight from embeddings and complexity.

        Weight = alpha * |delta_complexity| + beta * (1 - cosine_similarity)

        Lower weight = easier transition:
          - Semantically similar topics (high cosine_sim) are cheaper
          - Small complexity jumps are cheaper
        """
        c_source = self.graph.nodes[source].get('complexity', 1)
        c_target = self.graph.nodes[target].get('complexity', 1)
        complexity_delta = abs(c_target - c_source) / 10.0  # Normalize to [0, 1]

        if source in self.node_embeddings and target in self.node_embeddings:
            cos_sim = float(
                np.dot(self.node_embeddings[source], self.node_embeddings[target])
            )
            semantic_distance = 1.0 - cos_sim
        else:
            semantic_distance = 0.5  # Neutral fallback

        return complexity_delta + semantic_distance

    def _collect_relevant_ancestors(
        self, node: str, target_nodes: List[str]
    ) -> Set[str]:
        """
        Collect prerequisite ancestors that are semantically relevant to the
        target goals. Prunes ancestor chains that drift too far off-topic.

        This prevents scenarios like DevOps pulling in the entire ML chain
        just because MLOps depends on PyTorch.
        """
        # Compute target direction for relevance filtering
        target_embs = []
        for t in target_nodes:
            if t in self.node_embeddings:
                target_embs.append(self.node_embeddings[t])

        has_relevance_filter = bool(target_embs) and bool(self.node_embeddings)
        if has_relevance_filter:
            goal_direction = np.mean(target_embs, axis=0)
            goal_direction = goal_direction / (np.linalg.norm(goal_direction) + 1e-9)

        ancestors = set()
        # BFS: collect ancestors, pruning branches that are off-topic
        stack = [node]
        while stack:
            current = stack.pop()
            for pred in self.graph.predecessors(current):
                if pred in ancestors:
                    continue

                # Check if this ancestor is semantically related
                if has_relevance_filter and pred in self.node_embeddings:
                    sim = float(np.dot(self.node_embeddings[pred], goal_direction))
                    if sim < 0.15:
                        # Too distant from the goal — skip this branch
                        continue

                ancestors.add(pred)
                stack.append(pred)
        return ancestors

    def _expand_with_semantic_neighbors(
        self, path_nodes: Set[str], target_nodes: List[str], min_size: int
    ) -> Set[str]:
        """
        If the path is still too small, expand by adding semantically relevant
        neighbor nodes (successors and siblings of current path nodes).

        Only adds nodes that are direct graph neighbors of existing path nodes
        and have semantic similarity >= 0.20 to the targets.
        """
        if len(path_nodes) >= min_size or not self.node_embeddings:
            return path_nodes

        # Compute average target embedding as the "goal direction"
        target_embs = []
        for t in target_nodes:
            if t in self.node_embeddings:
                target_embs.append(self.node_embeddings[t])
        if not target_embs:
            return path_nodes

        goal_direction = np.mean(target_embs, axis=0)
        goal_direction = goal_direction / (np.linalg.norm(goal_direction) + 1e-9)

        # Collect candidate neighbors: successors + sibling nodes
        candidate_set = set()
        for node in list(path_nodes):
            # Direct successors
            for neighbor in self.graph.successors(node):
                if neighbor not in path_nodes:
                    candidate_set.add(neighbor)
            # Siblings: other children of node's predecessors
            for pred in self.graph.predecessors(node):
                for sibling in self.graph.successors(pred):
                    if sibling not in path_nodes:
                        candidate_set.add(sibling)

        # Score all candidates by similarity to goal
        candidates = []
        for neighbor in candidate_set:
            if neighbor in self.node_embeddings:
                sim = float(np.dot(self.node_embeddings[neighbor], goal_direction))
                candidates.append((neighbor, sim))

        # Sort by relevance and add best candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        expanded = set(path_nodes)
        for node, sim in candidates:
            if len(expanded) >= min_size:
                break
            if sim >= 0.20:
                expanded.add(node)

        return expanded

    def _prune_to_max_size(
        self, path_nodes: Set[str], target_nodes: List[str]
    ) -> Set[str]:
        """
        If path exceeds MAX_PATH_SIZE, keep only the most relevant nodes.
        Always preserves target nodes.
        """
        if not self.node_embeddings:
            return path_nodes

        # Compute goal direction
        target_embs = []
        for t in target_nodes:
            if t in self.node_embeddings:
                target_embs.append(self.node_embeddings[t])
        if not target_embs:
            return path_nodes

        goal_direction = np.mean(target_embs, axis=0)
        goal_direction = goal_direction / (np.linalg.norm(goal_direction) + 1e-9)

        # Score all nodes by relevance and keep the best ones
        target_set = set(target_nodes)
        scored = []
        for node in path_nodes:
            if node in target_set:
                scored.append((node, float('inf')))  # Always keep targets
            elif node in self.node_embeddings:
                sim = float(np.dot(self.node_embeddings[node], goal_direction))
                scored.append((node, sim))
            else:
                scored.append((node, 0.0))

        scored.sort(key=lambda x: x[1], reverse=True)
        return {node for node, _ in scored[:self.MAX_PATH_SIZE]}

    def find_optimal_paths(
        self, target_nodes: List[str], known_nodes: Set[str] = None
    ) -> Set[str]:
        """
        Find the comprehensive set of nodes to reach all targets.

        Strategy:
        1. Dijkstra shortest path from sources to each target
        2. Full ancestor collection for each target (complete dependency tree)
        3. Semantic neighbor expansion if path is still too small

        Args:
            target_nodes: Node IDs the user wants to learn
            known_nodes: Node IDs the user already knows (act as path sources)

        Returns:
            Set of node IDs forming the comprehensive learning path
        """
        if not target_nodes:
            return set()

        known_nodes = known_nodes or set()

        # Source candidates: graph roots + user's known nodes
        root_nodes = {
            n for n in self.graph.nodes() if self.graph.in_degree(n) == 0
        }
        source_nodes = root_nodes | known_nodes

        required_nodes = set()

        for target in target_nodes:
            if target not in self.graph:
                continue
            if target in known_nodes:
                continue

            # Step 1: Dijkstra shortest path (keeps the optimal backbone)
            best_path = None
            best_cost = float('inf')

            for source in source_nodes:
                if source not in self.graph:
                    continue
                try:
                    cost = nx.dijkstra_path_length(
                        self.graph, source, target, weight='weight'
                    )
                    if cost < best_cost:
                        best_cost = cost
                        best_path = nx.dijkstra_path(
                            self.graph, source, target, weight='weight'
                        )
                except nx.NetworkXNoPath:
                    continue

            if best_path:
                required_nodes.update(best_path)

            # Step 2: Collect semantically-relevant ancestor tree for the target
            ancestors = self._collect_relevant_ancestors(target, target_nodes)
            required_nodes.update(ancestors)
            required_nodes.add(target)

        # Step 3: Semantic neighbor expansion if path is too small
        required_nodes = self._expand_with_semantic_neighbors(
            required_nodes, target_nodes, self.MIN_PATH_SIZE
        )

        # Step 4: Cap the path size to prevent overwhelming roadmaps
        if len(required_nodes) > self.MAX_PATH_SIZE:
            required_nodes = self._prune_to_max_size(
                required_nodes, target_nodes
            )

        # Remove nodes the user already knows
        remaining = required_nodes - known_nodes

        print(
            f"[Graph Navigator] Targets: {target_nodes} | "
            f"Full path nodes: {len(required_nodes)} | "
            f"After filtering known: {len(remaining)}"
        )
        return remaining

    def match_skills_to_nodes(self, skill_strings: List[str]) -> Set[str]:
        """
        Match user-provided skill strings to graph nodes via embedding similarity.

        Replaces the old substring/exact-match approach with pure cosine similarity.
        Each skill string is embedded and matched to the most similar graph node
        if the similarity exceeds a learned threshold.
        """
        if not skill_strings or not self.node_embeddings or self._model is None:
            return set()

        # Encode user-provided skill descriptions
        skill_embeddings = self._model.encode(skill_strings)

        node_ids = list(self.node_embeddings.keys())
        node_embs = np.array([self.node_embeddings[nid] for nid in node_ids])

        matched = set()
        for skill_str, skill_emb in zip(skill_strings, skill_embeddings):
            similarities = np.dot(node_embs, skill_emb)
            best_idx = int(np.argmax(similarities))
            best_sim = float(similarities[best_idx])

            # Only match if similarity is semantically meaningful
            if best_sim >= 0.40:
                matched.add(node_ids[best_idx])
                print(
                    f"[Skill Match] '{skill_str}' -> "
                    f"{node_ids[best_idx]} (sim: {best_sim:.3f})"
                )

        return matched
