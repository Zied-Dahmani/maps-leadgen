"""
Playwright-based Google Maps scraper (no API key required).

How it works:
  1. Opens Google Maps search in a headless browser
  2. Accepts cookie consent (EU/BE)
  3. Scrolls the results sidebar to load listings
  4. Clicks each listing to open its detail panel
  5. Extracts: name, address, phone, website, rating, category, maps_url

Limitations vs the Places API:
  - Slower (real browser, real clicks)
  - Google may throttle or block after many requests
  - Selectors can break when Google updates its UI
"""

import time
import re
from typing import Optional

from leadgen.config import log, RATE_LIMIT_MIN, RATE_LIMIT_MAX

try:
    from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAPS_SEARCH_URL = "https://www.google.com/maps/search/{query}?hl=en"

# Selectors — Google Maps DOM (as of mid-2024)
# These are the most stable selectors; class names change but roles/aria don't.
SEL_RESULTS_FEED   = '[role="feed"]'
SEL_RESULT_ITEM    = '[role="feed"] > div'
SEL_NAME           = "h1.DUwDvf, h1.fontHeadlineLarge"
SEL_ADDRESS        = '[data-item-id="address"]'
SEL_PHONE          = '[data-item-id^="phone:tel"]'
SEL_WEBSITE        = '[data-item-id="authority"]'
SEL_RATING         = 'div.F7nice span[aria-hidden="true"]'
SEL_CATEGORY       = 'button.DkEaL'
SEL_COOKIE_ACCEPT  = 'button[aria-label*="Accept"], button[aria-label*="Accepter"], form:last-of-type button'


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_text(page: "Page", selector: str, default: str = "") -> str:
    try:
        el = page.query_selector(selector)
        return el.inner_text().strip() if el else default
    except Exception:
        return default


def _safe_attr(page: "Page", selector: str, attr: str, default: str = "") -> str:
    try:
        el = page.query_selector(selector)
        return (el.get_attribute(attr) or default).strip() if el else default
    except Exception:
        return default


def _parse_city(address: str) -> str:
    if not address:
        return ""
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 3:
        return parts[-3]
    return parts[0] if parts else ""


def _accept_cookies(page: "Page") -> None:
    try:
        btn = page.query_selector(SEL_COOKIE_ACCEPT)
        if btn:
            btn.click()
            page.wait_for_timeout(800)
    except Exception:
        pass


def _scroll_feed(page: "Page", steps: int = 3) -> None:
    """Scroll the results sidebar to trigger lazy-loading."""
    try:
        feed = page.query_selector(SEL_RESULTS_FEED)
        if feed:
            for _ in range(steps):
                feed.evaluate("el => el.scrollBy(0, 800)")
                page.wait_for_timeout(600)
    except Exception:
        pass


def _extract_detail(page: "Page", maps_url: str) -> dict:
    """Extract all fields from the currently open detail panel."""
    name     = _safe_text(page, SEL_NAME)
    category = _safe_text(page, SEL_CATEGORY)
    rating_raw = _safe_text(page, SEL_RATING)
    try:
        rating = float(rating_raw.replace(",", "."))
    except ValueError:
        rating = ""

    address_el = page.query_selector(SEL_ADDRESS)
    address_raw = address_el.get_attribute("aria-label") or "" if address_el else ""
    # Strip any language's label prefix ("Address: ", "العنوان: ", etc.)
    address = re.sub(r"^[^:]+:\s*", "", address_raw).strip()

    phone_el = page.query_selector(SEL_PHONE)
    phone_raw = phone_el.get_attribute("aria-label") or "" if phone_el else ""
    phone = re.sub(r"^[^:]+:\s*", "", phone_raw).strip()

    website = _safe_attr(page, SEL_WEBSITE, "href")

    return {
        "name":     name,
        "address":  address,
        "phone":    phone,
        "website":  website,
        "email":    "",
        "rating":   rating,
        "category": category,
        "maps_url": maps_url,
        "city":     _parse_city(address),
    }


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def scrape_google_maps(keyword: str, location: str, max_results: int) -> list[dict]:
    """
    Scrape Google Maps results using a headless Playwright browser.

    Args:
        keyword:     Business type (e.g. "dentist")
        location:    Target area   (e.g. "Brussels")
        max_results: Stop after this many unique leads

    Returns:
        List of lead dicts (email field empty — enriched later by generate_leads)
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError(
            "Playwright is not installed.\n"
            "Run:  pip install playwright && playwright install chromium"
        )

    query = f"{keyword} {location}"
    url   = MAPS_SEARCH_URL.format(query=query.replace(" ", "+"))
    log.info("Playwright scraper → %s", url)

    leads: list[dict] = []
    seen_names: set[str] = set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx     = browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="en-US",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            _accept_cookies(page)

            # Wait for the results feed to appear
            try:
                page.wait_for_selector(SEL_RESULTS_FEED, timeout=15_000)
            except PWTimeout:
                log.error("Results feed did not load — Google may have changed its layout.")
                return leads

            # Collect listing elements until we have enough
            scroll_rounds = 0
            while len(leads) < max_results:
                scroll_rounds += 1
                _scroll_feed(page, steps=4)
                page.wait_for_timeout(1_200)

                items = page.query_selector_all(SEL_RESULT_ITEM)
                log.info("Scroll round %d — %d items visible, %d collected",
                         scroll_rounds, len(items), len(leads))

                for item in items:
                    if len(leads) >= max_results:
                        break

                    # Each item needs a clickable link to open the detail panel
                    link = item.query_selector("a")
                    if not link:
                        continue

                    # Quick name pre-check to skip already-seen items
                    name_el = item.query_selector(".qBF1Pd, .fontHeadlineSmall")
                    quick_name = name_el.inner_text().strip() if name_el else ""
                    if quick_name and quick_name in seen_names:
                        continue

                    # Click to open detail panel
                    try:
                        link.click()
                        page.wait_for_selector(SEL_NAME, timeout=8_000)
                        page.wait_for_timeout(800)
                    except PWTimeout:
                        log.debug("  Detail panel timed out, skipping.")
                        continue
                    except Exception as exc:
                        log.debug("  Click failed: %s", exc)
                        continue

                    detail_url = page.url
                    lead = _extract_detail(page, detail_url)

                    if not lead["name"]:
                        continue
                    if lead["name"] in seen_names:
                        continue

                    seen_names.add(lead["name"])
                    leads.append(lead)
                    log.info(
                        "  [%d/%d] %-40s | %s",
                        len(leads), max_results,
                        lead["name"][:40],
                        lead["city"] or lead["address"][:30],
                    )

                # End of feed detection
                end_marker = page.query_selector('span.HlvSq')  # "You've reached the end"
                if end_marker:
                    log.info("Reached end of results.")
                    break

                if scroll_rounds >= max_results // 5 + 10:
                    log.info("Max scroll rounds reached.")
                    break

        except Exception as exc:
            log.error("Scraper error: %s", exc)
        finally:
            browser.close()

    log.info("Playwright scraper done. Collected %d leads.", len(leads))
    return leads
