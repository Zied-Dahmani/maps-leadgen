"""
Export utilities.

Supports:
  - CSV  (default, Excel-compatible UTF-8 BOM) — with append + dedup
  - JSONL (newline-delimited JSON)

Add new exporters here (Notion, Airtable, CRM) without touching core logic.
"""

import csv
import json
import os
import re

import pandas as pd

from leadgen.config import LEAD_COLUMNS, log


def _safe_filename(text: str) -> str:
    return re.sub(r"[^\w]", "_", text.lower())


def _dedup_key(row: dict) -> tuple:
    return (str(row.get("name", "")).lower().strip(),
            str(row.get("address", "")).lower().strip())


def to_records(leads: list[dict]) -> list[dict]:
    """Normalise leads to the canonical column set — ready for any downstream sink."""
    return [{col: lead.get(col, "") for col in LEAD_COLUMNS} for lead in leads]


def export_to_csv(
    leads: list[dict],
    keyword: str,
    location: str,
    output_dir: str = "output",
) -> str:
    """
    Save leads to CSV, merging with any existing file for the same keyword+location.

    If the file already exists, new leads are appended and the combined result is
    deduplicated by (name, address) before saving. This means you can run the tool
    multiple times for the same city and never get duplicates.

    Returns the absolute file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"leads_{_safe_filename(keyword)}_{_safe_filename(location)}.csv"
    filepath = os.path.join(output_dir, filename)

    new_records = to_records(leads)

    # Merge with existing file if present
    if os.path.exists(filepath):
        try:
            existing_df = pd.read_csv(filepath, dtype=str, encoding="utf-8-sig")
            existing_records = existing_df.fillna("").to_dict("records")
            log.info("Existing file has %d rows — merging…", len(existing_records))
        except Exception as exc:
            log.warning("Could not read existing file (%s) — overwriting.", exc)
            existing_records = []
    else:
        existing_records = []

    # Combine: existing first, new second — then deduplicate keeping first occurrence
    combined = existing_records + new_records
    seen: set[tuple] = set()
    unique: list[dict] = []
    for row in combined:
        key = _dedup_key(row)
        if key not in seen:
            seen.add(key)
            unique.append(row)

    duplicates_removed = len(combined) - len(unique)
    added = len(unique) - len(existing_records)

    df = pd.DataFrame(unique, columns=LEAD_COLUMNS)
    df.to_csv(filepath, index=False, quoting=csv.QUOTE_ALL, encoding="utf-8-sig")

    log.info(
        "CSV → %s | total: %d | added: %d | duplicates removed: %d",
        filepath, len(df), added, duplicates_removed,
    )
    return filepath


def export_to_jsonl(
    leads: list[dict],
    keyword: str,
    location: str,
    output_dir: str = "output",
) -> str:
    """
    Save leads as newline-delimited JSON.
    Returns the absolute file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"leads_{_safe_filename(keyword)}_{_safe_filename(location)}.jsonl"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        for lead in to_records(leads):
            f.write(json.dumps(lead, ensure_ascii=False) + "\n")

    log.info("JSONL → %s (%d rows)", filepath, len(leads))
    return filepath
