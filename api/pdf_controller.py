# app/api/pdf_controller.py

from fastapi import APIRouter, HTTPException
from app.models.schemas import MonthYear
from app.services.pdf_service import (
    generate_all_pdfs
)

router = APIRouter()

@router.post("/generate")
async def generate_pdfs(payload: MonthYear):
    """
    Generate English + Arabic PDF reports, upload to Directus, and email them.
    """
    try:
        result = await generate_all_pdfs(payload)
        return {"status": "success", "pdfs": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))