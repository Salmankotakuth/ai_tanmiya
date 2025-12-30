"""
LLM Text Generator (Placeholder)
--------------------------------

This module provides a clean interface function:
    generate_gpt_report(meeting_data, scores, predictions)

You can later replace the placeholder logic with:
- GPT-4 API
- Local LLM (Ollama)
- Azure OpenAI
- Together AI
etc.

For now it safely returns a formatted text summary.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("tanmiya.views.llm_text")


async def generate_gpt_report(
    meeting_data: Dict[str, Any],
    scores: Dict[str, Any],
    predictions: Dict[str, Any]
) -> str:
    """
    Generate a text report using an LLM.
    Currently returns a deterministic placeholder summary.
    """
    logger.info("LLM report generator called (placeholder implementation).")

    meeting_title = meeting_data.get("title", "Untitled Meeting")
    score_value = scores.get("total_score", "N/A")
    pred_summary = predictions.get("summary", "No predictions available.")

    # Simulated output
    report_text = f"""
    === Tanmiya Monthly Report ===

    Meeting: {meeting_title}

    Overall Score: {score_value}

    Executive Prediction Summary:
    {pred_summary}

    This is a placeholder LLM output.
    Replace with actual GPT/LLM API calls when ready.
    """.strip()

    return report_text
