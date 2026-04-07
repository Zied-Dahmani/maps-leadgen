"""
CLI entry point for the Google Maps Lead Generator.

Usage:
    python main.py --keyword dentist --location Brussels --max 50
    python main.py --keyword "real estate" --location "New York" --max 500 --no-email
    python main.py   # interactive prompts
"""

import argparse
import os
import sys

from leadgen import generate_leads, export_to_csv, export_to_jsonl
from leadgen.config import log


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Google Maps Lead Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --keyword dentist --location Brussels --max 50
  python main.py --keyword "real estate" --location "New York" --max 500 --no-email
  python main.py --keyword restaurant --location Paris --jsonl
        """,
    )
    parser.add_argument("--keyword",  "-k", type=str, help="Search keyword (e.g. 'dentist')")
    parser.add_argument("--location", "-l", type=str, help="Target location (e.g. 'Brussels')")
    parser.add_argument("--max",      "-m", type=int, default=100, help="Max results (default: 100)")
    parser.add_argument("--no-email", action="store_true",  help="Skip website email scraping (faster)")
    parser.add_argument("--jsonl",    action="store_true",  help="Also export JSONL alongside CSV")
    parser.add_argument("--output",   "-o", type=str, default=".", help="Output directory (default: .)")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    keyword  = args.keyword  or input("Keyword  (e.g. dentist):            ").strip()
    location = args.location or input("Location (e.g. Brussels, Belgium):  ").strip()

    if not keyword or not location:
        log.error("Keyword and location are required.")
        sys.exit(1)

    leads = generate_leads(
        keyword=keyword,
        location=location,
        max_results=args.max,
        scrape_emails=not args.no_email,
    )

    if not leads:
        log.warning("No leads collected — check your keyword, location, or API key.")
        return

    os.makedirs(args.output, exist_ok=True)

    csv_path = export_to_csv(leads, keyword, location, output_dir=args.output)
    print(f"\nDone! {len(leads)} leads saved to: {csv_path}")

    if args.jsonl:
        jsonl_path = export_to_jsonl(leads, keyword, location, output_dir=args.output)
        print(f"JSONL export:                  {jsonl_path}")


if __name__ == "__main__":
    main()
