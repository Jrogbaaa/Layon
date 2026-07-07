import logging
import time
from datetime import date, datetime

import requests

from . import config, content_analysis, db, instagram_scraper, metrics, recommendations, trend_scraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def already_ran_today() -> bool:
    if not config.LAST_RUN_FILE.exists():
        return False
    last_run = config.LAST_RUN_FILE.read_text().strip()
    return last_run == date.today().isoformat()


def mark_ran_today() -> None:
    config.LAST_RUN_FILE.write_text(date.today().isoformat())


def run_instagram_scrape(client) -> None:
    roster = config.load_roster()
    if not roster:
        logger.warning("No influencers in %s — nothing to scrape.", config.INFLUENCERS_FILE)
        return

    loader = instagram_scraper.build_loader()

    for i, handle in enumerate(roster):
        try:
            result = instagram_scraper.scrape_profile(loader, handle)
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
            db.insert_post_snapshots(client, influencer_id, result["posts"])

            already_analyzed = db.get_analyzed_shortcodes(client, influencer_id)
            analyzed = content_analysis.analyze_posts(result["posts"], already_analyzed)
            db.insert_post_content(client, influencer_id, analyzed)

            profile_snapshots = db.get_profile_snapshots(client, influencer_id)
            post_snapshots = db.get_all_post_snapshots(client, influencer_id)
            highlights = metrics.compute_highlights(handle, profile_snapshots, post_snapshots)
            db.insert_highlights(client, influencer_id, highlights)

            logger.info(
                "Scraped %s: %d posts, %d analyzed, %d highlights",
                handle,
                len(result["posts"]),
                len(analyzed),
                len(highlights),
            )
        except Exception:
            logger.exception("Failed to scrape %s — skipping", handle)

        if i < len(roster) - 1:
            time.sleep(config.PROFILE_REQUEST_DELAY_SECONDS)


def run_trend_scrape(client) -> None:
    for url in config.TREND_SOURCES:
        try:
            if db.trend_source_scraped_today(client, url):
                logger.info("Trend source already scraped today: %s", url)
                continue
            result = trend_scraper.scrape_trend_source(url)
            db.insert_trend_snapshot(client, url, result["title"], result["content_text"])
            logger.info("Scraped trend source: %s", url)
        except Exception:
            logger.exception("Failed to scrape trend source %s — skipping", url)


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
            content = recommendations.generate_recommendation(
                handle,
                profile_snapshots,
                posts,
                influencer.get("persona"),
                highlights,
                content_map,
            )
            db.insert_recommendation(client, influencer["id"], recommendations.GEMINI_MODEL, content)
            logger.info("Generated recommendation for %s", handle)
        except Exception:
            logger.exception("Failed to generate recommendation for %s — skipping", handle)


def main() -> None:
    if already_ran_today():
        logger.info("Already ran today (%s) — skipping.", date.today().isoformat())
        return

    client = db.get_client()
    run_instagram_scrape(client)
    run_trend_scrape(client)
    run_recommendations(client)
    mark_ran_today()
    logger.info("Daily run complete at %s", datetime.now().isoformat())


if __name__ == "__main__":
    main()
