import logging
import re

import instaloader

from . import config

logger = logging.getLogger(__name__)

CAPTION_MENTION_RE = re.compile(r"(?<![\w.])@([A-Za-z0-9._]+)")


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
    iphone_struct = _iphone_struct(post)
    if "is_paid_partnership" in iphone_struct:
        return bool(iphone_struct["is_paid_partnership"])
    try:
        return post.is_sponsored
    except Exception:
        return False


def _iphone_struct(post: instaloader.Post) -> dict:
    node = getattr(post, "_node", {})
    if not isinstance(node, dict):
        return {}
    iphone_struct = node.get("iphone_struct")
    return iphone_struct if isinstance(iphone_struct, dict) else {}


def _caption_mentions(post: instaloader.Post) -> list[str]:
    mentions: list[str] = []
    caption = post.caption or ""
    for username in CAPTION_MENTION_RE.findall(caption):
        username = username.lower()
        if username not in mentions:
            mentions.append(username)
    try:
        extracted = post.caption_mentions
    except Exception:
        extracted = []
    for username in extracted:
        username = username.lower()
        if username not in mentions:
            mentions.append(username)
    return mentions


def _tagged_usernames(post: instaloader.Post) -> list[str]:
    iphone_struct = _iphone_struct(post)
    if "usertags" in iphone_struct:
        usernames = []
        for tag in (iphone_struct.get("usertags") or {}).get("in", []):
            username = str((tag.get("user") or {}).get("username") or "").lower()
            if username and username not in usernames:
                usernames.append(username)
        return usernames
    try:
        return list(dict.fromkeys(username.lower() for username in post.tagged_users))
    except Exception:
        return []


def _sponsor_usernames(post: instaloader.Post) -> list[str]:
    iphone_struct = _iphone_struct(post)
    if "sponsor_tags" in iphone_struct:
        usernames = []
        for tag in iphone_struct.get("sponsor_tags") or []:
            username = str((tag.get("sponsor") or {}).get("username") or "").lower()
            if username and username not in usernames:
                usernames.append(username)
        return usernames
    try:
        return [profile.username.lower() for profile in post.sponsor_users]
    except Exception:
        return []


def _media_assets(post: instaloader.Post) -> list[dict[str, str]]:
    assets: list[dict[str, str]] = []
    try:
        if post.typename == "GraphSidecar":
            for node in post.get_sidecar_nodes():
                url = node.video_url if node.is_video else node.display_url
                if url:
                    assets.append(
                        {
                            "kind": "video" if node.is_video else "image",
                            "mime_type": "video/mp4" if node.is_video else "image/jpeg",
                            "url": url,
                        }
                    )
        else:
            url = post.video_url if post.is_video else post.url
            if url:
                assets.append(
                    {
                        "kind": "video" if post.is_video else "image",
                        "mime_type": "video/mp4" if post.is_video else "image/jpeg",
                        "url": url,
                    }
                )
    except Exception:
        logger.exception("Failed to extract media assets for %s — falling back to cover media", post.shortcode)

    if not assets:
        url = post.video_url if post.is_video else post.url
        if url:
            assets.append(
                {
                    "kind": "video" if post.is_video else "image",
                    "mime_type": "video/mp4" if post.is_video else "image/jpeg",
                    "url": url,
                }
            )

    return assets


def build_post_record(post: instaloader.Post) -> dict:
    return {
        "shortcode": post.shortcode,
        "post_type": _post_type(post),
        "likes": post.likes,
        "comments": _comment_count(post),
        "views": _view_count(post),
        "caption": post.caption,
        "posted_at": post.date_utc.isoformat() + "Z",
        "video_url": post.video_url if post.is_video else None,
        "thumbnail_url": post.url,
        "caption_mentions": _caption_mentions(post),
        "tagged_users": _tagged_usernames(post),
        "sponsor_users": _sponsor_usernames(post),
        "media_assets": _media_assets(post),
        "is_ad": _is_sponsored(post),
    }


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
        posts.append(build_post_record(post))
        if len(posts) >= limit:
            break

    return {"profile": profile_data, "posts": posts}
