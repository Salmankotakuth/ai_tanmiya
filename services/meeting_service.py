# app/services/meeting_service.py

"""
Meeting Service
- Responsible for collecting meeting data from Tanmiya backend (or other sources)
- Transforming / normalizing the payload
- Posting into Directus (tanmiya.aioman.org) via directus_service
"""

from typing import Any
from app.models.schemas import MonthYear, TanmiyaResponse, APIResponse
from app.services import directus_service
from app.utils import http_client
from app.utils.cleaner import clean_html  # to be implemented
from app.models.schemas import TanmiyaData, DataItem
import datetime
import logging

logger = logging.getLogger("tanmiya.services.meeting")


async def collect_data_from_tanmiya_backend(payload: MonthYear) -> dict:
    """
    Collect meeting details from the official backend for all regions (region ids 1..11)
    and post the cleaned data to Directus (tanmiya.aioman.org).

    Returns:
        dict: summary of what was posted (counts, successes, failures)
    """
    month = payload.month
    year = payload.year

    summary = {"posted": 0, "skipped": 0, "errors": []}

    # Example region list (should be centralised in constants)
    regions = [
        "Muscat", "Al_Batinah_North", "Musandam", "Al_Buraimi",
        "ADhahirah", "ADakhiliya", "ASharqiyah_North", "Al_Wusta",
        "Dhofar", "Al_Batinah_South", "ASharqiyah_South"
    ]

    # Tanmiya backend endpoint pattern (base url handled by http_client)
    for region in regions:
        url = f"/GetMeetingDetailList?Month={month}&Year={year}&RegionId={{region_id}}"  # placeholder path
        # In practice we construct the right URL per region id. For now call Directus-like endpoint:
        try:
            # Using http_client wrapper (init in app startup)
            # note: http_client.get(path_or_url, headers=...)
            resp = await http_client.get(f"/GetMeetingDetailList?Month={month}&Year={year}&RegionId={regions.index(region)+1}")
            if not resp or not resp.get("ResponseBody"):
                summary["skipped"] += 1
                continue

            # Clean discussions that may be HTML, convert to lists etc.
            response_body = resp["ResponseBody"]
            for item in response_body:
                # Normalize meeting.discussion to list of cleaned strings
                meetings = item.get("meeting", [])
                for m in meetings:
                    disc = m.get("discussion")
                    if isinstance(disc, str):
                        m["discussion"] = [clean_html(disc)]
                    elif isinstance(disc, list):
                        m["discussion"] = [clean_html(x) for x in disc]
            # Post each meeting as separate item into Directus/Tanmiya
            for meeting in response_body:
                post_payload = {
                    "date": meeting.get("date", "").split("T")[0],
                    "participants": meeting.get("participants", {}),
                    "meeting": meeting.get("meeting", []),
                    "number_of_topic": meeting.get("number_of_topic", 0),
                    "transferred_topic": meeting.get("transferred_topic", 0),
                }
                try:
                    await directus_service.post_item(collection_name=region, payload=post_payload)
                    summary["posted"] += 1
                except Exception as e:
                    logger.exception("Failed to post meeting to directus for region %s: %s", region, e)
                    summary["errors"].append({"region": region, "error": str(e)})
        except Exception as e:
            logger.exception("Error fetching data for region %s: %s", region, e)
            summary["errors"].append({"region": region, "error": str(e)})

    return summary
