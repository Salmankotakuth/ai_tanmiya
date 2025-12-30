# app/api/prediction_controller.py

from fastapi import APIRouter, HTTPException
from app.services.prediction_service import (
    predict_future_scores
)

router = APIRouter()

@router.post("/future")
async def predict_future():
    """
    Generate future scores using LSTM.
    """
    try:
        result = await predict_future_scores()
        return {"status": "success", "predictions": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))