# app/utils/http_client.py

"""
Async HTTP Client Wrapper
-------------------------

A reusable, production‑grade HTTP client that provides:

- A single shared httpx.AsyncClient instance
- Automatic retries with backoff
- Base URL support
- JSON request helpers (GET, POST, PATCH)
- Service ping helper
- Clean shutdown method for FastAPI lifecycle

This module is used by services such as:
- directus_service
- meeting_service
- translation service
- any external API calls
"""

import httpx
import asyncio
import logging
from typing import Any, Optional
from app.config.settings import settings

logger = logging.getLogger("tanmiya.utils.http")

# ----------------------------------------------------------
# Global shared client instance
# ----------------------------------------------------------
_client: Optional[httpx.AsyncClient] = None
_base_url: str = ""
_token: str = ""

# ----------------------------------------------------------
# Initialization
# ----------------------------------------------------------
async def init(base_url: Optional[str] = None, timeout: float = 30.0):
    """
    Initialize the global AsyncClient.
    Call this once inside FastAPI startup event.
    """
    global _client, _base_url, _token       # define as global make these accessible throughout the module

    _base_url = base_url or settings.TANMIYA_BACKEND_BASE_URL
    _token = settings.TANMIYA_BACKEND_TOKEN

    if _client is None:
        _client = httpx.AsyncClient(
            base_url=_base_url,
            timeout=timeout,
            follow_redirects=True,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_token}"
            }
        )
        logger.info(f"Async HTTP client initialized (base_url={_base_url})")


# ----------------------------------------------------------
# Graceful shutdown
# ----------------------------------------------------------
async def close():
    global _client
    if _client:
        await _client.aclose()
        logger.info("Async HTTP client closed.")
        _client = None


# ----------------------------------------------------------
# Retry Wrapper
# ----------------------------------------------------------
async def _with_retries(func, *args, retries=3, delay=1.0, **kwargs):
    """
    Retry any async HTTP operation with exponential backoff.
    """
    for attempt in range(1, retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == retries:
                logger.error(f"HTTP retry failed after {retries} attempts: {e}")
                raise
            wait_time = delay * attempt
            logger.warning(f"HTTP retry {attempt}/{retries} in {wait_time}s due to: {e}")
            await asyncio.sleep(wait_time)


# ----------------------------------------------------------
# JSON GET
# ----------------------------------------------------------
async def get(url: str, headers: dict = None) -> Any:
    if _client is None:
        raise RuntimeError("AsyncHTTPClient not initialized. Call init() first.")

    merged_headers = {
        "Authorization": f"Bearer {_token}",
        **(headers or {})
    }

    async def _do():
        resp = await _client.get(url, headers=merged_headers)
        resp.raise_for_status()
        return resp.json()

    return await _with_retries(_do)


# ----------------------------------------------------------
# JSON POST
# ----------------------------------------------------------
async def post(url: str, json: dict, headers: dict = None) -> Any:
    if _client is None:
        raise RuntimeError("AsyncHTTPClient not initialized. Call init() first.")

    merged_headers = {
        "Authorization": f"Bearer {_token}",
        "Content-Type": "application/json",
        **(headers or {})
    }

    async def _do():
        resp = await _client.post(url, json=json, headers=merged_headers)
        resp.raise_for_status()
        return resp.json()

    return await _with_retries(_do)


# ----------------------------------------------------------
# JSON PATCH
# ----------------------------------------------------------
async def patch(url: str, json: dict, headers: dict = None) -> Any:
    if _client is None:
        raise RuntimeError("AsyncHTTPClient not initialized. Call init() first.")

    merged_headers = {
        "Authorization": f"Bearer {_token}",
        **(headers or {})
    }

    async def _do():
        resp = await _client.patch(url, json=json, headers=merged_headers)
        resp.raise_for_status()
        return resp.json()

    return await _with_retries(_do)


# ----------------------------------------------------------
# Service Ping (health check)
# ----------------------------------------------------------
async def ping_service(url: str) -> bool:
    """
    Returns True if the service responds 200 OK.
    """
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
            return resp.status_code == 200
    except Exception:
        return False
