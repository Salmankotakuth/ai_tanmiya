# app/api/score_controller.py

from fastapi import APIRouter, HTTPException
from app.models.schemas import MonthYear
from app.services.score_service import (
    calculate_scores
)

router = APIRouter()

@router.post("/calculate")
async def calculate_score(payload: MonthYear):
    """
    Calculate participant, meeting NLP, topic, and overall scores.
    """
    try:
        result = await calculate_scores(payload)
        return {"status": "success", "scores": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))