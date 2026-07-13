import json
import logging
import subprocess
import time
from datetime import date, datetime, timedelta

import instaloader
import requests

from . import (
    briefing,
    config,
    content_analysis,
    db,
    instagram_scraper,
    metrics,
    recommendations,
    roster_patterns,
    trend_headlines,
    trend_scraper,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def already_ran_today() -> bool:
    if not config.LAST_RUN_FILE.exists():
        return False
    last_run = config.LAST_RUN_FILE.read_text().strip()
    return last_run == date.today().isoformat()


def mark_ran_today() -> None:
    config.LAST_RUN_FILE.write_text(date.today().isoformat())


# Bounded retry for transient connection errors during one handle's scrape.
TRANSIENT_RETRY_ATTEMPTS = 3
TRANSIENT_RETRY_BACKOFF_SECONDS = 30

# Reject a profile snapshot whose follower count moved more than this fraction
# day-over-day — a swing that large is a scrape error, not reality.
MAX_FOLLOWER_SWING = 0.5

# Session is dead — re-login required; retrying other handles is pointless.
SESSION_EXCEPTIONS = (
    instaloader.exceptions.LoginRequiredException,
    instaloader.exceptions.LoginException,
)


def _notify(title: str, message: str) -> None:
    """Post a macOS notification so failures are visible without opening logs."""
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
            check=False,
            timeout=10,
        )
    except Exception:
        logger.exception("Failed to post macOS notification")


def _scrape_with_retry(loader, handle: str) -> dict:
    """scrape_profile with bounded retry for transient connection errors.

    Session and rate-limit errors are re-raised immediately: a dead session can't
    recover by retrying, and a 429 should wait for the next launchd fire, not hammer.
    """
    for attempt in range(1, TRANSIENT_RETRY_ATTEMPTS + 1):
        try:
            return instagram_scraper.scrape_profile(loader, handle)
        except SESSION_EXCEPTIONS:
            raise
        except instaloader.exceptions.TooManyRequestsException:
            raise
        except (instaloader.exceptions.ConnectionException, requests.RequestException):
            if attempt == TRANSIENT_RETRY_ATTEMPTS:
                raise
            delay = TRANSIENT_RETRY_BACKOFF_SECONDS * attempt
            logger.warning(
                "Transient error scraping %s (attempt %d/%d) — retrying in %ds",
                handle, attempt, TRANSIENT_RETRY_ATTEMPTS, delay,
            )
            time.sleep(delay)


def _validate_profile(handle: str, profile: dict, prior_snapshots: list[dict]) -> None:
    """Reject implausible profile payloads before they reach Supabase."""
    followers = profile.get("followers")
    if not followers:
        raise ValueError(f"Rejected snapshot for {handle}: followers is {followers!r}")
    if prior_snapshots:
        previous = prior_snapshots[-1].get("followers")
        if previous and abs(followers - previous) / previous > MAX_FOLLOWER_SWING:
            raise ValueError(
                f"Rejected snapshot for {handle}: followers {previous} -> {followers} "
                f"moved more than {MAX_FOLLOWER_SWING:.0%} day-over-day"
            )


def run_instagram_scrape(client) -> list[str]:
    """Scrape every roster handle not already captured today.

    Returns the handles that failed (empty list = the day is complete).
    """
    roster = config.load_roster()
    if not roster:
        logger.warning("No influencers in %s — nothing to scrape.", config.INFLUENCERS_FILE)
        return []

    loader = instagram_scraper.build_loader()
    failed: list[str] = []
    session_dead = False

    for i, handle in enumerate(roster):
        if session_dead:
            failed.append(handle)
            continue
        try:
            influencer_id = db.get_or_create_influencer(client, handle)
            if db.profile_scraped_today(client, influencer_id):
                logger.info("Already scraped today: %s — skipping", handle)
                continue

            result = _scrape_with_retry(loader, handle)
            _validate_profile(handle, result["profile"], db.get_profile_snapshots(client, influencer_id))

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
        except SESSION_EXCEPTIONS:
            logger.exception("Instagram session expired scraping %s — aborting roster loop", handle)
            _notify(
                "You First scraper: session expired",
                f"Re-login required: instaloader --login={config.IG_USERNAME}",
            )
            failed.append(handle)
            session_dead = True
        except Exception:
            logger.exception("Failed to scrape %s — skipping", handle)
            failed.append(handle)

        if i < len(roster) - 1:
            time.sleep(config.PROFILE_REQUEST_DELAY_SECONDS)

    return failed


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


