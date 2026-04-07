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
"""

from leadgen.config import GOOGLE_MAPS_API_KEY, log
from leadgen.email_scraper import scrape_email_from_website
from leadgen.exporter import export_to_csv, export_to_jsonl, to_records


def generate_leads(
    keyword: str,
    location: str,
    max_results: int = 100,
    scrape_emails: bool = True,
) -> list[dict]:
    """
    Collect business leads from Google Maps.

    Automatically uses the Places API when GOOGLE_MAPS_API_KEY is set,
    otherwise falls back to the Playwright browser scraper (free, no key needed).

    Args:
        keyword:       Search term  (e.g. "dentist", "restaurant")
        location:      Target area  (e.g. "Brussels", "New York")
        max_results:   Cap on unique leads to return (default 100)
        scrape_emails: If True, visit each website to find a contact email

    Returns:
        List of dicts with keys:
        name, address, phone, website, email, rating, category, maps_url, city
    """
    log.info("=== Lead generation: %r in %r (max %d) ===", keyword, location, max_results)

    # ── Choose extraction backend ────────────────────────────────────────────
    if GOOGLE_MAPS_API_KEY:
        log.info("Mode: Google Places API")
        from leadgen.maps_client import collect_place_ids, fetch_lead

        place_ids = collect_place_ids(keyword, location, max_results)
        log.info("Found %d place IDs — fetching details…", len(place_ids))

        raw_leads: list[dict] = []
        for i, place_id in enumerate(place_ids, 1):
            log.info("[%d/%d] place_id=%s", i, len(place_ids), place_id)
            try:
                raw_leads.append(fetch_lead(place_id))
            except Exception as exc:
                log.warning("  Detail fetch failed: %s", exc)

    else:
        log.info("Mode: Playwright scraper (no API key found)")
        from leadgen.scraper import scrape_google_maps
        raw_leads = scrape_google_maps(keyword, location, max_results)

    # ── Deduplicate ──────────────────────────────────────────────────────────
    leads: list[dict] = []
    seen: set[tuple]  = set()

    for lead in raw_leads:
        key = (lead["name"].lower().strip(), lead["address"].lower().strip())
        if key in seen:
            log.debug("  Duplicate — skipping: %s", lead["name"])
            continue
        seen.add(key)
        leads.append(lead)

    log.info("After dedup: %d unique leads.", len(leads))

    # ── Email enrichment ─────────────────────────────────────────────────────
    if scrape_emails:
        for lead in leads:
            if lead.get("email") or not lead.get("website"):
                continue
            log.info("  Scraping email from %s…", lead["website"])
            try:
                lead["email"] = scrape_email_from_website(lead["website"])
                if lead["email"]:
                    log.info("  Email found: %s", lead["email"])
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
