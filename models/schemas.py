# app/models/schemas.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ------------------------------
# Request Payloads
# ------------------------------

class MonthYear(BaseModel):
    month: str
    year: str
    lastDay_of_month: Optional[str] = None


# ------------------------------
# Participants & Meeting Models
# ------------------------------

class Participants(BaseModel):
    ttl_administrator: int
    ptd_administrator: int
    ttl_sub_administrator: int
    ptd_sub_administrator: int
    ttl_coordinator: int
    ptd_coordinator: int
    ttl_member: int
    ptd_member: int
    ttl_gust: int
    ptd_gust: int


class MeetingItem(BaseModel):
    topic: str
    discussion: List[str]


class DataItem(BaseModel):
    id: int
    user_created: Optional[str] = None
    date_created: str
    date: datetime
    participants: Participants
    meeting: List[MeetingItem]
    number_of_topic: int
    transferred_topic: int


class TanmiyaData(BaseModel):
    MeetingId: int
    date: datetime
    participants: Participants
    meeting: List[MeetingItem]
    number_of_topic: int
    transferred_topic: int


class APIResponse(BaseModel):
    data: List[DataItem]


class TanmiyaResponse(BaseModel):
    ResponseBody: List[TanmiyaData]


# ------------------------------
# Leaderboard Items
# ------------------------------

class Item(BaseModel):
    date_created: datetime
    date_updated: Optional[datetime]
    id: int
    meeting_score: float
    month: str
    participants_score: float
    Rank: int
    Region: str
    Region_id: int
    total_score: float
    total_topics: int
    transferred_topics: int


class LeadBoard(BaseModel):
    data: List[Item]


# ------------------------------
# PDF & Graph Models
# ------------------------------

class Bar(BaseModel):
    x: List[str]
    y: List[float]


class StackedBarDataset(BaseModel):
    label: str
    data: List[float]


class StackedBar(BaseModel):
    x: List[str]
    y: List[StackedBarDataset]


class Graph(BaseModel):
    bar: Bar
    stackedBar: StackedBar


class Report(BaseModel):
    id: int
    date_created: str
    month: str
    Region_id: int
    report: str
    report_ar: str
    graph: Graph
    Region: str
    mail: str
