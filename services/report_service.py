# app/services/report_service.py
"""
Report Service
- Generates textual region reports using LLM or templating (views.llm_text)
- Aggregates data for all regions and returns report objects
"""

from typing import List, Dict, Any
from app.services import directus_service
from app.views.llm_text import generate_gpt_report  # to be implemented in views
import logging

logger = logging.getLogger("tanmiya.services.report")


async def generate_region_reports() -> List[Dict[str, Any]]:
    """
    Fetch latest leaderboard and predicted data, generate textual reports per region,
    and persist reports to Directus.
    """
    # fetch latest data and predicted data
    latest = await directus_service.get_leaderboard_latest()
    predicted = await directus_service.get_leaderboard_predictions()

    reports = []

    # for each region, generate a GPT-based report
    for region_item in latest:
        try:
            region_name = region_item.get("Region")
            # prepare system + user prompts as lists (views.llm_text expects lists)
            system_prompt = [
                "You are an AI assistant that provides organized explanations for tabular data in Arabic only.",
                "Write concise, structured analysis in Arabic."
            ]
            user_prompt = [
                f"Region: {region_name}",
                f"Actual scores: {region_item}",
                f"Predicted scores: {next((p for p in predicted if p.get('Region') == region_name), {})}"
            ]
            report_text = await generate_gpt_report(system_prompt, user_prompt)  # returns string
            report_obj = {
                "Region": region_name,
                "report": report_text,
                "report_ar": report_text,  # for now same; views may produce different content
                "month": region_item.get("month"),
                "graph": {}  # graph generation occurs in pdf_service
            }
            reports.append(report_obj)
        except Exception as e:
            logger.exception("Failed to generate report for region %s: %s", region_item.get("Region"), e)

    # Save reports into Directus (collection "report")
    try:
        await directus_service.post_reports(reports)
    except Exception as e:
        logger.exception("Failed to post reports to Directus: %s", e)

    return reports
