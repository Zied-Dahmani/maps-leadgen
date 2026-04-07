"""
Centralised configuration: environment variables, constants, and logging.
All other modules import from here — nothing reads os.getenv() elsewhere.
"""

import os
import re
import logging

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging (configure once at import time)
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("leadgen")

# ---------------------------------------------------------------------------
# API credentials
# ---------------------------------------------------------------------------

GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ---------------------------------------------------------------------------
# Google Places API endpoints
# ---------------------------------------------------------------------------

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL     = "https://maps.googleapis.com/maps/api/place/details/json"

DETAIL_FIELDS = [
    "name",
    "formatted_address",
    "formatted_phone_number",
    "website",
    "rating",
    "types",
    "url",
    "email",             # rarely present in Maps, but worth requesting
    "editorial_summary",
]

# ---------------------------------------------------------------------------
# Timing / rate limiting
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT = 15    # seconds – Places API calls
RATE_LIMIT_MIN  = 0.8   # seconds – min delay between requests
RATE_LIMIT_MAX  = 2.2   # seconds – max delay between requests
WEBSITE_TIMEOUT = 12    # seconds – website scraping calls

# ---------------------------------------------------------------------------
# Email filtering
# ---------------------------------------------------------------------------

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

GENERIC_EMAIL_PATTERNS = re.compile(
    r"(example|test|noreply|no-reply|donotreply|support@gmail|info@gmail"
    r"|admin@gmail|contact@gmail|@sentry|@email\.com|@domain\.|wixpress"
    r"|squarespace|wordpress|mailchimp|sendgrid)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# HTTP headers (browser-like, avoids most bot detection)
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# Lead schema — single source of truth for column order
# ---------------------------------------------------------------------------

LEAD_COLUMNS = [
    "name",
    "address",
    "phone",
    "website",
    "email",
    "rating",
    "category",
    "maps_url",
    "city",
]
