# app/services/prediction_service.py
"""
Prediction Service
- Uses the multi-output LSTM (app.models.lstm_multi.train_and_predict)
- Fetches historical data from Directus (Leaderboard_all)
- Prepares records and calls train_and_predict
"""

from typing import List, Dict, Any
from app.models.lstm_multi import train_and_predict
from app.services import directus_service
import logging
import datetime
from app.constants.regions import GOVERNORATE_FROM_REGION_ID

logger = logging.getLogger("tanmiya.services.prediction")


async def predict_future_scores() -> List[Dict[str, Any]]:
    """
    Fetch historical leaderboard data for all regions,
    run the LSTM trainer/predictor per-region, and upsert predictions to Directus.
    Returns the list of predicted items.
    """
    # get all items (may need pagination)
    items = await directus_service.get_all_leaderboard_items()

    latest_month = max([datetime.datetime.strptime(item['month'], "%m/%Y") for item in items])
    next_month = (latest_month + datetime.timedelta(days=31)).replace(day=1).strftime("%m/%Y")

    # items is expected as list of dict-like records keyed by date_created and metrics
    predictions = []

    # group items by region id
    regions_map = {}
    for it in items:
        rid = it.get("Region_id")
        regions_map.setdefault(rid, []).append(it)

    for region_id, records in regions_map.items():
        records.sort(key=lambda x: datetime.datetime.strptime(x["month"], "%m/%Y"))
        try:
            # train_and_predict expects records in a list of dicts with "meeting_score" etc
            pred = train_and_predict(records)

            region = GOVERNORATE_FROM_REGION_ID.get(region_id)

            out = {
                "month": next_month,
                "Region_id": region_id,
                "Region": region,
                "meeting_score": f"{round(pred['meeting_score'], 2)}",
                "participants_score": f"{round(pred['participants_score'], 2)}",
                "total_topics": int(pred["total_topics"]),
                "transferred_topics": int(pred["transferred_topics"]),
                "Rank": 0,
                "total_score": f"{round(float(pred['total_score']), 2)}"
            }
            predictions.append(out)
        except Exception as e:
            logger.exception("Prediction failed for region_id %s: %s", region_id, e)

    predictions.sort(key=lambda x: x["total_score"], reverse=True)
    for rank, item in enumerate(predictions, start=1):
        item["Rank"] = rank

    # upsert into Directus target collection (Leaderboard_predict)
    try:
        await directus_service.upsert_predictions(predictions)
    except Exception as e:
        logger.exception("Failed to upsert predictions: %s", e)

    return predictions
