import json
import logging

import requests
from google import genai
from google.genai import types

from . import config

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"

# Gemini rejects inline media past ~20MB, and a long Reel can be far larger than that.
MAX_INLINE_MEDIA_BYTES = 15 * 1024 * 1024


def _fetch_media_bytes(post: dict) -> tuple[bytes, str]:
    """Download the post's video (if any) or thumbnail image. Returns (bytes, mime_type).

    Oversized videos fall back to the thumbnail rather than being downloaded and
    rejected — classifying from the still frame beats failing into "unsure".
    """
    if post.get("video_url"):
        response = requests.get(post["video_url"], timeout=30, stream=True)
        response.raise_for_status()
        size = int(response.headers.get("Content-Length", 0))
        if 0 < size <= MAX_INLINE_MEDIA_BYTES:
            return response.content, "video/mp4"
        response.close()
        logger.info(
            "Video for post %s is %s bytes — classifying from thumbnail instead",
            post.get("shortcode"), size or "unknown",
        )

    response = requests.get(post["thumbnail_url"], timeout=30)
    response.raise_for_status()
    return response.content, "image/jpeg"


def detect_ad(client: genai.Client, post: dict) -> str:
    """Send the post's video/thumbnail + caption to Gemini to classify it.

    Returns one of "paid", "organic", "unsure". Classification is based purely on
    whether a product is deliberately featured or mentioned — not on whether a brand
    is merely visible (e.g. sponsor logos on an athlete's gear are organic).
    """
    # If the platform itself flagged it as an ad via explicitly declared paid partnership,
    # trust it immediately without hitting the LLM.
    if post.get("is_ad"):
        return "paid"

    try:
        media_bytes, mime_type = _fetch_media_bytes(post)

        prompt = f"""You are classifying an Instagram post as "paid" or "organic" content.
Analyze this {'video' if mime_type == 'video/mp4' else 'image'} and its caption:
{post.get('caption') or '(no caption)'}

Classify as "paid" ONLY if a product is deliberately featured or mentioned:
1. The person is holding up, using, or presenting a specific product as the subject of the shot.
2. The caption mentions or promotes a specific product (including discount codes, links, or
   brand @mentions that present/endorse a product).
3. The caption includes disclosure hashtags/phrases like #ad, #sponsored, #publi, #publicidad,
   #colaboración, or "paid partnership".

Classify as "organic" if no product is featured or mentioned. This includes cases where a
brand is merely VISIBLE but not the point of the post:
- An athlete or public figure wearing their professional gear/uniform (racing suit, team
  jersey, helmet) covered in sponsor logos.
- Logos, storefronts, or signage visible in the background of a lifestyle photo.
- Mentioning a venue, event, or tagging a friend/account without promoting a product.

If it is genuinely ambiguous whether a product is being deliberately promoted, classify as
"unsure" rather than guessing.

Answer with a simple JSON object matching this exact schema, with "reason" first:
{{"reason": "brief reason why", "classification": "paid" or "organic" or "unsure"}}"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=media_bytes, mime_type=mime_type),
                prompt,
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        analysis = json.loads(response.text)
        classification = analysis.get("classification", "unsure")
        if classification not in ("paid", "organic", "unsure"):
            classification = "unsure"
        logger.info(
            "Classified post %s as %s. Reason: %s",
            post.get("shortcode"), classification, analysis.get("reason"),
        )
        return classification
    except Exception:
        logger.exception("Failed to analyze post %s — marking unsure", post.get("shortcode"))
        return "unsure"


def detect_ads(posts: list[dict], known: dict[str, bool] | None = None) -> list[dict]:
    """Process a list of posts, adding/updating the `is_ad` field for each.

    Posts classified "unsure" are treated as not-ad (is_ad=False).

    A post's classification never changes, so any shortcode already present in `known`
    reuses its stored value instead of paying for another Gemini call — the daily job
    re-scrapes the same recent posts every night.
    """
    if not posts:
        return []

    known = known or {}
    client = None

    updated_posts = []
    for post in posts:
        updated_post = post.copy()
        if post["shortcode"] in known:
            updated_post["is_ad"] = known[post["shortcode"]]
        else:
            if client is None:
                client = genai.Client(api_key=config.GOOGLE_API_KEY)
            updated_post["is_ad"] = detect_ad(client, updated_post) == "paid"
        updated_posts.append(updated_post)

    return updated_posts
