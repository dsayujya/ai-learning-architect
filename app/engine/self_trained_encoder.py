import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import Pipeline
from sklearn.metrics.pairwise import cosine_similarity

class SelfTrainedEncoder:
    """
    Dynamically self-trained text embedding model.
    Learns the vocabulary and latent semantics directly from the curriculum graph at startup,
    removing the need for external pre-trained HuggingFace models.
    """
    def __init__(self, n_components=12):
        self.n_components = n_components
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                stop_words='english', 
                max_features=500,
                token_pattern=r"(?u)[a-zA-Z0-9#\+]+"
            )),
            ('svd', TruncatedSVD(n_components=self.n_components, random_state=42))
        ])
        self.is_trained = False
        self._vocab_corpus = []

    def train_on_curriculum(self, graph_path: str):
        """Fit the LSA model on the curriculum topics to learn the latent space."""
        print("[SelfTrainedEncoder] Extracting vocabulary from curriculum...")
        try:
            with open(graph_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle both formats: list of dicts directly, or a dict with a 'nodes' key
            nodes = data.get("nodes", []) if isinstance(data, dict) else data
            for node in nodes:
                topic = node.get("topic", node.get("id", ""))
                desc = node.get("description", node.get("search_text", ""))
                self._vocab_corpus.append(f"{topic} {desc}")
                
            # Ensure we don't request more components than samples
            n_samples = len(self._vocab_corpus)
            if n_samples < self.n_components:
                self.pipeline.set_params(svd__n_components=max(1, n_samples - 1))

            print(f"[SelfTrainedEncoder] Training LSA model on {len(self._vocab_corpus)} topics...")
            self.pipeline.fit(self._vocab_corpus)
            self.is_trained = True
            print("[SelfTrainedEncoder] Training complete. Local embedding space established.")
            
        except Exception as e:
            print(f"[SelfTrainedEncoder] Warning: Auto-training failed: {e}")

    def encode(self, texts, show_progress_bar=False):
        """
        Encode a list of strings (or a single string) into dense vectors.
        Signature matches sentence-transformers for drop-in replacement.
        """
        if not self.is_trained:
            print("[SelfTrainedEncoder] Warning: Called encode before training, returning zeros.")
            n_dims = self.pipeline.named_steps['svd'].n_components
            if isinstance(texts, str):
                return np.zeros((1, n_dims))
            return np.zeros((len(texts), n_dims))

        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
            
        vectors = self.pipeline.transform(texts)
        
        # Normalize vectors for cosine similarity compatibility
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10  # Prevent division by zero
        normalized = vectors / norms
        
        if is_single:
            return normalized[0]
        return normalized

