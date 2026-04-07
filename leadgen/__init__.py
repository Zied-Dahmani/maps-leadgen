"""
leadgen — Google Maps lead generation package.

Public API:
    generate_leads(keyword, location, max_results, scrape_emails) → list[dict]
    export_to_csv(leads, keyword, location, output_dir)           → str  (file path)
    export_to_jsonl(leads, keyword, location, output_dir)         → str  (file path)
    to_records(leads)                                             → list[dict]

Mode selection (automatic):
    - GOOGLE_MAPS_API_KEY set in .env  →  Google Places API  (faster, more reliable)
    - No API key                       →  Playwright scraper  (free, no account needed)

Scale strategy:
    Google Maps caps each search at ~60 results. To reliably hit max_results > 60,
    generate_leads automatically runs multiple sub-queries (with area/direction
    modifiers) and merges the results until the target count is reached.
"""

from leadgen.config import GOOGLE_MAPS_API_KEY, log
from leadgen.email_scraper import scrape_email_from_website
from leadgen.exporter import export_to_csv, export_to_jsonl, to_records
from leadgen.cities import get_cities


# ---------------------------------------------------------------------------
# Sub-query generation (for breaking the ~60-result cap)
# ---------------------------------------------------------------------------

def _sub_queries(keyword: str, location: str) -> list[str]:
    """
    Return an ordered list of search queries to run until max_results is hit.

    Strategy:
      - If location is a known country → iterate city by city (5 000+ scale)
      - Otherwise → direction/modifier variants of the same location (city scale)
    """
    cities = get_cities(location)

    if cities:
        # Country-level: one query per city, e.g. "restaurant Ghent, Belgium"
        country = location.strip().title()
        return [f"{keyword} {city}, {country}" for city in cities]

    # City-level: modifiers
    return [
        f"{keyword} {location}",
        f"{keyword} {location} center",
        f"{keyword} {location} north",
        f"{keyword} {location} south",
        f"{keyword} {location} east",
        f"{keyword} {location} west",
        f"best {keyword} {location}",
        f"top {keyword} {location}",
        f"{keyword} near {location}",
        f"cheap {keyword} {location}",
        f"popular {keyword} {location}",
    ]


# ---------------------------------------------------------------------------
# Deduplication helper
# ---------------------------------------------------------------------------

def _dedup(leads: list[dict], seen: set[tuple]) -> tuple[list[dict], set[tuple]]:
    unique = []
    for lead in leads:
        key = (lead["name"].lower().strip(), lead["address"].lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(lead)
    return unique, seen


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_leads(
    keyword: str,
    location: str,
    max_results: int = 100,
    scrape_emails: bool = True,
) -> list[dict]:
    """
    Collect business leads from Google Maps.

    Automatically uses the Places API when GOOGLE_MAPS_API_KEY is set,
    otherwise uses the Playwright browser scraper (free, no account needed).

    Runs multiple sub-queries (area modifiers) until max_results is reached,
    so asking for 100 actually returns 100 when available.

    Args:
        keyword:       Search term  (e.g. "dentist", "restaurant")
        location:      Target area  (e.g. "Brussels", "New York")
        max_results:   Target number of unique leads (default 100)
        scrape_emails: If True, visit each website to find a contact email

    Returns:
        List of dicts with keys:
        name, address, phone, website, email, rating, category, maps_url, city
    """
    log.info("=== Lead generation: %r in %r (target %d) ===", keyword, location, max_results)

    leads: list[dict] = []
    seen:  set[tuple] = set()
    queries = _sub_queries(keyword, location)

    if GOOGLE_MAPS_API_KEY:
        log.info("Mode: Google Places API")
        from leadgen.maps_client import collect_place_ids, fetch_lead

        for query_idx, query in enumerate(queries):
            if len(leads) >= max_results:
                break

            needed = max_results - len(leads)
            # Extract keyword+location from the composite query for the API
            q_keyword, _, q_location = query.partition(" ")
            log.info("Sub-query %d/%d: %r (need %d more)", query_idx + 1, len(queries), query, needed)

            place_ids = collect_place_ids(q_keyword, q_location or location, needed)

            for i, place_id in enumerate(place_ids, 1):
                if len(leads) >= max_results:
                    break
                log.info("  [%d/%d] place_id=%s", i, len(place_ids), place_id)
                try:
                    raw = fetch_lead(place_id)
                    new, seen = _dedup([raw], seen)
                    leads.extend(new)
                except Exception as exc:
                    log.warning("  Detail fetch failed: %s", exc)

    else:
        log.info("Mode: Playwright scraper (no API key found)")
        from leadgen.scraper import scrape_google_maps

        for query_idx, query in enumerate(queries):
            if len(leads) >= max_results:
                break

            needed = max_results - len(leads)
            log.info(
                "Sub-query %d/%d: %r (have %d/%d, need %d more)",
                query_idx + 1, len(queries), query, len(leads), max_results, needed,
            )

            # Split composite query back into keyword / location for the scraper
            parts  = query.split(" ", 1)
            q_kw   = parts[0]
            q_loc  = parts[1] if len(parts) > 1 else location

            raw = scrape_google_maps(q_kw, q_loc, needed)
            new, seen = _dedup(raw, seen)
            leads.extend(new)
            log.info("  Sub-query yielded %d new leads (total %d)", len(new), len(leads))

            if not new:
                log.info("  No new results from this sub-query — moving on.")

    log.info("Collection complete: %d unique leads.", len(leads))

    # ── Email enrichment ─────────────────────────────────────────────────────
    if scrape_emails:
        to_enrich = [l for l in leads if not l.get("email") and l.get("website")]
        log.info("Scraping emails for %d leads with a website…", len(to_enrich))
        for lead in to_enrich:
            log.info("  Scraping %s…", lead["website"])
            try:
                lead["email"] = scrape_email_from_website(lead["website"])
                if lead["email"]:
                    log.info("  Found: %s", lead["email"])
            except Exception as exc:
                log.debug("  Email scrape error: %s", exc)

    log.info("Done. %d leads ready.", len(leads))
    return leads


__all__ = [
    "generate_leads",
    "export_to_csv",
    "export_to_jsonl",
    "to_records",
]
