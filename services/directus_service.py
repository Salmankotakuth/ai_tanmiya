# app/services/directus_service.py

import httpx
import logging
from typing import Any, Dict, List, Optional
from app.config.settings import settings

logger = logging.getLogger("tanmiya.services.directus")


# ------------------------------------------------
# 1. Internal helper: create authenticated headers
# ------------------------------------------------
def _headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.DIRECTUS_TOKEN}"
    }


# ------------------------------------------------
# 2. Generic HTTP helpers
# ------------------------------------------------
async def _get(path: str) -> Any:
    url = f"{settings.DIRECTUS_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"GET {url} failed: {e}")
        raise


async def _post(path: str, payload: dict) -> Any:
    url = f"{settings.DIRECTUS_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"POST {url} failed: {e}")
        raise


async def _patch(path: str, payload: dict) -> Any:
    url = f"{settings.DIRECTUS_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.patch(url, json=payload, headers=_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"PATCH {url} failed: {e}")
        raise


# ------------------------------------------------
# 3. File upload to Directus
# ------------------------------------------------
async def upload_file(filepath: str, folder_id: Optional[str] = None) -> str:
    """
    Uploads PDF or any file to Directus /files endpoint.
    Returns the uploaded file ID.
    """
    url = f"{settings.DIRECTUS_URL}/files"

    data = {"folder": folder_id} if folder_id else {}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            with open(filepath, "rb") as f:
                files = {"file": (filepath, f)}
                resp = await client.post(
                    url,
                    data=data,
                    files=files,
                    headers={"Authorization": f"Bearer {settings.DIRECTUS_TOKEN}"}
                )
                resp.raise_for_status()
                return resp.json()["data"]["id"]
    except Exception as e:
        logger.error(f"File upload failed for {filepath}: {e}")
        raise


# ------------------------------------------------
# 4. Region Helpers (cached)
# ------------------------------------------------

_region_cache: Dict[str, int] = {}   # name → id
_region_reverse: Dict[int, str] = {} # id → name


async def _load_regions():
    """
    Load region mapping from Directus collection 'regions'
    Expected fields: id, name
    """
    global _region_cache, _region_reverse

    if _region_cache:
        return  # already loaded

    # Static region list
    regions = [
        "Muscat", "Al_Batinah_North", "Musandam", "Al_Buraimi",
        "ADhahirah", "ADakhiliya", "ASharqiyah_North", "Al_Wusta",
        "Dhofar", "Al_Batinah_South", "ASharqiyah_South"
    ]

    # Generate IDs as 1…N
    for idx, name in enumerate(regions, start=1):
        _region_cache[name] = idx
        _region_reverse[idx] = name


async def get_regions_list() -> List[str]:
    await _load_regions()
    return list(_region_cache.keys())


async def get_region_id(name: str) -> int:
    await _load_regions()
    return _region_cache.get(name, 0)


async def get_region_name(rid: int) -> str:
    await _load_regions()
    return _region_reverse.get(rid, "")


# ------------------------------------------------
# 5. Meeting Data Fetching
# ------------------------------------------------

async def get_items_for_region(region_name: str, month: str, year: str) -> List[dict]:
    region_id = await get_region_id(region_name)
    path = f"/items/{region_name}?filter[month][_eq]={month}&filter[year][_eq]={year}&limit=200"
    resp = await _get(path)
    return resp.get("data", [])


async def post_item(collection_name: str, payload: dict):
    return await _post(f"/items/{collection_name}", payload)


# ------------------------------------------------
# 6. Leaderboard Operations
# ------------------------------------------------

async def get_all_leaderboard_items() -> List[dict]:
    resp = await _get("/items/Leaderboard_all?limit=500")
    return resp.get("data", [])


async def upsert_leaderboard(items: List[dict]):
    """
    Accepts list of region results and inserts them into:
    - Leaderboard (monthly snapshot)
    - Leaderboard_all (historical series)
    """
    for item in items:
        await _post("/items/Leaderboard", item)
        await _post("/items/Leaderboard_all", item)


async def upsert_predictions(predictions: List[dict]):
    for p in predictions:
        await _post("/items/Leaderboard_predict", p)


async def get_leaderboard_latest() -> List[dict]:
    resp = await _get("/items/Leaderboard?limit=50")
    return resp.get("data", [])


async def get_leaderboard_predictions() -> List[dict]:
    resp = await _get("/items/Leaderboard_predict?limit=50")
    return resp.get("data", [])


# ------------------------------------------------
# 7. Report Operations
# ------------------------------------------------

async def post_reports(reports: List[dict]):
    for r in reports:
        await _post("/items/report", r)


async def get_reports(month: str, year: str) -> List[dict]:
    path = f"/items/report?filter[month][_eq]={month}/{year}&limit=200"
    resp = await _get(path)
    return resp.get("data", [])
