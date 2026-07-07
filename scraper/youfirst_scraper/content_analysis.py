import json
import logging
from statistics import median

import requests
from google import genai
from google.genai import types

from . import config

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
MAX_POSTS_PER_RUN = 4


def select_posts_to_analyze(posts: list[dict], already_analyzed: set[str]) -> list[dict]:
    """Pick unanalyzed posts at/above median engagement, or reels at/above median reel views.

    Capped at MAX_POSTS_PER_RUN, highest engagement first.
    """
    candidates = [p for p in posts if p["shortcode"] not in already_analyzed]
    if not candidates:
        return []

    engagements = [p["likes"] + p["comments"] for p in posts]
    median_engagement = median(engagements) if engagements else 0

    reel_views = [p["views"] for p in posts if p.get("post_type") == "reel" and p.get("views")]
    median_views = median(reel_views) if reel_views else 0

    selected = [
        p
        for p in candidates
        if p["likes"] + p["comments"] >= median_engagement
        or (p.get("post_type") == "reel" and p.get("views") and p["views"] >= median_views)
    ]
    selected.sort(key=lambda p: p["likes"] + p["comments"], reverse=True)
    return selected[:MAX_POSTS_PER_RUN]


def _fetch_media_bytes(post: dict) -> tuple[bytes, str]:
    """Download the post's video (if any) or thumbnail image. Returns (bytes, mime_type)."""
    url = post.get("video_url") or post["thumbnail_url"]
    mime_type = "video/mp4" if post.get("video_url") else "image/jpeg"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content, mime_type


def analyze_post(client: genai.Client, post: dict) -> dict:
    """Send the post's video/thumbnail + caption to Gemini and return {summary, analysis}.

    Raises on download or Gemini failure — the caller is responsible for catching and
    skipping so one bad post doesn't abort the run.
    """
    media_bytes, mime_type = _fetch_media_bytes(post)

    prompt = f"""Eres un analista de contenido de Instagram para una agencia de talento.

Mira este {"video (con audio)" if mime_type == "video/mp4" else "imagen"} de una
publicación de Instagram. Descripción original: {post.get("caption") or "(sin descripción)"}

Responde en español, en JSON con esta forma exacta:
{{"summary": "1-2 frases sobre de qué trata el contenido", "topic": "tema principal",
"format": "formato/estilo (p. ej. tutorial, humor, día en la vida, transición)",
"hook": "cómo capta la atención en los primeros segundos"}}"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=media_bytes, mime_type=mime_type),
            prompt,
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    analysis = json.loads(response.text)
    return {"summary": analysis["summary"], "analysis": analysis}


def analyze_posts(posts: list[dict], already_analyzed: set[str]) -> list[dict]:
    """Analyze the selected posts, returning [{shortcode, summary, analysis}, ...].

    Skips any post whose download or Gemini analysis fails, logging and continuing.
    """
    to_analyze = select_posts_to_analyze(posts, already_analyzed)
    if not to_analyze:
        return []

    client = genai.Client(api_key=config.GOOGLE_API_KEY)
    results = []
    for post in to_analyze:
        try:
            result = analyze_post(client, post)
            results.append({"shortcode": post["shortcode"], **result})
        except Exception:
            logger.exception("Failed to analyze post %s — skipping", post["shortcode"])
    return results
