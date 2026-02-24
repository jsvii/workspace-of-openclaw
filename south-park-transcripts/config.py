"""Configuration for South Park transcripts scraper."""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# IMSDb configuration
IMSDB_BASE_URL = "https://imsdb.com"
SOUTH_PARK_URL = f"{IMSDB_BASE_URL}/TV/South%20Park.html"

# Browser configuration
BROWSER_TIMEOUT = 30000  # 30 seconds

# Request configuration
DELAY_BETWEEN_REQUESTS = 1.0  # seconds between requests
REQUEST_TIMEOUT = 30  # seconds

# Output format
OUTPUT_FORMAT = "fountain"  # fountain or plain
