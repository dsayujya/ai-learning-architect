"""
Resource Enrichment Engine with Cross-Encoder semantic ranking.

Fetches YouTube tutorial candidates for each learning topic, then uses
a Cross-Encoder transformer model to rank candidates by semantic relevance
to the curriculum topic. No hardcoded fallback video IDs.

Includes retry logic and graceful degradation — a failed YouTube fetch
never crashes the pipeline.
"""

import urllib.request
import urllib.parse
import re
import sys
import time
import numpy as np
from typing import List, Dict, Optional, Tuple

# Fix Windows console encoding for emoji in video titles
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


class SequenceOptimizer:
    """
    Enriches roadmap nodes with semantically-ranked YouTube resources.

    Uses a Cross-Encoder model (cross-encoder/ms-marco-MiniLM-L-6-v2) to score
    (topic, video_title) pairs and select the most relevant tutorial.
    """

    MAX_RETRIES = 2
    RETRY_DELAY = 1.5  # seconds
    REQUEST_TIMEOUT = 12  # seconds

    def __init__(self, model):
        self._model = model
        self._yt_cache: Dict[str, Tuple[Optional[str], Optional[float]]] = {}
        print("[SequenceOptimizer] Using SelfTrainedEncoder for YouTube candidate ranking")

    def _fetch_youtube_candidates(
        self, topic: str, max_results: int = 5
    ) -> List[Tuple[str, str]]:
        """
        Fetch multiple YouTube video candidates with titles.
        Includes retry logic for transient failures.

        Returns:
            List of (video_id, video_title) tuples for CrossEncoder scoring
        """
        last_error = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                query = urllib.parse.quote(f"{topic} full course tutorial")
                url = (
                    f"https://www.youtube.com/results?search_query={query}"
                    f"&sp=EgIQAQ%253D%253D"
                )
                req = urllib.request.Request(url, headers={
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/120.0.0.0 Safari/537.36'
                    ),
                    'Accept-Language': 'en-US,en;q=0.9'
                })
                response = urllib.request.urlopen(req, timeout=self.REQUEST_TIMEOUT)
                html = response.read().decode('utf-8', errors='replace')

                # Try to extract (videoId, title) pairs from videoRenderer JSON blocks
                pairs = re.findall(
                    r'"videoRenderer":\{"videoId":"([a-zA-Z0-9_-]{11})"'
                    r'.+?"title":\{"runs":\[\{"text":"([^"]+)"',
                    html
                )

                if pairs:
                    seen = set()
                    candidates = []
                    for vid, title in pairs:
                        if vid not in seen:
                            seen.add(vid)
                            candidates.append((vid, title))
                            if len(candidates) >= max_results:
                                break
                    return candidates

                # Fallback: extract just video IDs (titles unknown)
                raw_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
                seen = set()
                candidates = []
                for vid in raw_ids:
                    if vid not in seen:
                        seen.add(vid)
                        # Use search query as proxy title for CrossEncoder scoring
                        candidates.append((vid, f"{topic} - Tutorial"))
                        if len(candidates) >= max_results:
                            break

                if candidates:
                    return candidates

                # If we got HTML but no results, don't retry
                print(f"[YouTube Fetch] No video IDs found in HTML for '{topic}'")
                return []

            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    print(
                        f"[YouTube Fetch] Attempt {attempt + 1} failed for "
                        f"'{topic}': {e}. Retrying in {self.RETRY_DELAY}s..."
                    )
                    time.sleep(self.RETRY_DELAY)
                else:
                    print(
                        f"[YouTube Fetch] All {self.MAX_RETRIES + 1} attempts "
                        f"failed for '{topic}': {last_error}"
                    )

        return []

    def rank_and_select(
        self, topic: str
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Fetch YouTube candidates and rank them with the Cross-Encoder.

        Returns:
            (best_video_id, relevance_score) or (None, None) if no results
        """
        if topic in self._yt_cache:
            return self._yt_cache[topic]

        candidates = self._fetch_youtube_candidates(topic)

        if not candidates:
            print(f"[SequenceOptimizer] No YouTube candidates found for '{topic}'")
            self._yt_cache[topic] = (None, None)
            return (None, None)

        # We use cosine similarity between the topic embedding and candidate titles
        topic_emb = self._model.encode([f"{topic} tutorial"])
        
        if len(candidates) == 1:
            title_emb = self._model.encode([candidates[0][1]])
            score = float(np.dot(topic_emb, title_emb.T)[0][0])
            self._yt_cache[topic] = (candidates[0][0], round(score, 4))
            return self._yt_cache[topic]

        # Score all candidates
        titles = [title for _, title in candidates]
        title_embs = self._model.encode(titles)
        
        # Compute cosine similarities
        scores = np.dot(title_embs, topic_emb.T).flatten()

        best_idx = int(np.argmax(scores))
        best_id = candidates[best_idx][0]
        best_score = round(float(scores[best_idx]), 4)

        print(
            f"[SequenceOptimizer] '{topic}' -> "
            f"Selected: '{candidates[best_idx][1]}' "
            f"(sim_score: {best_score:.3f} out of {len(candidates)} candidates)"
        )

        self._yt_cache[topic] = (best_id, best_score)
        return (best_id, best_score)

    def enrich_roadmap(
        self,
        subgraph,
        ordered_nodes: List[str],
        readiness_scores: List[float],
        priorities: List[str]
    ) -> List[Dict]:
        """
        Build the final enriched roadmap with GNN scores and ranked resources.

        Each node gets:
        - GNN-predicted readiness score and priority label
        - Cross-Encoder-ranked YouTube tutorial (or null if fetch failed)
        - Layout coordinates for the frontend graph visualization
        """
        roadmap = []
        for i, node in enumerate(ordered_nodes):
            topic = subgraph.nodes[node].get('topic', node)

            # Layout: vertical line for the React Flow visualization
            x = 350.0
            y = float(i * 400 + 50)

            # Cross-Encoder ranked YouTube resource — graceful degradation
            try:
                youtube_id, relevance_score = self.rank_and_select(topic)
            except Exception as e:
                print(f"[Enrichment] YouTube ranking failed for '{topic}': {e}")
                youtube_id, relevance_score = None, None

            roadmap.append({
                "order": i + 1,
                "topic": topic,
                "priority": priorities[i],
                "prerequisites_met": False,
                "confidence": round(readiness_scores[i], 4),
                "x": x,
                "y": y,
                "youtube_id": youtube_id,
                "relevance_score": relevance_score
            })

        return roadmap
