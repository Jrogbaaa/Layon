from collections import defaultdict


def engagement_rate(posts: list[dict], followers: int) -> float:
    """Average (likes + comments) / followers across the given posts, as a percentage."""
    if not posts or followers <= 0:
        return 0.0
    total = sum(post["likes"] + post["comments"] for post in posts)
    return round((total / len(posts)) / followers * 100, 2)


def follower_delta(profile_snapshots: list[dict]) -> int:
    """Change in followers between the oldest and newest snapshot given (ascending order)."""
    if len(profile_snapshots) < 2:
        return 0
    return profile_snapshots[-1]["followers"] - profile_snapshots[0]["followers"]


def format_performance(posts: list[dict]) -> dict:
    """Average engagement (likes + comments) per post, grouped by post_type."""
    totals: dict[str, list[int]] = defaultdict(list)
    for post in posts:
        totals[post["post_type"]].append(post["likes"] + post["comments"])

    return {
        post_type: round(sum(values) / len(values), 1)
        for post_type, values in totals.items()
    }


def posting_cadence_days(posts: list[dict]) -> float:
    """Average days between consecutive posts, given posts sorted oldest-to-newest
    with ISO 8601 `posted_at` timestamps."""
    if len(posts) < 2:
        return 0.0

    from datetime import datetime

    dates = [datetime.fromisoformat(post["posted_at"].replace("Z", "+00:00")) for post in posts]
    dates.sort()
    gaps = [(dates[i + 1] - dates[i]).total_seconds() / 86400 for i in range(len(dates) - 1)]
    return round(sum(gaps) / len(gaps), 1)


def compute_metrics(profile_snapshots: list[dict], posts: list[dict]) -> dict:
    """profile_snapshots: ascending by captured_at. posts: most recent snapshot's posts."""
    latest_followers = profile_snapshots[-1]["followers"] if profile_snapshots else 0
    return {
        "engagement_rate_pct": engagement_rate(posts, latest_followers),
        "follower_delta": follower_delta(profile_snapshots),
        "format_performance": format_performance(posts),
        "posting_cadence_days": posting_cadence_days(posts),
    }
