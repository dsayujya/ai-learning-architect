from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import RoadmapRequest, RoadmapResponse
from app.engine.orchestrator import PathInferenceEngine
import os

app = FastAPI(
    title="AI-Powered Autonomous Learning Architect",
    version="2.0.0",
    description="100% ML-driven learning path generator. No mocks, no hardcoded paths."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup PathInferenceEngine (singleton for the app)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
graph_path = os.path.join(base_dir, "data", "sample_curriculum.json")

engine = PathInferenceEngine(cur_graph_path=graph_path)


@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")


@app.post("/generate_roadmap", response_model=RoadmapResponse)
def generate_roadmap(request: RoadmapRequest):
    result_state = engine.generate_roadmap(request.goal, request.current_skills)

    return RoadmapResponse(
        goal=result_state["goal"],
        extracted_skills=result_state["extracted_skills"],
        roadmap=result_state["roadmap"]
    )
