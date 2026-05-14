# 🧠 AI-Powered Autonomous Learning Architect

The **AI Learning Architect** is a 100% ML-driven application that takes a vague, unstructured career or learning goal (e.g., *"I want to learn deep learning and neural networks"*) and produces a **personalized, optimally-sequenced learning roadmap** with embedded, semantically-ranked YouTube tutorials.

Unlike typical educational roadmaps, **there are zero hardcoded paths, if-statements, or keyword fallbacks**. Every decision—from intent parsing to resource retrieval—is handled dynamically by a pipeline of custom Machine Learning models running locally.

---

## 🚀 Key Features

- **Semantic Intent Resolution:** Utilizes a custom-trained LSA/TF-IDF encoder + FAISS indexing to map vague natural language queries to curriculum nodes via inner-product vector similarity.
- **Topological Graph Pathfinding:** Leverages NetworkX and Dijkstra's algorithm to compute the "cognitive cost" between nodes, discovering the optimal learning path based on complexity and semantic embedding proximity.
- **Graph Neural Network (GNN) Sequencing:** A self-supervised 2-layer Graph Attention Network (GAT) built in pure PyTorch dynamically predicts node readiness and priority classification based on the user's customized subgraph.
- **Cross-Encoder Video Ranking:** Dynamically scrapes YouTube for candidates and uses a Cross-Encoder to semantically score and rank `(Topic, Video Title)` pairs, ensuring zero reliance on hardcoded fallback URLs.
- **LangGraph Orchestration:** A deterministic, 4-stage StateGraph architecture coordinates the data flow between all the independent ML models.

---

## 🛠️ Technology Stack

**Backend**
* **Python 3**
* **FastAPI + Uvicorn:** High-performance REST API
* **LangGraph:** Pipeline state management
* **PyTorch:** Hand-rolled Graph Attention Networks
* **NetworkX:** Directed Acyclic Graph (DAG) operations
* **Scikit-Learn:** Custom Vectorization and LSA 
* **FAISS:** Sub-millisecond similarity vector search
* **Sentence-Transformers:** Cross-Encoder for tutorial ranking

**Frontend**
* **React + Vite:** Lightning-fast frontend build tool
* **React Flow (`@xyflow/react`):** Interactive, draggable graph visualization canvas
* **Tailwind CSS & Vanilla CSS:** Modern dark-mode glassmorphism UI

---

## ⚙️ Getting Started

### Prerequisites
Make sure you have the following installed on your machine:
* [Python 3.10+](https://www.python.org/downloads/)
* [Node.js v18+](https://nodejs.org/)
* Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai_learning_architect.git
   cd ai_learning_architect
   ```

2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### 🚀 Running the App

A convenient auto-launcher is provided for Windows users. Simply double-click `launch.bat` or run it from the terminal:

```bash
.\launch.bat
```

This will automatically:
1. Boot up the FastAPI Python backend on `http://127.0.0.1:8000`
2. Launch the React Vite frontend on `http://localhost:5173`

> Note: On the very first startup, the application will download the required open-source HuggingFace models for the Cross-Encoder ranking. Subsequent boots will be practically instantaneous as it uses your local `.cache`.

---

## 📚 Documentation
If you're interested in the deep technical architecture or the graph theory applied behind the ML Engine, please refer to our internal documentation located in the `docs/aiml/` folder:
- [Graph Theory & Topology](docs/aiml/GRAPH_THEORY_TOPOLOGY.md)
- [GNN Sequencer Logic](docs/aiml/GNN_SEQUENCER.md)
- [NLP & Semantic Intent](docs/aiml/NLP_SEMANTIC_INTENT.md)
- [Dynamic Scraping Engine](docs/aiml/DYNAMIC_SCRAPING_ENGINE.md)

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
