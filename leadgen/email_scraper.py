"""
Email extraction from business websites.

Strategy per site:
  1. homepage   – scan mailto: links
  2. /contact   – scan mailto: links → footer → full-page regex
  3. /about     – same fallback chain

Returns the first valid, non-generic business email found.
"""

import time
import random
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from leadgen.config import (
    EMAIL_REGEX,
    GENERIC_EMAIL_PATTERNS,
    HEADERS,
    RATE_LIMIT_MIN,
    RATE_LIMIT_MAX,
    WEBSITE_TIMEOUT,
    log,
)


def _sleep():
    time.sleep(random.uniform(RATE_LIMIT_MIN, RATE_LIMIT_MAX))


def is_generic_email(email: str) -> bool:
    return bool(GENERIC_EMAIL_PATTERNS.search(email))


def _extract_emails_from_html(html: str, site_domain: str) -> list[str]:
    """
    Return unique, non-generic emails from raw HTML.
    Same-domain emails are sorted first.
    """
    found = EMAIL_REGEX.findall(html)
    results: list[str] = []
    seen: set[str] = set()

    for email in found:
        email = email.lower().strip(".,;")
        if email in seen or is_generic_email(email):
            continue
        seen.add(email)
        results.append(email)

    results.sort(key=lambda e: (0 if site_domain in e else 1))
    return results


def _fetch(url: str, client: httpx.Client) -> Optional[str]:
    """GET url, return HTML string or None on any failure."""
    try:
        r = client.get(url, timeout=WEBSITE_TIMEOUT, follow_redirects=True)
        if r.status_code == 200:
            return r.text
    except Exception as exc:
        log.debug("Fetch failed %s: %s", url, exc)
    return None


def scrape_email_from_website(website: str) -> str:
    """
    Attempt to extract a business email from the given website URL.
    Returns first valid email found, or empty string.
    """
    if not website:
        return ""

    parsed = urlparse(website)
    domain = parsed.netloc.lstrip("www.")

    pages_to_try = [
        website,
        urljoin(website, "/contact"),
        urljoin(website, "/contact-us"),
        urljoin(website, "/contact.html"),
        urljoin(website, "/about"),
    ]

    with httpx.Client(headers=HEADERS, verify=False) as client:
        for url in pages_to_try:
            html = _fetch(url, client)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # 1. mailto: links — highest confidence
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith("mailto:"):
                    email = href[7:].split("?")[0].strip().lower()
                    if email and not is_generic_email(email):
                        return email

            # 2. Footer section
            footer = soup.find("footer")
            if footer:
                emails = _extract_emails_from_html(footer.get_text(), domain)
                if emails:
                    return emails[0]

            # 3. Full-page regex sweep
            emails = _extract_emails_from_html(html, domain)
            if emails:
                return emails[0]

            _sleep()

    return ""
