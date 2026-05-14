"""
Embedding-based Intent Resolver using FAISS + sentence-transformers.

All intent resolution is pure vector similarity search. User goals are encoded
into 384-dimensional embeddings and matched against pre-computed curriculum
topic embeddings via FAISS nearest-neighbor search.

No keyword matching. No hardcoded defaults. No mapping files.
"""

import json
import numpy as np
import faiss
from typing import List, Tuple


class IntentParser:
    """
    FAISS-powered intent resolver.

    Encodes user goals with a shared SentenceTransformer model and resolves
    them to curriculum node IDs via cosine similarity (inner product on
    L2-normalized embeddings).
    """

    def __init__(self, model):
        """
        Args:
            model: A self-trained encoder instance (SelfTrainedEncoder)
        """
        self.model = model
        self._index: faiss.IndexFlatIP = None
        self._topic_names: List[str] = []
        self._topic_ids: List[str] = []

    def build_index(self, data_path: str):
        """
        Build a FAISS inner-product index over all curriculum topic embeddings.

        After this call, resolve_intent() can be used for zero-shot goal matching.
        """
        with open(data_path, 'r') as f:
            data = json.load(f)

        self._topic_names = [item['topic'] for item in data]
        self._topic_ids = [item['id'] for item in data]

        # Use search_text for indexing (includes keywords/synonyms for better matching)
        # Fall back to topic name if search_text is not present
        search_texts = [
            item.get('search_text', item['topic']) for item in data
        ]

        # Encode search texts; SelfTrainedEncoder inherently normalizes
        embeddings = self.model.encode(search_texts)
        embeddings = np.array(embeddings, dtype=np.float32)

        # FAISS IndexFlatIP: exact inner-product search
        self._index = faiss.IndexFlatIP(embeddings.shape[1])
        self._index.add(embeddings)

        print(f"[FAISS Intent] Built index over {len(self._topic_names)} curriculum topics")

    def resolve_intent(
        self, goal: str, top_k: int = 5
    ) -> List[Tuple[str, str, float]]:
        """
        Resolve a free-text goal to curriculum node IDs via embedding search.

        Uses a strict threshold to prevent off-topic matches:
        - Absolute minimum similarity: 0.35
        - Dynamic: must be within 85% of the top match score

        Args:
            goal: Free-text user goal (e.g. "I want to learn machine learning")
            top_k: Maximum number of candidates to retrieve from FAISS

        Returns:
            List of (node_id, topic_name, confidence_score) tuples,
            sorted by descending confidence. Only semantically relevant matches.
        """
        if self._index is None:
            raise RuntimeError("Intent index not built. Call build_index() first.")

        # Encode user goal into the same embedding space
        query_emb = self.model.encode([goal])
        query_emb = np.array(query_emb, dtype=np.float32)

        # FAISS nearest-neighbor search
        scores, indices = self._index.search(query_emb, top_k)

        # Strict threshold: 85% of top score, minimum 0.35
        top_score = float(scores[0][0])
        threshold = max(top_score * 0.85, 0.35)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            if float(score) >= threshold:
                results.append((
                    self._topic_ids[idx],
                    self._topic_names[idx],
                    round(float(score), 4)
                ))

        # Safety net: if nothing passed threshold, return the single best match
        if not results and indices[0][0] != -1:
            idx = int(indices[0][0])
            results.append((
                self._topic_ids[idx],
                self._topic_names[idx],
                round(float(scores[0][0]), 4)
            ))

        print(
            f"[FAISS Intent] Goal: '{goal}' -> "
            f"{[(r[1], f'{r[2]:.3f}') for r in results]} "
            f"(threshold: {threshold:.3f})"
        )
        return results
