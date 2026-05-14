from pydantic import BaseModel
from typing import List, Optional

class RoadmapRequest(BaseModel):
    goal: str
    current_skills: List[str]

class RoadmapStep(BaseModel):
    order: int
    topic: str
    priority: str
    prerequisites_met: bool
    confidence: float = 0.0
    x: float
    y: float
    youtube_id: Optional[str] = None
    relevance_score: Optional[float] = None

class RoadmapResponse(BaseModel):
    goal: str
    extracted_skills: List[str]
    roadmap: List[RoadmapStep]
