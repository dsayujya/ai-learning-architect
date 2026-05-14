# NLP & Semantic Intent Parsing (v2.0)

The first stage of the PathInferenceEngine resolves *what the user actually wants* from vague, unstructured text. We solve this using **Dense Vector Embeddings** + **FAISS nearest-neighbor search** — not a single keyword match or regex in sight.

---

## 1. The Model: `all-MiniLM-L6-v2`

The system uses a high-performance **Sentence-Transformer** model loaded once and shared across components.

*   **Architecture:** BERT-based mini-transformer (6 layers, 384 hidden dims).
*   **Output Dimensions:** 384 dimensions per sentence.
*   **Mechanism:** Maps entire sentences into a vector space where semantically similar sentences are geometrically close.

### Semantic vs. Keyword Matching
| Input | Old Keyword Result | New Embedding Result |
| :--- | :--- | :--- |
| "I want to hack stuff" | No match → `"Python Basics"` | **Ethical Hacking & Pen Testing** (sim: 0.42) |
| "build a phone app" | No match → `"Python Basics"` | **Mobile App UI Design** (sim: 0.45) |
| "teach me deep learning" | Partial match | **Deep Learning Fundamentals** (sim: 0.60) |

---

## 2. FAISS-Powered Resolution

### The Index
At startup, all 39 curriculum topic names are encoded into 384-dim vectors and added to a **FAISS `IndexFlatIP`** (inner-product) index. Because embeddings are L2-normalized, inner product = cosine similarity.

### The Search
When a user submits a goal:

```mermaid
graph LR
    Goal["'I want to learn neural networks'"] --> Encode["Encode with<br/>all-MiniLM-L6-v2"]
    Encode --> Search["FAISS IndexFlatIP<br/>top-3 search"]
    Search --> Results["(deep_learning, 0.604)<br/>(cnn, 0.486)"]
```

### Dynamic Thresholding
We don't just take the top match. We use an **anchor-based threshold**:
1. Find the highest scoring topic (the anchor).
2. Include any topic scoring within **80%** of the anchor, minimum **0.20**.
3. This allows "fullstack" to match *both* Frontend and Backend simultaneously.

### Mathematical Basis
$$similarity = \frac{A \cdot B}{\|A\| \|B\|} = A \cdot B \quad \text{(when L2-normalized)}$$

Because we normalize all embeddings, cosine similarity reduces to a simple dot product — exactly what `IndexFlatIP` computes natively.

---

## 3. What Was Eliminated

| Before (v1.0) | After (v2.0) |
|:---|:---|
| `curriculum_mapping.jsonl` keyword file | **Deleted** — not referenced |
| `_keyword_extract()` with word overlap counting | **Deleted** |
| Hardcoded fallback: `return ["Python Basics"]` | **Deleted** — worst case returns lowest-scoring FAISS match |
| Separate `VectorEngine` class | **Absorbed** into `IntentParser` |

---

## 4. Implementation Details

*   **File:** [intent_parser.py](../../app/engine/intent_parser.py)
*   **Class:** `IntentParser`
*   **Key Method:** `resolve_intent(goal, top_k=3)` → returns `List[Tuple[node_id, topic_name, confidence]]`
*   **Model sharing:** The `SentenceTransformer` instance is loaded once in `PathInferenceEngine.__init__()` and passed by reference to `IntentParser` and `KnowledgeGraph`.
