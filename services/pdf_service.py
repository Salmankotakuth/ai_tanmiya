# app/services/pdf_service.py
"""
PDF Service
- Uses view-layer functions to generate English and Arabic PDFs, upload files, and email them.
- The actual PDF creation lives in app.views.pdf_eng and app.views.pdf_ar
"""

from typing import Dict, Any
from app.models.schemas import MonthYear
from app.services import directus_service
from app.views.pdf_eng import generate_en_pdf  # to be implemented
from app.views.pdf_ar import generate_ar_pdf    # to be implemented
from app.views.emailer import send_email        # to be implemented
import logging
import os

logger = logging.getLogger("tanmiya.services.pdf")


async def generate_all_pdfs(payload: MonthYear) -> Dict[str, Any]:
    """
    For each region:
      - Collect required data (latest & predicted),
      - Generate English + Arabic PDFs,
      - Upload to Directus files endpoint,
      - Send emails with attachments if required.

    Returns a mapping: { region_id: { "en_pdf": path_or_url, "ar_pdf": path_or_url } }
    """
    month = payload.month
    year = payload.year

    results = {}

    # Get reports from directus (assuming report collection exists and has all data)
    reports = await directus_service.get_reports(month=month, year=year)
    # reports is a list of Report dicts per region
    for report in reports:
        region = report.get("Region")
        try:
            # Extract components needed for PDF
            regions_ordered = [r.get("Region") for r in reports]  # simplify for graphs
            latest_scores = [float(r.get("total_score", 0)) for r in reports]
            predicted_scores = [float(r.get("total_score", 0)) for r in reports]  # replace with real predicted

            introduction = report.get("report", "")
            analysis = report.get("report", "")
            prediction = report.get("report", "")

            # Generate English PDF (synchronous heavy op) - it's okay to call from async, but you might
            # run it in threadpool in production (via asyncio.to_thread). For now, use to_thread.
            en_pdf_path = await asyncio.to_thread(generate_en_pdf, region, regions_ordered, latest_scores, predicted_scores, introduction, analysis, prediction, month, year)
            ar_pdf_path = await asyncio.to_thread(generate_ar_pdf, region, regions_ordered, latest_scores, predicted_scores, introduction, analysis, prediction, datetime.date.today())

            # Upload to directus files
            en_file_id = await directus_service.upload_file(en_pdf_path, folder_id=settings.ENGLISH_REPORTS_FOLDER)
            ar_file_id = await directus_service.upload_file(ar_pdf_path, folder_id=settings.ARABIC_REPORTS_FOLDER)

            # Optionally send email (if region has mail addresses)
            mail_to = report.get("mail")
            if mail_to:
                await asyncio.to_thread(send_email, settings.EMAIL_FROM, mail_to, f"Report for {region}", "Please find attached.", [en_pdf_path, ar_pdf_path], settings.EMAIL_PASSWORD)

            results[region] = {"en_pdf": en_file_id, "ar_pdf": ar_file_id}
        except Exception as e:
            logger.exception("Failed to render/upload PDF for %s: %s", region, e)
            results[region] = {"error": str(e)}
    return results
