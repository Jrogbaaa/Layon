import logging

import instaloader

from . import config

logger = logging.getLogger(__name__)


def build_loader() -> instaloader.Instaloader:
    """Build an Instaloader instance, authenticated if IG_USERNAME has a saved session.

    Anonymous (not-logged-in) requests are aggressively blocked by Instagram, so a
    logged-in session is strongly recommended. Create one by logging into instagram.com
    in Chrome, then running:
        instaloader --load-cookies Chrome
    which imports the browser's trusted session and saves a reusable session file.
    Avoid `instaloader --login=<IG_USERNAME>`: Instagram checkpoint-blocks that login
    endpoint for this account (learned 2026-07-15), and each retry re-arms the block.
    This codebase never handles the password directly either way.
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
                "No saved session for IG_USERNAME=%s — log into instagram.com in Chrome, "
                "then run `instaloader --load-cookies Chrome` once. "
                "Proceeding anonymously, which Instagram is likely to block.",
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


def _comment_count(post: instaloader.Post) -> int:
    """Read the comment count from the timeline edge data directly.

    Instaloader's post.comments property expects edge_media_to_parent_comment,
    which isn't present on this endpoint's response shape, so it falls back to a
    per-post metadata fetch that currently fails upstream. The timeline edge
    already carries the count under a plain "comments" key.

    A missing key means Instagram changed the response shape — that must fail
    the scrape, not silently record 0 comments for every post.
    """
    if "comments" not in post._node:
        raise KeyError(
            f"'comments' key missing from timeline node for post {post.shortcode} — "
            "Instagram response shape may have changed"
        )
    return post._node["comments"]


def _view_count(post: instaloader.Post) -> int | None:
    """Return video/reel view count from timeline edge data when available."""
    if not post.is_video:
        return None
    node = post._node
    for key in ("video_view_count", "play_count", "view_count"):
        value = node.get(key)
        if isinstance(value, int):
            return value
    logger.warning(
        "No view-count key on video post %s — Instagram response shape may have changed",
        post.shortcode,
    )
    return None


def _is_sponsored(post: instaloader.Post) -> bool:
    try:
        return post.is_sponsored
    except Exception:
        return False


def scrape_profile(
    loader: instaloader.Instaloader, handle: str, post_limit: int | None = None
) -> dict:
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
        "avatar_source_url": profile.profile_pic_url,
    }

    limit = post_limit if post_limit is not None else config.POSTS_PER_INFLUENCER

    posts = []
    for post in profile.get_posts():
        posts.append(
            {
                "shortcode": post.shortcode,
                "post_type": _post_type(post),
                "likes": post.likes,
                "comments": _comment_count(post),
                "views": _view_count(post),
                "caption": post.caption,
                "posted_at": post.date_utc.isoformat() + "Z",
                "video_url": post.video_url if post.is_video else None,
                "thumbnail_url": post.url,
                "is_ad": _is_sponsored(post),
            }
        )
        if len(posts) >= limit:
            break

    return {"profile": profile_data, "posts": posts}
