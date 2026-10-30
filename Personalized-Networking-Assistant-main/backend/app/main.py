import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import (
    GenerationRequest, GenerationResponse,
    FactCheckRequest, FactCheckResponse,
    FeedbackRequest
)
from backend.app.event_analyzer import EventAnalyzer
from backend.app.topic_generator import TopicGenerator
from backend.app.fact_checker import FactChecker

app = FastAPI(title="Personalized Networking Assistant Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = EventAnalyzer()
generator = TopicGenerator()
checker = FactChecker()

# Using absolute path structure to resolve directory routing mismatches
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Points to backend/
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.json")


def _ensure_json_file(path: str):
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        with open(path, "w") as f:
            json.dump([], f)


@app.on_event("startup")
def startup_event():
    os.makedirs(DATA_DIR, exist_ok=True)
    _ensure_json_file(HISTORY_FILE)
    _ensure_json_file(FEEDBACK_FILE)


@app.post("/api/v1/generate", response_model=GenerationResponse, status_code=status.HTTP_200_OK)
async def generate_conversation(payload: GenerationRequest):
    try:
        # Step 1: Extract themes
        extracted_themes = analyzer.extract_themes(payload.event_description)

        # Step 2: Generate starters
        conversation_starters = generator.generate_starters(
            bio=payload.bio,
            themes=extracted_themes,
            event_desc=payload.event_description
        )

        # Create a unique session identifier string for tracking feedback
        generated_session_id = f"sess_{int(datetime.utcnow().timestamp())}"

        # Step 3: Format payload for internal persistence
        history_record = {
            "session_id": generated_session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "bio": payload.bio,
            "event": payload.event_description,
            "themes": extracted_themes,
            "starters": conversation_starters
        }

        # Step 4: Write logs safely
        with open(HISTORY_FILE, "r+") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append(history_record)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        return {
            "session_id": generated_session_id,
            "event": payload.event_description,
            "themes": extracted_themes,
            "starters": conversation_starters
        }

    except Exception as e:
        print(f"CRITICAL PIPELINE ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference Engine error: {str(e)}"
        )


@app.post("/api/v1/verify", response_model=FactCheckResponse, status_code=status.HTTP_200_OK)
async def verify_fact(payload: FactCheckRequest):
    try:
        result = checker.verify_topic(payload.query)
        return result
    except Exception as e:
        print(f"FACT CHECK ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fact checking error: {str(e)}"
        )


@app.post("/api/v1/feedback", status_code=status.HTTP_200_OK)
async def submit_feedback(payload: FeedbackRequest):
    try:
        feedback_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": payload.session_id,
            "starter": payload.starter,
            "feedback": payload.feedback
        }

        with open(FEEDBACK_FILE, "r+") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append(feedback_record)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        return {"status": "ok"}

    except Exception as e:
        print(f"FEEDBACK WRITE ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save feedback: {str(e)}"
        )


@app.get("/api/v1/history", status_code=status.HTTP_200_OK)
async def get_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            try:
                history_data = json.load(f)
            except json.JSONDecodeError:
                history_data = []

        with open(FEEDBACK_FILE, "r") as f:
            try:
                feedback_data = json.load(f)
            except json.JSONDecodeError:
                feedback_data = []

        # Build a lookup of (session_id, starter_text) -> feedback value.
        # If a starter was rated more than once, the most recent entry wins
        # since feedback_data is appended to in chronological order.
        feedback_map = {}
        for fb in feedback_data:
            key = (fb.get("session_id"), fb.get("starter"))
            feedback_map[key] = fb.get("feedback")

        # Annotate each starter in each history record with its feedback status
        for record in history_data:
            session_id = record.get("session_id")
            starters = record.get("starters", [])
            record["starters_with_feedback"] = [
                {
                    "text": s,
                    "feedback": feedback_map.get((session_id, s))  # None if never rated
                }
                for s in starters
            ]

        return history_data
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"HISTORY READ ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read history: {str(e)}"
        )