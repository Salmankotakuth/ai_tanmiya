# app/views/graph_builder.py
"""
Shared chart-building utilities for PDF generators.
Used by pdf_eng.py and pdf_ar.py.
"""

import io
import matplotlib.pyplot as plt
from typing import List


def build_bar(labels: List[str], values: List[float], title: str) -> bytes:
    """
    Create a bar chart and return PNG bytes.
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


def build_compare_chart(labels: List[str], latest: List[float], predicted: List[float], title: str) -> bytes:
    """
    Build a comparison chart (latest vs predicted).
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
    ax.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


async def generate_graphs(actual_data: List[dict], predicted_data: List[dict]) -> dict:

    # ordering region name and score for actual data
    region_score_actual = []
    for item in actual_data:
        region_score_actual.append([item['Region'], item['total_score']])

    # ordering region name and score for predicted data
    region_score_predicted = {}
    for item in predicted_data:
        region_score_predicted[f"{item['Region']}"] = item['total_score']

    regions_ordered = [region_score_actual[i][0] for i in range(0, 11)]
    scores_actual = [region_score_actual[i][1] for i in range(0, 11)]
    scores_predicted = []

    for region in regions_ordered:
        scores_predicted.append(region_score_predicted[f"{region}"])

    bar = {
        "x": regions_ordered,
        "y": scores_actual
    }

    stacked_bar = {
        "x": regions_ordered,
        "y": [
            {"data": scores_actual, "label": "actual"},
            {"data": scores_predicted, "label": "predicted"}
        ]
    }

    return {"bar": bar, "stackedBar": stacked_bar}