def run_trend_headlines(client) -> None:
    # Over-fetch, then keep the newest snapshot per source: the latest N rows overall
    # can hold duplicates of one source (and miss another) when a source fails a day.
    rows = db.get_latest_trend_snapshots(client, limit=len(config.TREND_SOURCES) * 7)
    latest_by_source: dict[str, dict] = {}
    for row in rows:
        latest_by_source.setdefault(row["source_url"], row)
    snapshots = list(latest_by_source.values())
    if not snapshots:
        logger.info("No trend snapshots — skipping headlines")
        return
    try:
        content = trend_headlines.generate_headlines(snapshots)
        if content is None:
            logger.warning("No valid trend headlines generated — keeping previous")
            return
        db.insert_trend_headlines(client, trend_headlines.GEMINI_MODEL, content)
        logger.info("Generated trend headlines")
    except Exception:
        logger.exception("Failed to generate trend headlines — keeping previous")


def _latest_trend_texts(client) -> list[str] | None:
    """English texts of the latest stored trend headlines, or None if absent/stale/invalid."""
    try:
        row = db.get_latest_trend_headlines(client)
    except Exception:
        logger.exception("Failed to fetch trend headlines — recommendations proceed without trends")
        return None
    if not row:
        return None
    try:
        # The prompt presents these as today's trends; a row kept from a failed
        # generation day must not be passed off as fresh.
        generated_at = datetime.fromisoformat(row["generated_at"])
        if datetime.now(generated_at.tzinfo) - generated_at > timedelta(hours=24):
            logger.warning("Latest trend headlines are stale — recommendations proceed without trends")
            return None
        headlines = json.loads(row["content"])["headlines"]
        texts = [h["text"]["en"] for h in headlines]
        return texts or None
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def run_recommendations(client) -> None:
    trend_items = _latest_trend_texts(client)
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
                trend_items,
            )
            if content is None:
                logger.warning("No valid recommendation generated for %s — keeping previous", handle)
                continue
            db.insert_recommendation(client, influencer["id"], recommendations.GEMINI_MODEL, content)
            logger.info("Generated recommendation for %s", handle)
        except Exception:
            logger.exception("Failed to generate recommendation for %s — skipping", handle)


def _first_recommendation_text(content: str | None) -> str | None:
    """Pull the first bullet's English text out of a stored recommendation JSON string."""
    if not content:
        return None
    try:
        bullets = json.loads(content)["bullets"]
        return bullets[0]["text"]["en"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None


def run_roster_briefing(client) -> None:
    influencers = db.list_influencers(client)
    if not influencers:
        logger.info("No influencers — skipping roster briefing")
        return

    try:
        profile_snapshots_by_id = {}
        post_snapshots_by_id = {}
        content_map_by_id = {}
        recommendations_by_handle = {}

        for influencer in influencers:
            influencer_id = influencer["id"]
            profile_snapshots_by_id[influencer_id] = db.get_profile_snapshots(client, influencer_id)
            post_snapshots_by_id[influencer_id] = db.get_all_post_snapshots(client, influencer_id)
            content_map_by_id[influencer_id] = db.get_post_content_map(client, influencer_id)

            latest_recommendation = db.get_latest_recommendation(client, influencer_id)
            text = _first_recommendation_text(latest_recommendation["content"] if latest_recommendation else None)
            if text:
                recommendations_by_handle[influencer["handle"]] = text

        pattern_facts = roster_patterns.compute_roster_patterns(
            influencers, profile_snapshots_by_id, post_snapshots_by_id, content_map_by_id
        )

        content = briefing.generate_briefing(pattern_facts, recommendations_by_handle)
        if content is None:
            logger.warning("No valid roster briefing generated — keeping previous")
            return

        db.insert_roster_briefing(client, briefing.GEMINI_MODEL, content)
        logger.info("Generated roster briefing")
    except Exception:
        logger.exception("Failed to generate roster briefing — keeping previous")


def main() -> None:
    if already_ran_today():
        logger.info("Already ran today (%s) — skipping.", date.today().isoformat())
        return

    client = db.get_client()
    failed_handles = run_instagram_scrape(client)
    run_trend_scrape(client)
    run_trend_headlines(client)
    run_recommendations(client)
    run_roster_briefing(client)
    if failed_handles:
        # Leave .last_run unwritten so a later launchd fire retries the missed
        # handles today (already-scraped handles are skipped per-handle).
        logger.error(
            "Daily run INCOMPLETE — missing handles: %s (will retry on next scheduled fire)",
            ", ".join(failed_handles),
        )
        _notify(
            "You First scraper: run incomplete",
            f"Missing: {', '.join(failed_handles)}",
        )
    else:
        mark_ran_today()
        logger.info("Daily run complete at %s", datetime.now().isoformat())


if __name__ == "__main__":
    main()
