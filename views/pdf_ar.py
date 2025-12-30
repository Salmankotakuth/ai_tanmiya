# app/views/pdf_ar.py
"""
Arabic PDF generator for Tanmiya reports.

- Uses arabic_reshaper + python-bidi to prepare Arabic strings for ReportLab.
- Embeds an Arabic TTF font (you must place the font file under app/static/fonts/).
- Synchronous; call via asyncio.to_thread(generate_ar_pdf, ...) from async code.
"""

import os
import io
from datetime import datetime, date
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt

# Arabic shaping / bidi
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None

# Configure output directory and Arabic font path
OUTPUT_DIR = os.path.join("app", "static", "reports", "ar")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Default Arabic font file: put your Arabic TTF under app/static/fonts/
ARABIC_FONT_NAME = "NotoSansArabic"  # logical name used in ReportLab
ARABIC_FONT_PATH = os.path.join("app", "static", "fonts", "NotoSansArabic-Regular.ttf")

# Register Arabic font if available
def _register_arabic_font():
    if os.path.exists(ARABIC_FONT_PATH):
        try:
            pdfmetrics.registerFont(TTFont(ARABIC_FONT_NAME, ARABIC_FONT_PATH))
        except Exception:
            pass


_register_arabic_font()


def _reshape_arabic(text: str) -> str:
    """
    Prepare Arabic string for display in ReportLab:
    1. reshape using arabic_reshaper
    2. apply bidi reordering
    """
    if not text:
        return ""
    if arabic_reshaper and get_display:
        try:
            reshaped = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped)
            return bidi_text
        except Exception:
            # fallback: return original
            return text
    return text


def _create_bar_chart(labels: List[str], values: List[float], title_ar: str) -> bytes:
    """
    Simple bar chart. Labels are Arabic; reshape them for matplotlib tick labels if possible.
    Returns image bytes.
    """
    fig, ax = plt.subplots(figsize=(8, 3))
    # reshape labels for proper visual order (matplotlib will not handle shaping; this is best-effort)
    display_labels = []
    for lab in labels:
        if arabic_reshaper and get_display:
            try:
                display_labels.append(get_display(arabic_reshaper.reshape(lab)))
            except Exception:
                display_labels.append(lab)
        else:
            display_labels.append(lab)

    ax.bar(display_labels, values)
    # reshape title
    title = _reshape_arabic(title_ar)
    ax.set_title(title)
    ax.set_ylabel("")  # keep y label empty for Arabic layout
    ax.set_ylim(0, max(max(values) * 1.1, 1))
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _create_compare_chart(labels: List[str], latest: List[float], predicted: List[float], title_ar: str) -> bytes:
    import numpy as np

    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar([i - width/2 for i in x], latest, width=width, label=_reshape_arabic("الحالي"))
    ax.bar([i + width/2 for i in x], predicted, width=width, label=_reshape_arabic("المتوقع"))
    display_labels = []
    for lab in labels:
        if arabic_reshaper and get_display:
            try:
                display_labels.append(get_display(arabic_reshaper.reshape(lab)))
            except Exception:
                display_labels.append(lab)
        else:
            display_labels.append(lab)
    ax.set_xticks(list(x))
    ax.set_xticklabels(display_labels, rotation=30, ha="right")
    ax.set_title(_reshape_arabic(title_ar))
    ax.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _img_bytes_to_reportlab_image(img_bytes: bytes, max_width_mm=170) -> Image:
    buf = io.BytesIO(img_bytes)
    img = Image(buf)
    max_w = max_width_mm * mm
    if img.drawWidth > max_w:
        scale = max_w / img.drawWidth
        img.drawWidth *= scale
        img.drawHeight *= scale
    return img


