import logging
import time

import requests

from . import ad_detection, config, db, instagram_scraper, metrics, recommendations

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BACKFILL_POSTS_PER_INFLUENCER = 50


def run_backfill_scrape(client) -> None:
    roster = config.load_roster()
    if not roster:
        logger.warning("No influencers in %s — nothing to backfill.", config.INFLUENCERS_FILE)
        return

    loader = instagram_scraper.build_loader()

    for i, handle in enumerate(roster):
        try:
            result = instagram_scraper.scrape_profile(
                loader, handle, post_limit=BACKFILL_POSTS_PER_INFLUENCER
            )
            influencer_id = db.get_or_create_influencer(client, handle)

            avatar_source_url = result["profile"].get("avatar_source_url")
            if avatar_source_url:
                try:
                    response = requests.get(avatar_source_url, timeout=10)
                    response.raise_for_status()
                    avatar_url = db.upload_avatar(client, handle, response.content)
                    db.update_influencer_avatar(client, influencer_id, avatar_url)
                except Exception:
                    logger.exception("Failed to update avatar for %s — continuing", handle)

            db.insert_profile_snapshot(client, influencer_id, result["profile"])
            result["posts"] = ad_detection.detect_ads(result["posts"])
            db.insert_post_snapshots(client, influencer_id, result["posts"])

            profile_snapshots = db.get_profile_snapshots(client, influencer_id)
            post_snapshots = db.get_all_post_snapshots(client, influencer_id)
            highlights = metrics.compute_highlights(handle, profile_snapshots, post_snapshots)
            db.insert_highlights(client, influencer_id, highlights)

            logger.info(
                "Backfilled %s: %d posts, %d highlights",
                handle,
                len(result["posts"]),
                len(highlights),
            )
        except Exception:
            logger.exception("Failed to backfill %s — skipping", handle)

        if i < len(roster) - 1:
            time.sleep(config.PROFILE_REQUEST_DELAY_SECONDS * 3)


def run_recommendations(client) -> None:
    for influencer in db.list_influencers(client):
        handle = influencer["handle"]
        try:
            profile_snapshots = db.get_profile_snapshots(client, influencer["id"])
            if not profile_snapshots:
                logger.info("No profile history yet for %s — skipping recommendation", handle)
                continue
            posts = db.get_recent_posts(client, influencer["id"])
            highlights = db.get_latest_highlights(client, influencer["id"])
            content_map = db.get_post_content_map(client, influencer["id"])
            alltime_top_posts = db.get_top_posts(client, influencer["id"])
            content = recommendations.generate_recommendation(
                handle,
                profile_snapshots,
                posts,
                influencer.get("persona"),
                highlights,
                content_map,
                alltime_top_posts,
            )
            db.insert_recommendation(client, influencer["id"], recommendations.GEMINI_MODEL, content)
            logger.info("Generated recommendation for %s", handle)
        except Exception:
            logger.exception("Failed to generate recommendation for %s — skipping", handle)


def main() -> None:
    client = db.get_client()
    run_backfill_scrape(client)
    run_recommendations(client)
    logger.info("Backfill complete.")


if __name__ == "__main__":
    main()
