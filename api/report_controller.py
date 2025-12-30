# app/api/report_controller.py

from fastapi import APIRouter, HTTPException
from app.services.report_service import (
    generate_region_reports
)

router = APIRouter()

@router.post("/generate")
async def generate_reports():
    """
    Generate textual analysis reports for each region.
    """
    try:
        result = await generate_region_reports()
        return {"status": "success", "reports": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))