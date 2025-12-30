# app/views/pdf_eng.py
"""
English PDF generator for Tanmiya reports.

Public function:
    generate_en_pdf(region: str, regions: list[str], latest_scores: list[float],
                    predicted_scores: list[float], introduction: str,
                    analysis: str, prediction: str, month: str, year: str) -> str

Returns:
    path to generated PDF file (string)

Notes:
- This function is CPU-bound and synchronous by design. In service layer we call it
  using asyncio.to_thread(...) to avoid blocking the event loop.
- Uses matplotlib for charts and reportlab for PDF pages.
- Keeps external dependencies minimal and configurable.
"""

import os
import io
from datetime import datetime
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    TableStyle,
)
from reportlab.lib import colors
import matplotlib.pyplot as plt

# Constants
OUTPUT_DIR = os.path.join("app", "static", "reports", "en")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _create_bar_chart(labels: List[str], values: List[float], title: str) -> bytes:
    """
    Create a bar chart and return image bytes.
    """
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel("Score")
    ax.set_ylim(0, max(max(values) * 1.1, 1))
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _create_stacked_bar(labels: List[str], latest: List[float], predicted: List[float], title: str) -> bytes:
    """
    Create a simple stacked-like comparison bar chart (latest vs predicted) and return image bytes.
    """
    import numpy as np

    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar([i - width/2 for i in x], latest, width=width, label="Latest")
    ax.bar([i + width/2 for i in x], predicted, width=width, label="Predicted")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_title(title)
    ax.set_ylabel("Score")
    ax.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _img_bytes_to_reportlab_image(img_bytes: bytes, max_width_mm=170) -> Image:
    """
    Convert image bytes to a ReportLab Image flowable and scale to page width.
    """
    buf = io.BytesIO(img_bytes)
    img = Image(buf)
    # scale to width
    max_w = max_width_mm * mm
    if img.drawWidth > max_w:
        scale = max_w / img.drawWidth
        img.drawWidth *= scale
        img.drawHeight *= scale
    return img


def _build_metadata_table(region: str, month: str, year: str) -> Table:
    """
    Build a small metadata table for the report header.
    """
    data = [
        ["Region:", region],
        ["Month:", f"{month}/{year}"],
        ["Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
    ]
    table = Table(data, colWidths=[60 * mm, 100 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def generate_en_pdf(
    region: str,
    regions_ordered: List[str],
    latest_scores: List[float],
    predicted_scores: List[float],
    introduction: str,
    analysis: str,
    prediction: str,
    month: str,
    year: str,
) -> str:
    """
    Generate the English PDF for a single region. Returns the file path.
    """
    safe_region = region.replace(" ", "_")
    filename = f"en_report_{safe_region}_{month}_{year}.pdf"
    out_path = os.path.join(OUTPUT_DIR, filename)

    # Create charts
    bar_bytes = _create_bar_chart(regions_ordered, latest_scores, "Latest Total Scores by Region")
    compare_bytes = _create_stacked_bar(regions_ordered, latest_scores, predicted_scores, "Latest vs Predicted Total Scores")

    # Build PDF
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = styles["Heading1"]
    heading.fontName = "Helvetica-Bold"

    story = []

    # Title
    story.append(Paragraph(f"Monthly Report — {region}", heading))
    story.append(Spacer(1, 6))

    # Metadata
    story.append(_build_metadata_table(region, month, year))
    story.append(Spacer(1, 12))

    # Introduction
    story.append(Paragraph("<b>Introduction</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(introduction or "No introduction available.", normal))
    story.append(Spacer(1, 12))

    # Analysis
    story.append(Paragraph("<b>Analysis</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    for para in (analysis or "No analysis available.").split("\n\n"):
        story.append(Paragraph(para.strip(), normal))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 12))

    # Charts
    story.append(Paragraph("<b>Charts</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(_img_bytes_to_reportlab_image(bar_bytes))
    story.append(Spacer(1, 8))
    story.append(_img_bytes_to_reportlab_image(compare_bytes))
    story.append(PageBreak())

    # Predictions section
    story.append(Paragraph("<b>Predictions</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    for para in (prediction or "No prediction available.").split("\n\n"):
        story.append(Paragraph(para.strip(), normal))
        story.append(Spacer(1, 6))

    # Small leaderboard table (region: score)
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Region Scores (short)</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))

    # Build a simple table of region → latest_score
    table_data = [["Region", "Latest Score", "Predicted Score"]]
    for r, l, p in zip(regions_ordered, latest_scores, predicted_scores):
        table_data.append([r, f"{l:.3f}", f"{p:.3f}"])

    tbl = Table(table_data, colWidths=[80 * mm, 45 * mm, 45 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.gray),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(tbl)

    # Build the PDF file
    doc.build(story)

    return out_path
