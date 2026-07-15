import logging

import instaloader

from . import ad_detection, db, instagram_scraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


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
            found[post.shortcode] = {
                "video_url": post.video_url if post.is_video else None,
                "thumbnail_url": post.url,
            }
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


def main() -> None:
    client = db.get_client()
    loader = instagram_scraper.build_loader()

    influencers = db.list_influencers(client)

    # Re-check every post; the previous prompt was too aggressive so stored is_ad
    # values are not trustworthy and must be re-derived.
    logger.info("Fetching all posts to classify...")
    result = client.table("post_snapshots").select(
        "shortcode, influencer_id, caption, is_ad"
    ).execute()
    posts_to_check = _dedupe_posts(result.data)

    logger.info("Found %d posts to analyze via Gemini.", len(posts_to_check))

    genai_client = ad_detection.genai.Client(api_key=ad_detection.config.GOOGLE_API_KEY)

    paid, organic, unsure = [], [], []
    media_cache: dict[int, dict[str, dict]] = {}

    for i, post in enumerate(posts_to_check):
        logger.info("Analyzing post %d/%d (shortcode: %s)", i + 1, len(posts_to_check), post["shortcode"])

        influencer_id = post["influencer_id"]
        if influencer_id not in media_cache:
            handle = next((inf["handle"] for inf in influencers if inf["id"] == influencer_id), None)
            needed = {p["shortcode"] for p in posts_to_check if p["influencer_id"] == influencer_id}
            try:
                media_cache[influencer_id] = _media_urls_by_shortcode(loader, handle, needed) if handle else {}
            except Exception:
                logger.exception("Failed to scrape profile for influencer %s — its posts will be unsure", influencer_id)
                media_cache[influencer_id] = {}

        media_urls = media_cache[influencer_id].get(post["shortcode"])
        if media_urls is None:
            logger.warning("No media found for post %s (not in recent profile posts) — marking unsure", post["shortcode"])
            unsure.append(post)
            # Unsure always means is_ad=False for now, same as a classified-unsure post
            # below — never leave a stale (possibly wrong) value sitting unreviewed.
            client.table("post_snapshots").update({"is_ad": False}).eq("shortcode", post["shortcode"]).execute()
            continue

        # Don't let the stale is_ad value short-circuit detect_ad's early return.
        post_to_check = {**post, **media_urls, "is_ad": False}
        classification = ad_detection.detect_ad(genai_client, post_to_check)

        if classification == "paid":
            paid.append(post)
        elif classification == "organic":
            organic.append(post)
        else:
            unsure.append(post)

        # Unconditional write: snapshot rows of the same shortcode can disagree on
        # is_ad, so comparing against the one deduped row could skip needed updates.
        new_is_ad = classification == "paid"
        client.table("post_snapshots").update({"is_ad": new_is_ad}).eq("shortcode", post["shortcode"]).execute()

    logger.info("--- BACKFILL COMPLETE ---")
    logger.info("Paid: %d, Organic: %d, Unsure: %d", len(paid), len(organic), len(unsure))

    by_influencer: dict[str, dict[str, int]] = {}
    for post, key in [(p, "paid") for p in paid] + [(p, "organic") for p in organic] + [(p, "unsure") for p in unsure]:
        counts = by_influencer.setdefault(post["influencer_id"], {"paid": 0, "organic": 0, "unsure": 0})
        counts[key] += 1
    for influencer_id, counts in by_influencer.items():
        logger.info(" - %s: paid=%d organic=%d unsure=%d", influencer_id, counts["paid"], counts["organic"], counts["unsure"])

    if unsure:
        logger.info("--- POSTS NEEDING MANUAL REVIEW (%d) ---", len(unsure))
        for p in unsure:
            logger.info(
                " - %s: https://www.instagram.com/p/%s/ (influencer: %s)",
                p["shortcode"], p["shortcode"], p["influencer_id"],
            )


if __name__ == "__main__":
    main()
