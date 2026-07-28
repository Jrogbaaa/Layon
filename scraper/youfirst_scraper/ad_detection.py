import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

import requests
from google import genai
from google.genai import types

from . import config

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
CLASSIFIER_VERSION = "brand-evidence-v1"

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


def _fetch_media_parts(post: dict) -> list[dict[str, Any]]:
    assets = post.get("media_assets") or []
    if not assets:
        return [{"kind": "image", "mime_type": "image/jpeg", "url": post["thumbnail_url"]}]
    return [asset for asset in assets if asset.get("url")]


def _normalize_usernames(values: Any) -> list[str]:
    if not values:
        return []
    usernames: list[str] = []
    for value in values:
        if isinstance(value, str):
            username = value.strip().lstrip("@").lower()
        elif isinstance(value, dict):
            username = str(value.get("username") or value.get("user") or value.get("name") or "").strip().lstrip("@").lower()
        else:
            username = str(getattr(value, "username", "")).strip().lstrip("@").lower()
        if username and username not in usernames:
            usernames.append(username)
    return usernames


def _profile_context(loader, username: str) -> dict[str, Any]:
    try:
        import instaloader

        profile = instaloader.Profile.from_username(loader.context, username)
    except Exception:
        return {"username": username, "lookup_status": "unavailable"}

    return {
        "username": username,
        "full_name": getattr(profile, "full_name", None),
        "biography": getattr(profile, "biography", None),
        "is_business_account": getattr(profile, "is_business_account", None),
        "business_category_name": getattr(profile, "business_category_name", None),
        "lookup_status": "ok",
    }