def _build_metadata_table_ar(region_ar: str, month_ar: str, year_ar: str) -> Table:
    """
    Build metadata table with right-to-left orientation;
    we insert pre-shaped Arabic strings so they visually align right-to-left.
    """
    data = [
        [_reshape_arabic("المنطقة:"), _reshape_arabic(region_ar)],
        [_reshape_arabic("الشهر:"), _reshape_arabic(month_ar)],
        [_reshape_arabic("تم الإنشاء:"), _reshape_arabic(datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))],
    ]
    table = Table(data, colWidths=[60 * mm, 100 * mm], hAlign="RIGHT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -1), ARABIC_FONT_NAME if os.path.exists(ARABIC_FONT_PATH) else "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def generate_ar_pdf(
    region_ar: str,
    regions_ordered_ar: List[str],
    latest_scores: List[float],
    predicted_scores: List[float],
    introduction_ar: str,
    analysis_ar: str,
    prediction_ar: str,
    month: str,
    year: str,
) -> str:
    """
    Main function to generate Arabic PDF. Returns path to the created PDF file.
    region_ar and regions_ordered_ar are Arabic strings (not reshaped yet).
    """
    safe_region = region_ar.replace(" ", "_")
    filename = f"ar_report_{safe_region}_{month}_{year}.pdf"
    out_path = os.path.join(OUTPUT_DIR, filename)

    # Create charts (titles in Arabic)
    bar_bytes = _create_bar_chart(regions_ordered_ar, latest_scores, "أحدث درجات المناطق")
    compare_bytes = _create_compare_chart(regions_ordered_ar, latest_scores, predicted_scores, "الحالي مقابل المتوقع")

    # Prepare document
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    # create Arabic paragraph style (right aligned)
    arabic_style = ParagraphStyle(
        name="Arabic",
        parent=styles["Normal"],
        fontName=ARABIC_FONT_NAME if os.path.exists(ARABIC_FONT_PATH) else "Helvetica",
        fontSize=11,
        leading=14,
        alignment=2,  # right align
    )
    heading_style = ParagraphStyle(
        name="ArabicHeading",
        parent=styles["Heading1"],
        fontName=ARABIC_FONT_NAME if os.path.exists(ARABIC_FONT_PATH) else "Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=2,
    )

    story = []

    # Title (reshaped)
    story.append(Paragraph(_reshape_arabic(f"تقرير شهري — {region_ar}"), heading_style))
    story.append(Spacer(1, 6))

    # Metadata table
    story.append(_build_metadata_table_ar(region_ar, month, year))
    story.append(Spacer(1, 12))

    # Introduction
    story.append(Paragraph(_reshape_arabic("مقدمة"), heading_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(_reshape_arabic(introduction_ar or "لا توجد مقدمة متاحة."), arabic_style))
    story.append(Spacer(1, 12))

    # Analysis
    story.append(Paragraph(_reshape_arabic("التحليل"), heading_style))
    story.append(Spacer(1, 6))
    for para in (analysis_ar or "لا يوجد تحليل متاح.").split("\n\n"):
        story.append(Paragraph(_reshape_arabic(para.strip()), arabic_style))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 12))

    # Charts
    story.append(Paragraph(_reshape_arabic("مخططات"), heading_style))
    story.append(Spacer(1, 6))
    story.append(_img_bytes_to_reportlab_image(bar_bytes))
    story.append(Spacer(1, 8))
    story.append(_img_bytes_to_reportlab_image(compare_bytes))
    story.append(PageBreak())

    # Predictions
    story.append(Paragraph(_reshape_arabic("التوقعات"), heading_style))
    story.append(Spacer(1, 6))
    for para in (prediction_ar or "لا توجد توقعات متاحة.").split("\n\n"):
        story.append(Paragraph(_reshape_arabic(para.strip()), arabic_style))
        story.append(Spacer(1, 6))

    # Small region table: Region | Latest | Predicted (reshaped headers)
    story.append(Spacer(1, 12))
    story.append(Paragraph(_reshape_arabic("درجات المناطق (موجز)"), heading_style))
    story.append(Spacer(1, 6))

    table_data = [[_reshape_arabic("المنطقة"), _reshape_arabic("الدرجة الحالية"), _reshape_arabic("الدرجة المتوقعة")]]
    for r, l, p in zip(regions_ordered_ar, latest_scores, predicted_scores):
        table_data.append([_reshape_arabic(r), f"{l:.3f}", f"{p:.3f}"])

    tbl = Table(table_data, colWidths=[80 * mm, 45 * mm, 45 * mm], hAlign="RIGHT")
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.gray),
                ("FONTNAME", (0, 0), (-1, 0), ARABIC_FONT_NAME if os.path.exists(ARABIC_FONT_PATH) else "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(tbl)

    doc.build(story)
    return out_path
