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

logger = logging.getLogger("tanmiya.services.prediction")


async def predict_future_scores() -> List[Dict[str, Any]]:
    """
    Fetch historical leaderboard data for all regions,
    run the LSTM trainer/predictor per-region, and upsert predictions to Directus.
    Returns the list of predicted items.
    """
    # get all items (may need pagination)
    items = await directus_service.get_all_leaderboard_items()
    # items is expected as list of dict-like records keyed by date_created and metrics
    predictions = []

    # group items by region id
    regions_map = {}
    for it in items:
        rid = it.get("Region_id")
        regions_map.setdefault(rid, []).append(it)

    for region_id, records in regions_map.items():
        try:
            # train_and_predict expects records in a list of dicts with "meeting_score" etc
            pred = train_and_predict(records)
            out = {
                "id": region_id,
                "Region_id": region_id,
                "Region": records[0].get("Region"),
                "meeting_score": float(pred["meeting_score"]),
                "participants_score": float(pred["participants_score"]),
                "total_topics": int(pred["total_topics"]),
                "transferred_topics": int(pred["transferred_topics"]),
                "total_score": float(pred["total_score"])
            }
            predictions.append(out)
        except Exception as e:
            logger.exception("Prediction failed for region_id %s: %s", region_id, e)

    # upsert into Directus target collection (Leaderboard_predict)
    try:
        await directus_service.upsert_predictions(predictions)
    except Exception as e:
        logger.exception("Failed to upsert predictions: %s", e)

    return predictions
