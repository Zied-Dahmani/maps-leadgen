"""
Export utilities.

Supports:
  - CSV  (default, Excel-compatible UTF-8 BOM)
  - JSONL (newline-delimited JSON — easy to stream into any API)

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


def to_records(leads: list[dict]) -> list[dict]:
    """Normalise leads to the canonical column set — ready for any downstream sink."""
    return [{col: lead.get(col, "") for col in LEAD_COLUMNS} for lead in leads]


def export_to_csv(leads: list[dict], keyword: str, location: str, output_dir: str = ".") -> str:
    """
    Save leads to CSV.
    Returns the absolute file path.
    """
    filename = f"leads_{_safe_filename(keyword)}_{_safe_filename(location)}.csv"
    filepath = os.path.join(output_dir, filename)

    df = pd.DataFrame(to_records(leads), columns=LEAD_COLUMNS)
    df.to_csv(filepath, index=False, quoting=csv.QUOTE_ALL, encoding="utf-8-sig")
    log.info("CSV  → %s (%d rows)", filepath, len(df))
    return filepath


def export_to_jsonl(leads: list[dict], keyword: str, location: str, output_dir: str = ".") -> str:
    """
    Save leads as newline-delimited JSON.
    Returns the absolute file path.
    """
    filename = f"leads_{_safe_filename(keyword)}_{_safe_filename(location)}.jsonl"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        for lead in to_records(leads):
            f.write(json.dumps(lead, ensure_ascii=False) + "\n")

    log.info("JSONL → %s (%d rows)", filepath, len(leads))
    return filepath
