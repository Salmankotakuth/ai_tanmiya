# app/api/meeting_controller.py

from fastapi import APIRouter, HTTPException
from app.models.schemas import MonthYear
from app.services.meeting_service import (
    collect_data_from_tanmiya_backend
)

router = APIRouter()

@router.post("/collect")
async def collect_meeting_data(payload: MonthYear):
    """
    Trigger data collection from Tanmiya backend.
    """
    try:
        result = await collect_data_from_tanmiya_backend(payload)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))