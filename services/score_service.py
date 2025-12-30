# app/services/score_service.py
"""
Score Service
- Computes participant score, meeting NLP scores and topic-based scores
- Aggregates results for all regions and posts leaderboard data
"""

from typing import List, Dict, Any
from app.models.schemas import MonthYear
from app.services import directus_service
from app.utils.cleaner import clean_html
from app.models.domain import RegionScore
from app.models.schemas import TanmiyaResponse
import logging
from app.utils.translator import translator  # to be implemented (wrapper for local translator)
from sentence_transformers import CrossEncoder  # heavy; ensure installed where used
import asyncio
from app.constants.regions import REGIONS
from app.utils import http_client

logger = logging.getLogger("tanmiya.services.score")

# weights
PARTICIPANT_WEIGHT = 0.4
MEETING_WEIGHT = 0.4
TOPIC_WEIGHT = 0.2

# preload ranking model (CrossEncoder) lazily
_ranking_model = None


def _get_ranking_model():
    global _ranking_model
    if _ranking_model is None:
        _ranking_model = CrossEncoder("mixedbread-ai/mxbai-rerank-xsmall-v1")
    return _ranking_model


def calculate_participants_score(participants: Dict[str, Any]) -> float:
    """
    Compute weighted participant score using the same logic as earlier.
    Accepts dict compatible with Participants.
    """
    # Safe access with defaults
    def safe_get(d, k):
        return int(d.get(k, 0)) if d else 0

    ttl_administrator = safe_get(participants, "ttl_administrator")
    ptd_administrator = safe_get(participants, "ptd_administrator")
    ttl_sub = safe_get(participants, "ttl_sub_administrator")
    ptd_sub = safe_get(participants, "ptd_sub_administrator")
    ttl_coord = safe_get(participants, "ttl_coordinator")
    ptd_coord = safe_get(participants, "ptd_coordinator")
    ttl_member = safe_get(participants, "ttl_member")
    ptd_member = safe_get(participants, "ptd_member")
    ttl_gust = safe_get(participants, "ttl_gust")
    ptd_gust = safe_get(participants, "ptd_gust")

    def ratio(ptd, ttl):
        return (ptd / ttl) if ttl > 0 else 0.0

    score = (
        ratio(ptd_administrator, ttl_administrator) * 0.3 +
        ratio(ptd_sub, ttl_sub) * 0.2 +
        ratio(ptd_coord, ttl_coord) * 0.2 +
        ratio(ptd_member, ttl_member) * 0.2 +
        ratio(ptd_gust, ttl_gust) * 0.1
    )
    return score


async def generate_minutes_score(topic: str, discussions: List[str]) -> float:
    """
    Translate Arabic topic/discussions to English (if needed), then score similarity
    using CrossEncoder ranker to produce a meeting score in [0, ?].
    """
    # Ensure valid input before translation
    topic = topic.strip() if isinstance(topic, str) else ""
    discussions = discussions.strip() if isinstance(discussions, str) else ""

    if not topic or not discussions:
        return 0.0

    # translate topic and joined discussions
    # translator.translate should be async and return plain str
    try:
        translated_topic = await translator.translate(topic, target_lang="en") if topic else ""
        # For discussion list, join or pass many — the CrossEncoder.rank call will accept two lists
        joined_discussion = " ".join(discussions) if discussions else ""
        translated_discussion = await translator.translate(joined_discussion, target_lang="en") if joined_discussion else ""

        model = CrossEncoder("mixedbread-ai/mxbai-rerank-xsmall-v1")

        # model.rank expects (query, documents, ...) — we use small top_k
        results = model.rank(translated_topic, translated_discussion, return_documents=True, top_k=4)

        if not results:
            return 0.0

        # average score
        avg = sum([r["score"] for r in results]) / len(results)
        return avg

    except Exception as e:
        logger.exception("generate_minutes_score failed: %s", e)
        return 0.0


async def fetch_region_data(region: str, month: int, year: int):
    """
    Orchestrates fetching data for all regions (via http_client.get),
    """

    region_id = REGIONS.index(region) + 1
    resp = await http_client.get(
        f"/GetMeetingDetailList?Month={month}&Year={year}&RegionId={region_id}"
    )

    if not resp or not resp.get("ResponseBody"):
        return []

    # Same cleanup logic as collect_data_from_tanmiya_backend
    data = resp["ResponseBody"]
    for item in data:
        meetings = item.get("meeting", [])
        for m in meetings:
            disc = m.get("discussion")
            if isinstance(disc, str):
                m["discussion"] = [clean_html(disc)]
            elif isinstance(disc, list):
                m["discussion"] = [clean_html(x) for x in disc]

    return data


async def calculate_scores(payload: MonthYear) -> List[Dict[str, Any]]:
    """
    computes the participant, meeting, topic and overall score, returns list of region results.
    Also posts results to leaderboard collections using directus_service.
    """
    results = []

    # fetch all regions' raw items
    regions = REGIONS  # from constants, collect the region list
    for region in regions:
        try:
            items = await fetch_region_data(region, payload.month, payload.year)

            if not items:
                continue

            # items is a list of TanmiyaData-like dicts
            total_topics = sum([it.get("number_of_topic", 0) for it in items])
            transferred_topics = sum([it.get("transferred_topic", 0) for it in items])

            # compute participant & meeting scores averaged over all items
            participant_scores = []
            meeting_scores = []
            for it in items:
                participants_obj = it.get("participants", {})
                participant_scores.append(calculate_participants_score(participants_obj))

                # meeting: list of meeting objects
                meeting_items = it.get("meeting", [])
                # For each meeting item compute minutes score and average them
                meeting_item_scores = []
                for m in meeting_items:
                    topic = m.get("topic", "")
                    discussions = m.get("discussion", [])
                    # ensure discussions is list[str]
                    if isinstance(discussions, str):
                        discussions = [discussions]
                    score = await generate_minutes_score(topic, discussions)
                    meeting_item_scores.append(score)
                meeting_scores.append(sum(meeting_item_scores) / len(meeting_item_scores) if meeting_item_scores else 0.0)

            avg_participant_score = sum(participant_scores) / len(participant_scores) if participant_scores else 0.0
            avg_meeting_score = sum(meeting_scores) / len(meeting_scores) if meeting_scores else 0.0
            topic_score = (total_topics - transferred_topics) / total_topics if total_topics else 0.0

            overall = avg_participant_score * PARTICIPANT_WEIGHT + avg_meeting_score * MEETING_WEIGHT + topic_score * TOPIC_WEIGHT

            reg_result = {
                "Region": region,
                "Region_id": await directus_service.get_region_id(region),
                "month": f"{payload.month}/{payload.year}",
                "meeting_score": float(f"{avg_meeting_score:.4f}"),
                "participants_score": float(f"{avg_participant_score:.4f}"),
                "total_score": float(f"{overall:.4f}"),
                "total_topics": total_topics,
                "transferred_topics": transferred_topics,
                "Rank": None
            }

            results.append(reg_result)
        except Exception as e:
            logger.exception("Error computing scores for region %s: %s", region, e)

    # ranking by total_score
    results.sort(key=lambda x: x["total_score"], reverse=True)
    for idx, r in enumerate(results, start=1):
        r["Rank"] = idx

    # Post results to leaderboards using directus_service (collection names: Leaderboard_all, Leaderboard)
    try:
        await directus_service.upsert_leaderboard(results)      # post calculated scores to leader bord
    except Exception as e:
        logger.exception("Failed to upsert leaderboard: %s", e)

    return results
