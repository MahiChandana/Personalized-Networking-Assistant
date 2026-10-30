from pydantic import BaseModel
from typing import List, Optional

class GenerationRequest(BaseModel):
    bio: str
    event_description: str

class GenerationResponse(BaseModel):
    session_id: str
    event: str
    themes: List[str]
    starters: List[str]

class FactCheckRequest(BaseModel):
    query: str

class FactCheckResponse(BaseModel):
    status: str
    title: str = ""
    summary: str
    url: str = ""

class FeedbackRequest(BaseModel):
    session_id: Optional[str] = None
    starter: str
    feedback: str