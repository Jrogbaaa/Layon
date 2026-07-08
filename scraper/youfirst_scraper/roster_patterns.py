from collections import defaultdict
from statistics import median

from . import metrics

NOTABLE_THRESHOLD_PCT = 30.0
MIN_HANDLES_FOR_SHARED_PATTERN = 2


def _post_engagement(post: dict) -> int:
    return post["likes"] + post["comments"]


def influencer_status(handle: str, profile_snapshots: list[dict], post_snapshots: list[dict]) -> dict:
    """Per-influencer roll-up: engagement rate, follower delta, warning highlight count."""
    latest_posts = list(metrics._latest_posts_by_shortcode(post_snapshots).values())
    latest_followers = profile_snapshots[-1]["followers"] if profile_snapshots else 0
    return {
        "handle": handle,
        "engagement_rate_pct": metrics.engagement_rate(latest_posts, latest_followers),
        "follower_delta": metrics.follower_delta(profile_snapshots),
        "followers": latest_followers,
    }


def content_patterns(handle_content: dict[str, dict[str, dict]], handle_posts: dict[str, list[dict]]) -> list[dict]:
    """Find content topics/formats/hooks that outperform each influencer's median engagement,
    grouped across influencers when the same attribute value recurs for 2+ handles.

    handle_content: {handle: {shortcode: {summary, analysis: {topic, format, hook}}}}
    handle_posts: {handle: [latest post_snapshots rows]}
    """
    attribute_hits: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for handle, content_map in handle_content.items():
        posts = handle_posts.get(handle, [])
        latest_posts = list(metrics._latest_posts_by_shortcode(posts).values())
        if not latest_posts:
            continue
        baseline = median(_post_engagement(p) for p in latest_posts)
        if baseline <= 0:
            continue

        posts_by_shortcode = {p["shortcode"]: p for p in latest_posts}
        for shortcode, content in content_map.items():
            post = posts_by_shortcode.get(shortcode)
            if post is None:
                continue
            engagement = _post_engagement(post)
            pct = round((engagement - baseline) / baseline * 100, 1)
            if pct < NOTABLE_THRESHOLD_PCT:
                continue

            analysis = content.get("analysis") or {}
            for attr in ("topic", "format", "hook"):
                value = analysis.get(attr)
                if not value:
                    continue
                attribute_hits[(attr, value)].append(
                    {
                        "handle": handle,
                        "shortcode": shortcode,
                        "pct": pct,
                        "engagement": engagement,
                        "median_engagement": baseline,
                    }
                )

    patterns = []
    for (attr, value), hits in attribute_hits.items():
        handles = sorted({hit["handle"] for hit in hits})
        if len(handles) < MIN_HANDLES_FOR_SHARED_PATTERN:
            continue
        patterns.append(
            {
                "attribute": attr,
                "value": value,
                "handles": handles,
                "evidence": sorted(hits, key=lambda h: h["pct"], reverse=True),
            }
        )

    patterns.sort(key=lambda p: max(h["pct"] for h in p["evidence"]), reverse=True)
    return patterns


def compute_roster_patterns(
    influencers: list[dict],
    profile_snapshots_by_id: dict[int, list[dict]],
    post_snapshots_by_id: dict[int, list[dict]],
    content_map_by_id: dict[int, dict[str, dict]],
) -> dict:
    """Top-level entry point: build the pattern-fact payload the briefing prompt consumes.

    influencers: [{id, handle, persona}, ...] (as returned by db.list_influencers)
    """
    statuses = []
    handle_content: dict[str, dict[str, dict]] = {}
    handle_posts: dict[str, list[dict]] = {}

    for influencer in influencers:
        handle = influencer["handle"]
        profile_snapshots = profile_snapshots_by_id.get(influencer["id"], [])
        post_snapshots = post_snapshots_by_id.get(influencer["id"], [])
        statuses.append(influencer_status(handle, profile_snapshots, post_snapshots))
        handle_content[handle] = content_map_by_id.get(influencer["id"], {})
        handle_posts[handle] = post_snapshots

    return {
        "statuses": statuses,
        "patterns": content_patterns(handle_content, handle_posts),
    }
