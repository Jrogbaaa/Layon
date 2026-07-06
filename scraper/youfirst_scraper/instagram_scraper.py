import logging

import instaloader

from . import config

logger = logging.getLogger(__name__)


def build_loader() -> instaloader.Instaloader:
    """Build an Instaloader instance, authenticated if IG_USERNAME has a saved session.

    Anonymous (not-logged-in) requests are aggressively blocked by Instagram, so a
    logged-in session is strongly recommended. Create one once via:
        instaloader --login=<IG_USERNAME>
    which prompts for the password interactively and saves a reusable session file —
    this codebase never handles the password directly.
    """
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        save_metadata=False,
        compress_json=False,
    )

    if config.IG_USERNAME:
        try:
            loader.load_session_from_file(config.IG_USERNAME)
            logger.info("Loaded Instagram session for %s", config.IG_USERNAME)
        except FileNotFoundError:
            logger.warning(
                "No saved session for IG_USERNAME=%s — run `instaloader --login=%s` once. "
                "Proceeding anonymously, which Instagram is likely to block.",
                config.IG_USERNAME,
                config.IG_USERNAME,
            )
    else:
        logger.warning("IG_USERNAME not set — scraping anonymously, which Instagram is likely to block.")

    return loader


def _post_type(post: instaloader.Post) -> str:
    if post.is_video:
        return "reel" if post.typename == "GraphVideo" else "video"
    if post.typename == "GraphSidecar":
        return "carousel"
    return "photo"


def scrape_profile(loader: instaloader.Instaloader, handle: str) -> dict:
    """Fetch profile stats and recent posts for one handle.

    Raises whatever instaloader raises on failure (e.g. ProfileNotExistsException,
    ConnectionException) — the caller is responsible for catching and skipping.
    """
    profile = instaloader.Profile.from_username(loader.context, handle)

    profile_data = {
        "followers": profile.followers,
        "following": profile.followees,
        "media_count": profile.mediacount,
        "bio": profile.biography,
    }

    posts = []
    for post in profile.get_posts():
        posts.append(
            {
                "shortcode": post.shortcode,
                "post_type": _post_type(post),
                "likes": post.likes,
                "comments": post.comments,
                "caption": post.caption,
                "posted_at": post.date_utc.isoformat() + "Z",
            }
        )
        if len(posts) >= config.POSTS_PER_INFLUENCER:
            break

    return {"profile": profile_data, "posts": posts}
