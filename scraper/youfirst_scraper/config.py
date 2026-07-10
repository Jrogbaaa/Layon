import os
from pathlib import Path

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PACKAGE_DIR / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Instagram account used to authenticate scraping (session file created separately via
# `instaloader --login=<IG_USERNAME>` — the password is never handled by this codebase).
IG_USERNAME = os.environ.get("IG_USERNAME", "")

INFLUENCERS_FILE = PACKAGE_DIR / "influencers.txt"

TREND_SOURCES = [
    "https://trends.google.com/trending/rss?geo=ES",
    "https://www.20minutos.es/rss/gente/",
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/cultura/portada",
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
