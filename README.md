# maps-leadgen

Reusable Python tool that extracts structured business leads from Google Maps and exports them to CSV.

## Features

- Search by **keyword** (dentist, restaurant, real estate…) and **location** (city, country, region)
- Extracts: name, address, phone, website, email, rating, category, Google Maps URL, city
- **Email extraction** — scrapes business websites (mailto links → footer → full-page regex)
- **Two modes** — automatically selected:
  - **Google Places API** (fast, structured) — requires an API key
  - **Playwright scraper** (free, no account needed) — headless Chrome
- Deduplication, rate limiting, progress logs
- CSV + optional JSONL export

## Project structure

```
maps-leadgen/
├── main.py                  # CLI entry point
├── requirements.txt
├── .env.example
└── leadgen/
    ├── __init__.py          # generate_leads() — public API + orchestration
    ├── config.py            # constants, env vars, logging
    ├── maps_client.py       # Google Places API (search + details)
    ├── scraper.py           # Playwright scraper (free fallback)
    ├── email_scraper.py     # website email extraction
    └── exporter.py          # CSV / JSONL export
```

## Setup

```bash
# 1. Clone and create a virtual environment
git clone https://github.com/Zied-Dahmani/maps-leadgen.git
cd maps-leadgen
python3 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the browser (only needed for the Playwright scraper)
playwright install chromium

# 4. (Optional) Add your Google Maps API key
cp .env.example .env
# Edit .env and set GOOGLE_MAPS_API_KEY=your_key_here
```

> Without an API key the tool automatically uses the Playwright scraper — no account or billing required.

## Usage

```bash
# Basic
python main.py --keyword dentist --location Brussels --max 50

# Skip email scraping (much faster)
python main.py --keyword restaurant --location "New York" --max 200 --no-email

# Also export JSONL
python main.py --keyword "real estate" --location Paris --jsonl

# Interactive mode (prompts for keyword and location)
python main.py
```

Output file: `leads_<keyword>_<location>.csv`

### CSV columns

| Column | Description |
|--------|-------------|
| name | Business name |
| address | Full formatted address |
| phone | Phone number |
| website | Website URL |
| email | Contact email (scraped from website) |
| rating | Google rating (0–5) |
| category | Business category |
| maps_url | Direct Google Maps link |
| city | Parsed from address |

## Use as a library

```python
from leadgen import generate_leads, export_to_csv

leads = generate_leads(keyword="dentist", location="Brussels", max_results=50)
export_to_csv(leads, keyword="dentist", location="Brussels")
```

`generate_leads` returns a `list[dict]` — plug into any downstream sink (Notion, Airtable, CRM):

```python
from leadgen import generate_leads, to_records

leads  = generate_leads("lawyer", "Amsterdam", max_results=100)
records = to_records(leads)   # clean list[dict], ready for any API
```

## Notes on scale

The Google Places API returns a maximum of **60 results per search query** (3 pages × 20). To collect 1 000+ leads, run the tool across multiple sub-locations or keyword variants and merge the resulting CSVs — the deduplication logic handles overlaps.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_MAPS_API_KEY` | No | Enables the Places API mode. Get one at [console.cloud.google.com](https://console.cloud.google.com/apis/credentials) — enable **Places API**. |
