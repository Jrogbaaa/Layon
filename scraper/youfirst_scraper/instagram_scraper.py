import logging

import instaloader

from . import config

logger = logging.getLogger(__name__)


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