def _hash_classification_inputs(post: dict, profile_contexts: list[dict[str, Any]]) -> str:
    payload = {
        "caption": post.get("caption"),
        "instagram_paid_partnership": bool(post.get("is_ad")),
        "caption_mentions": _normalize_usernames(post.get("caption_mentions")),
        "tagged_users": _normalize_usernames(post.get("tagged_users")),
        "sponsor_users": _normalize_usernames(post.get("sponsor_users")),
        "media_assets": [asset.get("url") for asset in _fetch_media_parts(post)],
        "profile_contexts": sorted(profile_contexts, key=lambda item: item.get("username", "")),
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _extract_facts(client: genai.Client, post: dict, profile_contexts: list[dict[str, Any]]) -> dict[str, Any]:
    media_parts = _fetch_media_parts(post)
    contents = []
    for asset in media_parts[:4]:
        try:
            response = requests.get(asset["url"], timeout=30)
            response.raise_for_status()
            contents.append(types.Part.from_bytes(data=response.content, mime_type=asset["mime_type"]))
        except Exception:
            logger.exception("Failed to fetch media asset for %s", post.get("shortcode"))

    prompt = f"""You are extracting paid-media evidence from an Instagram post.

Post caption:
{post.get('caption') or '(no caption)'}

Caption mentions:
{', '.join(_normalize_usernames(post.get('caption_mentions'))) or '(none)'}

Tagged accounts:
{json.dumps(profile_contexts, ensure_ascii=False)}

Sponsor accounts:
{', '.join(_normalize_usernames(post.get('sponsor_users'))) or '(none)'}

Rules:
- A post is paid if it clearly promotes a brand, product, paid partnership, or disclosure.
- A post is organic if the tags/mentions are people only and any brands in the image are incidental.
- If you cannot tell whether a tagged account is a person or a brand, mark that account unknown.
- Only call a visual brand central if the branded item is the subject of the post, not a background logo or natural sponsor-marked clothing.

Return JSON with this exact schema:
{{
  "summary": "brief plain-language note",
  "caption_brand_mentions": [{{"text": "brand or product mention", "reason": "why it matters"}}],
  "tagged_accounts": [{{"username": "handle", "account_type": "person|commercial_brand|noncommercial_org|unknown", "reason": "why"}}],
  "visual_brand_mentions": [{{"name": "brand or product", "prominence": "central|incidental|unknown", "reason": "why"}}],
  "disclosure_terms": ["#ad", "#sponsored"],
  "uncertain": false
}}"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents + [prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)


def _decide_classification(post: dict, facts: dict[str, Any]) -> dict[str, Any]:
    disclosure_terms = [term for term in facts.get("disclosure_terms", []) if term]
    caption_brand_mentions = facts.get("caption_brand_mentions", [])
    tagged_accounts = facts.get("tagged_accounts", [])
    visual_brand_mentions = facts.get("visual_brand_mentions", [])
    uncertain = bool(facts.get("uncertain"))

    brand_tagged = any(account.get("account_type") in {"commercial_brand", "noncommercial_org"} for account in tagged_accounts)
    unknown_tagged = any(account.get("account_type") == "unknown" for account in tagged_accounts)
    central_visual_brand = any(item.get("prominence") == "central" for item in visual_brand_mentions)
    incidental_visual_brand = any(item.get("prominence") == "incidental" for item in visual_brand_mentions)

    if post.get("is_ad"):
        status = "paid"
        decision_code = "instagram_paid_partnership"
    elif disclosure_terms:
        status = "paid"
        decision_code = "caption_disclosure"
    elif caption_brand_mentions:
        status = "paid"
        decision_code = "caption_brand_mention"
    elif brand_tagged:
        status = "paid"
        decision_code = "brand_tagged_account"
    elif central_visual_brand:
        status = "paid"
        decision_code = "visual_brand_central"
    elif uncertain or unknown_tagged:
        status = "needs_review"
        decision_code = "ambiguous"
    else:
        status = "organic"
        decision_code = "people_only_or_incidental_brand"

    evidence = {
        "caption_mentions": _normalize_usernames(post.get("caption_mentions")),
        "tagged_users": _normalize_usernames(post.get("tagged_users")),
        "sponsor_users": _normalize_usernames(post.get("sponsor_users")),
        "caption_brand_mentions": caption_brand_mentions,
        "tagged_accounts": tagged_accounts,
        "visual_brand_mentions": visual_brand_mentions,
        "disclosure_terms": disclosure_terms,
        "incidental_visual_brand": incidental_visual_brand,
        "summary": facts.get("summary"),
    }

    return {
        "status": status,
        "decision_code": decision_code,
        "evidence": evidence,
        "classifier_version": CLASSIFIER_VERSION,
        "input_hash": facts.get("input_hash"),
        "classified_at": datetime.now(timezone.utc).isoformat(),
    }


def classify_post(client: genai.Client, post: dict, loader=None, profile_contexts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if profile_contexts is None:
        profile_contexts = []
    if loader is not None and not profile_contexts:
        account_usernames = sorted(
            set(_normalize_usernames(post.get("caption_mentions")) + _normalize_usernames(post.get("tagged_users")))
        )
        for username in account_usernames:
            try:
                profile_contexts.append(_profile_context(loader, username))
            except Exception:
                logger.exception("Failed to inspect tagged account %s on %s", username, post.get("shortcode"))

    input_hash = _hash_classification_inputs(post, profile_contexts)

    if post.get("is_ad"):
        return {
            "status": "paid",
            "decision_code": "instagram_paid_partnership",
            "evidence": {
                "caption_mentions": _normalize_usernames(post.get("caption_mentions")),
                "tagged_users": _normalize_usernames(post.get("tagged_users")),
                "sponsor_users": _normalize_usernames(post.get("sponsor_users")),
                "caption_brand_mentions": [],
                "tagged_accounts": [],
                "visual_brand_mentions": [],
                "disclosure_terms": [],
                "summary": "Instagram marked this post as a paid partnership.",
            },
            "classifier_version": CLASSIFIER_VERSION,
            "input_hash": input_hash,
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }

    facts = _extract_facts(client, post, profile_contexts)
    facts["input_hash"] = input_hash
    return _decide_classification(post, facts)


def classify_posts(posts: list[dict], client: genai.Client, loader=None, known: dict[str, dict[str, Any]] | None = None) -> list[dict]:
    if not posts:
        return []

    known = known or {}
    updated_posts = []
    for post in posts:
        updated_post = post.copy()
        cached = known.get(post["shortcode"])
        profile_contexts = []
        if loader is not None:
            account_usernames = sorted(
                set(_normalize_usernames(post.get("caption_mentions")) + _normalize_usernames(post.get("tagged_users")))
            )
            for username in account_usernames:
                try:
                    profile_contexts.append(_profile_context(loader, username))
                except Exception:
                    logger.exception("Failed to inspect tagged account %s on %s", username, post.get("shortcode"))

        input_hash = _hash_classification_inputs(post, profile_contexts)
        if post.get("is_ad"):
            # Instagram's current paid-partnership signal is authoritative and must
            # never be overridden by an older cached organic classification.
            classification = classify_post(client, updated_post, loader=loader, profile_contexts=profile_contexts)
        elif cached and cached.get("classifier_version") == CLASSIFIER_VERSION and cached.get("input_hash") == input_hash:
            classification = cached
        else:
            classification = classify_post(client, updated_post, loader=loader, profile_contexts=profile_contexts)
            classification["input_hash"] = input_hash

        updated_post["classification"] = classification
        updated_post["is_ad"] = classification["status"] == "paid"
        updated_posts.append(updated_post)

    return updated_posts


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
