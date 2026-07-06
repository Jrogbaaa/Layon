import os
from pathlib import Path

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PACKAGE_DIR / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

INFLUENCERS_FILE = PACKAGE_DIR / "influencers.txt"

TREND_SOURCES = [
    "https://newengen.com/insights/instagram-trends/",
    "https://www.modash.io/content-library/country/spanish-examples",
]

# Seconds to wait between profile requests, to avoid hammering Instagram.
PROFILE_REQUEST_DELAY_SECONDS = 20

# How many recent posts to pull per influencer per run.
POSTS_PER_INFLUENCER = 12

# State file used to guard against running the pipeline more than once per day.
LAST_RUN_FILE = PACKAGE_DIR / ".last_run"


def load_roster() -> list[str]:
    if not INFLUENCERS_FILE.exists():
        return []
    lines = INFLUENCERS_FILE.read_text().splitlines()
    return [line.strip() for line in lines if line.strip()]
