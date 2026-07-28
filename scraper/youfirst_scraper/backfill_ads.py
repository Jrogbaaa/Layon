import logging
from datetime import datetime, timezone
import hashlib
import json

import instaloader

from . import ad_detection, db, instagram_scraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

POST_SNAPSHOT_PAGE_SIZE = 1000


def _media_urls_by_shortcode(loader, handle: str, needed: set[str]) -> dict[str, dict]:
    """post_snapshots never stores media URLs, so walk the influencer's recent posts
    (the same proven path the daily job uses) to recover them for retroactive
    classification. Per-post shortcode lookups (tried first) get blocked by Instagram
    as suspicious. Stops as soon as every needed shortcode is found — the DB only holds
    each influencer's most recent posts, so this keeps Instagram traffic minimal."""
    profile = instaloader.Profile.from_username(loader.context, handle)
    found: dict[str, dict] = {}
    checked = 0
    for post in profile.get_posts():
        checked += 1
        if post.shortcode in needed:
            found[post.shortcode] = instagram_scraper.build_post_record(post)
            if len(found) == len(needed):
                break
        # Safety cap: don't page deep into profile history for shortcodes that may
        # have been deleted from Instagram.
        if checked >= len(needed) + 50:
            break
    return found


def _dedupe_posts(rows: list[dict]) -> list[dict]:
    """post_snapshots holds one row per daily capture, so dedupe to unique posts —
    the is_ad update below applies to every snapshot row of a shortcode anyway."""
    return list({(row["influencer_id"], row["shortcode"]): row for row in rows}.values())


def _fetch_post_snapshot_page(
    client,
    active_influencer_ids: list[int],
    start: int,
    page_size: int = POST_SNAPSHOT_PAGE_SIZE,
) -> list[dict]:
    result = (
        client.table("post_snapshots")
        .select("id, shortcode, influencer_id, caption, is_ad")
        .in_("influencer_id", active_influencer_ids)
        .order("id")
        .range(start, start + page_size - 1)
        .execute()
    )
    return result.data


def _load_posts_to_backfill(
    client,
    active_influencer_ids: list[int],
    page_size: int = POST_SNAPSHOT_PAGE_SIZE,
) -> list[dict]:
    rows: list[dict] = []
    start = 0
    while True:
        page = _fetch_post_snapshot_page(client, active_influencer_ids, start, page_size)
        rows.extend(page)
        if len(page) < page_size:
            break
        start += page_size
    return _dedupe_posts(rows)


def _update_snapshot_classification(client, influencer_id: int, shortcode: str, status: str) -> None:
    (
        client.table("post_snapshots")
        .update({"is_ad": status == "paid"})
        .eq("influencer_id", influencer_id)
        .eq("shortcode", shortcode)
        .execute()
    )


def main() -> None:
    client = db.get_client()
    loader = instagram_scraper.build_loader()
    genai_client = ad_detection.genai.Client(api_key=ad_detection.config.GOOGLE_API_KEY)

    influencers = db.list_influencers(client)
    active_influencer_ids = [influencer["id"] for influencer in influencers]
    if not active_influencer_ids:
        logger.info("No active influencers — nothing to backfill.")
        return

    # Re-check every post; the previous prompt was too aggressive so stored is_ad
    # values are not trustworthy and must be re-derived.
    logger.info("Fetching all posts to classify...")
    posts_to_check = _load_posts_to_backfill(client, active_influencer_ids)

    logger.info("Found %d posts to analyze via Gemini.", len(posts_to_check))
    paid, organic, needs_review = [], [], []
    media_cache: dict[int, dict[str, dict]] = {}
    classification_cache: dict[int, dict[str, dict]] = {}
    classified_by_influencer: dict[int, list[dict]] = {}

    for i, post in enumerate(posts_to_check):
        logger.info("Analyzing post %d/%d (shortcode: %s)", i + 1, len(posts_to_check), post["shortcode"])

        influencer_id = post["influencer_id"]
        if influencer_id not in media_cache:
            handle = next((inf["handle"] for inf in influencers if inf["id"] == influencer_id), None)
            needed = {p["shortcode"] for p in posts_to_check if p["influencer_id"] == influencer_id}
            try:
                media_cache[influencer_id] = _media_urls_by_shortcode(loader, handle, needed) if handle else {}
            except Exception:
                logger.exception(
                    "Failed to scrape profile for influencer %s — its posts will need review",
                    influencer_id,
                )
                media_cache[influencer_id] = {}

        if influencer_id not in classification_cache:
            classification_cache[influencer_id] = db.get_post_classifications(client, influencer_id)

        media_record = media_cache[influencer_id].get(post["shortcode"])
        if media_record is None:
            logger.warning(
                "No media found for post %s (not in recent profile posts) — marking needs review",
                post["shortcode"],
            )
            classification = {
                "status": "needs_review",
                "decision_code": "media_missing",
                "evidence": {
                    "caption_mentions": [],
                    "tagged_users": [],
                    "sponsor_users": [],
                    "caption_brand_mentions": [],
                    "tagged_accounts": [],
                    "visual_brand_mentions": [],
                    "disclosure_terms": [],
                    "summary": "The post could not be re-located in the profile scrape, so it needs manual review.",
                },
                "classifier_version": ad_detection.CLASSIFIER_VERSION,
                "input_hash": hashlib.sha256(json.dumps(post, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
                "classified_at": datetime.now(timezone.utc).isoformat(),
            }
            updated_post = {**post, "is_ad": False, "classification": classification}
        else:
            # media_record comes from the live Instagram scrape, so its is_ad value
            # is Instagram's current paid-partnership flag, not the stale DB boolean.
            post_to_check = media_record
            classified_post = ad_detection.classify_posts(
                [post_to_check],
                genai_client,
                loader=loader,
                known=classification_cache[influencer_id],
            )[0]
            classification = classified_post["classification"]
            updated_post = classified_post

        classified_by_influencer.setdefault(influencer_id, []).append(updated_post)
        classification_cache[influencer_id][post["shortcode"]] = classification

        if classification["status"] == "paid":
            paid.append(post)
        elif classification["status"] == "organic":
            organic.append(post)
        else:
            needs_review.append(post)

        _update_snapshot_classification(
            client,
            influencer_id,
            post["shortcode"],
            classification["status"],
        )

    logger.info("--- BACKFILL COMPLETE ---")
    logger.info("Paid: %d, Organic: %d, Needs review: %d", len(paid), len(organic), len(needs_review))

    by_influencer: dict[str, dict[str, int]] = {}
    for post, key in [(p, "paid") for p in paid] + [(p, "organic") for p in organic] + [(p, "needs_review") for p in needs_review]:
        counts = by_influencer.setdefault(post["influencer_id"], {"paid": 0, "organic": 0, "needs_review": 0})
        counts[key] += 1
    for influencer_id, counts in by_influencer.items():
        logger.info(
            " - %s: paid=%d organic=%d needs_review=%d",
            influencer_id,
            counts["paid"],
            counts["organic"],
            counts["needs_review"],
        )

    for influencer_id, posts in classified_by_influencer.items():
        db.upsert_post_classifications(client, influencer_id, posts)

    if needs_review:
        logger.info("--- POSTS NEEDING MANUAL REVIEW (%d) ---", len(needs_review))
        for p in needs_review:
            logger.info(
                " - %s: https://www.instagram.com/p/%s/ (influencer: %s)",
                p["shortcode"], p["shortcode"], p["influencer_id"],
            )


if __name__ == "__main__":
    main()
