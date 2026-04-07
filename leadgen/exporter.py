"""
Export utilities.

Supports:
  - CSV  (default, Excel-compatible UTF-8 BOM)
  - JSONL (newline-delimited JSON)

On repeated runs for the same keyword + location, the exporter:
  1. Reads ALL existing CSVs for that keyword+location to build a dedup set
  2. Writes ONLY the new (unseen) leads to a NEW timestamped file
  3. Never modifies existing files — safe for Google Sheets workflows where
     your team may have added status/notes columns to previous exports.

File naming:
  leads_<keyword>_<location>.csv          ← first run
  leads_<keyword>_<location>_2.csv        ← second run (new leads only)
  leads_<keyword>_<location>_3.csv        ← third run, etc.
"""

import csv
import glob
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


def _next_filepath(base: str, output_dir: str) -> str:
    """
    Return the next available file path.
    e.g. leads_dentist_brussels.csv → leads_dentist_brussels_2.csv → _3.csv …
    """
    first = os.path.join(output_dir, f"{base}.csv")
    if not os.path.exists(first):
        return first

    n = 2
    while True:
        path = os.path.join(output_dir, f"{base}_{n}.csv")
        if not os.path.exists(path):
            return path
        n += 1


def _load_existing_keys(base: str, output_dir: str) -> set[tuple]:
    """
    Collect (name, address) dedup keys from every existing CSV
    that matches this keyword + location, regardless of run number.
    """
    pattern = os.path.join(output_dir, f"{base}*.csv")
    seen: set[tuple] = set()

    for filepath in glob.glob(pattern):
        try:
            df = pd.read_csv(filepath, dtype=str, encoding="utf-8-sig")
            for _, row in df.fillna("").iterrows():
                seen.add(_dedup_key(row.to_dict()))
            log.info("Loaded %d existing keys from %s", len(df), filepath)
        except Exception as exc:
            log.warning("Could not read %s: %s", filepath, exc)

    return seen


def export_to_csv(
    leads: list[dict],
    keyword: str,
    location: str,
    output_dir: str = "output",
) -> str:
    """
    Export new leads to a new CSV file, skipping any already seen in previous runs.

    - Reads all existing CSVs for this keyword+location to build a dedup set
    - Writes ONLY unseen leads to a new numbered file
    - Never modifies existing files

    Returns the path to the newly created file, or empty string if no new leads.
    """
    os.makedirs(output_dir, exist_ok=True)
    base = f"leads_{_safe_filename(keyword)}_{_safe_filename(location)}"

    existing_keys = _load_existing_keys(base, output_dir)
    log.info("Found %d leads across existing files for '%s %s'", len(existing_keys), keyword, location)

    new_records = [
        r for r in to_records(leads)
        if _dedup_key(r) not in existing_keys
    ]

    skipped = len(leads) - len(new_records)
    if skipped:
        log.info("Skipped %d leads already in previous exports.", skipped)

    if not new_records:
        log.info("No new leads to write — all %d were duplicates of existing exports.", len(leads))
        return ""

    filepath = _next_filepath(base, output_dir)
    df = pd.DataFrame(new_records, columns=LEAD_COLUMNS)
    df.to_csv(filepath, index=False, quoting=csv.QUOTE_ALL, encoding="utf-8-sig")

    log.info("CSV → %s | %d new leads written | %d duplicates skipped", filepath, len(df), skipped)
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
    base = f"leads_{_safe_filename(keyword)}_{_safe_filename(location)}"
    filename = f"{base}.jsonl"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        for lead in to_records(leads):
            f.write(json.dumps(lead, ensure_ascii=False) + "\n")

    log.info("JSONL → %s (%d rows)", filepath, len(leads))
    return filepath
