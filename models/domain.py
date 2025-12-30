# app/models/domain.py

from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class RegionScore:
    region_id: int
    region_name: str
    month: str
    meeting_score: float
    participants_score: float
    total_score: float
    total_topics: int
    transferred_topics: int


@dataclass
class RegionPrediction:
    region_id: int
    region_name: str
    meeting_score: float
    participants_score: float
    total_topics: int
    transferred_topics: int
    total_score: float


@dataclass
class ReportText:
    introduction: str
    analysis: str
    prediction: str
