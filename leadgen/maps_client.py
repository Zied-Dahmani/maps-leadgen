"""
Google Places API client.

Exposes two public functions:
  - collect_place_ids(keyword, location, max_results) → list[str]
  - fetch_lead(place_id)                              → dict
"""

import re
import time
import random
from typing import Optional

import requests

from leadgen.config import (
    GOOGLE_MAPS_API_KEY,
    PLACES_TEXT_SEARCH_URL,
    PLACES_DETAILS_URL,
    DETAIL_FIELDS,
    REQUEST_TIMEOUT,
    RATE_LIMIT_MIN,
    RATE_LIMIT_MAX,
    log,
)


def _sleep():
    time.sleep(random.uniform(RATE_LIMIT_MIN, RATE_LIMIT_MAX))


# ---------------------------------------------------------------------------
# Low-level API wrappers
# ---------------------------------------------------------------------------

def _text_search(keyword: str, location: str, page_token: Optional[str] = None) -> dict:
    params: dict = {
        "query":    f"{keyword} in {location}",
        "key":      GOOGLE_MAPS_API_KEY,
        "language": "en",
    }
    if page_token:
        params["pagetoken"] = page_token

    resp = requests.get(PLACES_TEXT_SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _details(place_id: str) -> dict:
    params = {
        "place_id": place_id,
        "fields":   ",".join(DETAIL_FIELDS),
        "key":      GOOGLE_MAPS_API_KEY,
        "language": "en",
    }
    resp = requests.get(PLACES_DETAILS_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("result", {})


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def _parse_city(address: str) -> str:
    """Best-effort city extraction from a formatted address string."""
    if not address:
        return ""
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 3:
        return parts[-3]
    elif len(parts) == 2:
        return parts[0]
    return parts[0] if parts else ""


def _detail_to_lead(detail: dict) -> dict:
    """Map a Places Details response to a flat lead dict."""
    address  = detail.get("formatted_address", "")
    types    = detail.get("types", [])
    category = types[0].replace("_", " ").title() if types else ""

    return {
        "name":     detail.get("name", ""),
        "address":  address,
        "phone":    detail.get("formatted_phone_number", ""),
        "website":  detail.get("website", ""),
        "email":    detail.get("email", ""),   # usually empty from Maps
        "rating":   detail.get("rating", ""),
        "category": category,
        "maps_url": detail.get("url", ""),
        "city":     _parse_city(address),
    }


# ---------------------------------------------------------------------------
# Main public functions
# ---------------------------------------------------------------------------

def collect_place_ids(keyword: str, location: str, max_results: int) -> list[str]:
    """
    Paginate through Places Text Search and return up to max_results place IDs.
    Google returns at most 60 results (3 pages × 20).
    """
    place_ids: list[str] = []
    page_token: Optional[str] = None
    page = 0

    while len(place_ids) < max_results:
        page += 1
        log.info("Fetching search page %d (collected %d/%d)…", page, len(place_ids), max_results)

        if page_token:
            # Google requires ~2 s before a next_page_token becomes valid
            time.sleep(2.5)

        try:
            data = _text_search(keyword, location, page_token)
        except Exception as exc:
            log.error("Text search failed: %s", exc)
            break

        status = data.get("status")
        if status == "ZERO_RESULTS":
            log.info("No more results from Google.")
            break
        if status not in ("OK", "UNKNOWN_ERROR"):
            log.warning("Unexpected API status: %s — %s", status, data.get("error_message", ""))
            break

        for r in data.get("results", []):
            pid = r.get("place_id")
            if pid and pid not in place_ids:
                place_ids.append(pid)
            if len(place_ids) >= max_results:
                break

        page_token = data.get("next_page_token")
        if not page_token:
            log.info("Reached last page of results.")
            break

    return place_ids


def fetch_lead(place_id: str) -> dict:
    """
    Fetch full Place Details for a single place_id.
    Returns a flat lead dict (email field usually empty — enriched later).
    """
    _sleep()
    detail = _details(place_id)
    return _detail_to_lead(detail)
