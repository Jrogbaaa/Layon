from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median


def engagement_rate(posts: list[dict], followers: int) -> float:
    """Average (likes + comments) / followers across the given posts, as a percentage."""
    if not posts or followers <= 0:
        return 0.0
    total = sum(post["likes"] + post["comments"] for post in posts)
    return round((total / len(posts)) / followers * 100, 2)


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _closest_older_snapshot(snapshots: list[dict], min_age_days: int) -> dict | None:
    """Return the newest snapshot at least min_age_days older than the latest."""
    if len(snapshots) < 2:
        return None

    if "captured_at" not in snapshots[-1]:
        return snapshots[0]

    latest = _parse_ts(snapshots[-1]["captured_at"])
    cutoff = latest - timedelta(days=min_age_days)
    candidates = [
        s for s in snapshots[:-1] if "captured_at" in s and _parse_ts(s["captured_at"]) <= cutoff
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda s: _parse_ts(s["captured_at"]))


def follower_delta(profile_snapshots: list[dict]) -> int:
    """Week-over-week follower change using the closest snapshot at least 6 days older."""
    if len(profile_snapshots) < 2:
        return 0

    older = _closest_older_snapshot(profile_snapshots, min_age_days=6)
    if older is None:
        return profile_snapshots[-1]["followers"] - profile_snapshots[0]["followers"]

    return profile_snapshots[-1]["followers"] - older["followers"]


def follower_growth_pct(profile_snapshots: list[dict]) -> float | None:
    if len(profile_snapshots) < 2:
        return None

    older = _closest_older_snapshot(profile_snapshots, min_age_days=6)
    if older is None:
        return None

    baseline = older["followers"]
    if baseline <= 0:
        return None

    latest = profile_snapshots[-1]["followers"]
    return round((latest - baseline) / baseline * 100, 1)


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

    dates = [_parse_ts(post["posted_at"]) for post in posts]
    dates.sort()
    gaps = [(dates[i + 1] - dates[i]).total_seconds() / 86400 for i in range(len(dates) - 1)]
    return round(sum(gaps) / len(gaps), 1)


def _engagement(post: dict) -> int:
    return post["likes"] + post["comments"]


def _latest_posts_by_shortcode(post_snapshots: list[dict]) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for row in post_snapshots:
        shortcode = row["shortcode"]
        if shortcode not in latest or _parse_ts(row["captured_at"]) > _parse_ts(latest[shortcode]["captured_at"]):
            latest[shortcode] = row
    return latest


def median_engagement(post_snapshots: list[dict]) -> float | None:
    latest_posts = list(_latest_posts_by_shortcode(post_snapshots).values())
    if not latest_posts:
        return None
    return float(median(_engagement(post) for post in latest_posts))


def post_outperformance_pct(post: dict, baseline: float | None) -> float | None:
    if baseline is None or baseline <= 0:
        return None
    return round((_engagement(post) - baseline) / baseline * 100, 1)


def post_growth_over_time(post_snapshots: list[dict], shortcode: str, min_age_days: int = 6) -> dict | None:
    """Diff likes/comments for one shortcode between latest and closest older capture."""
    rows = sorted(
        [row for row in post_snapshots if row["shortcode"] == shortcode],
        key=lambda row: _parse_ts(row["captured_at"]),
    )
    if len(rows) < 2:
        return None

    latest = rows[-1]
    older = _closest_older_snapshot(rows, min_age_days=min_age_days)
    if older is None:
        return None

    baseline_engagement = _engagement(older)
    latest_engagement = _engagement(latest)
    if baseline_engagement <= 0:
        return None

    return {
        "shortcode": shortcode,
        "likes_delta": latest["likes"] - older["likes"],
        "comments_delta": latest["comments"] - older["comments"],
        "engagement_pct": round((latest_engagement - baseline_engagement) / baseline_engagement * 100, 1),
        "older_captured_at": older["captured_at"],
        "latest_captured_at": latest["captured_at"],
    }


def top_reel_views_vs_median(post_snapshots: list[dict]) -> dict | None:
    latest_posts = list(_latest_posts_by_shortcode(post_snapshots).values())
    reels = [post for post in latest_posts if post.get("post_type") == "reel" and post.get("views")]
    if not reels:
        return None

    views = [post["views"] for post in reels]
    median_views = float(median(views))
    if median_views <= 0:
        return None

    top_reel = max(reels, key=lambda post: post["views"])
    pct = round((top_reel["views"] - median_views) / median_views * 100, 1)
    return {
        "shortcode": top_reel["shortcode"],
        "views": top_reel["views"],
        "median_views": median_views,
        "pct_vs_median": pct,
    }


def engagement_trend(post_snapshots: list[dict]) -> dict | None:
    """Compare the average engagement of the more-recent half of posts (by posted_at)
    against the older half, to detect a recent drop-off in performance."""
    latest_posts = list(_latest_posts_by_shortcode(post_snapshots).values())
    if len(latest_posts) < 4:
        return None

    ordered = sorted(latest_posts, key=lambda post: _parse_ts(post["posted_at"]))
    mid = len(ordered) // 2
    older, recent = ordered[:mid], ordered[mid:]
    older_avg = sum(_engagement(post) for post in older) / len(older)
    recent_avg = sum(_engagement(post) for post in recent) / len(recent)
    if older_avg <= 0:
        return None

    return {
        "pct": round((recent_avg - older_avg) / older_avg * 100, 1),
        "recent_avg": round(recent_avg, 1),
        "older_avg": round(older_avg, 1),
    }


def posting_gap(posts: list[dict], cadence_days: float, *, now: datetime | None = None) -> dict | None:
    """Days since the most recent post, if it exceeds 2x the usual cadence (min 7 days)."""
    if not posts:
        return None

    latest_posted_at = max(_parse_ts(post["posted_at"]) for post in posts)
    reference = now or datetime.now(timezone.utc)
    gap_days = (reference - latest_posted_at).total_seconds() / 86400
    threshold = max(cadence_days * 2, 7)
    if gap_days <= threshold:
        return None

    return {"gap_days": round(gap_days, 1), "threshold_days": round(threshold, 1)}


def compute_metrics(profile_snapshots: list[dict], posts: list[dict]) -> dict:
    """profile_snapshots: ascending by captured_at. posts: most recent snapshot's posts."""
    latest_followers = profile_snapshots[-1]["followers"] if profile_snapshots else 0
    return {
        "engagement_rate_pct": engagement_rate(posts, latest_followers),
        "follower_delta": follower_delta(profile_snapshots),
        "format_performance": format_performance(posts),
        "posting_cadence_days": posting_cadence_days(posts),
    }


def compute_highlights(
    handle: str,
    profile_snapshots: list[dict],
    post_snapshots: list[dict],
    *,
    notable_threshold_pct: float = 30.0,
    now: datetime | None = None,
) -> list[dict]:
    """Return notable highlight dicts with content + metric payload."""
    highlights: list[dict] = []
    latest_posts = list(_latest_posts_by_shortcode(post_snapshots).values())
    baseline = median_engagement(post_snapshots)

    if latest_posts and baseline is not None:
        best_post = max(latest_posts, key=_engagement)
        pct = post_outperformance_pct(best_post, baseline)
        if pct is not None and abs(pct) >= notable_threshold_pct:
            highlights.append(
                {
                    "content": (
                        f"@{handle}'s post {best_post['shortcode']} performed {pct:+.0f}% "
                        f"vs their typical post ({_engagement(best_post)} vs median {baseline:.0f} engagement)."
                    ),
                    "metric": {
                        "type": "outperformance",
                        "shortcode": best_post["shortcode"],
                        "pct": pct,
                        "engagement": _engagement(best_post),
                        "median_engagement": baseline,
                        "severity": "good" if pct >= 0 else "warning",
                    },
                }
            )

    for post in latest_posts[:5]:
        growth = post_growth_over_time(post_snapshots, post["shortcode"])
        if growth and abs(growth["engagement_pct"]) >= notable_threshold_pct:
            highlights.append(
                {
                    "content": (
                        f"@{handle}'s post {post['shortcode']} gained {growth['engagement_pct']:+.0f}% "
                        f"engagement since {growth['older_captured_at'][:10]} "
                        f"(+{growth['likes_delta']} likes, +{growth['comments_delta']} comments)."
                    ),
                    "metric": {
                        "type": "post_growth",
                        "severity": "good" if growth["engagement_pct"] >= 0 else "warning",
                        **growth,
                    },
                }
            )
            break

    follower_pct = follower_growth_pct(profile_snapshots)
    if follower_pct is not None and abs(follower_pct) >= notable_threshold_pct:
        highlights.append(
            {
                "content": (
                    f"@{handle} gained {follower_pct:+.1f}% followers week-over-week "
                    f"({profile_snapshots[-1]['followers']:,} now)."
                ),
                "metric": {
                    "type": "follower_growth",
                    "pct": follower_pct,
                    "followers": profile_snapshots[-1]["followers"],
                    "severity": "good" if follower_pct >= 0 else "warning",
                },
            }
        )

    reel_views = top_reel_views_vs_median(post_snapshots)
    if reel_views and abs(reel_views["pct_vs_median"]) >= notable_threshold_pct:
        highlights.append(
            {
                "content": (
                    f"@{handle}'s reel {reel_views['shortcode']} hit {reel_views['views']:,} views — "
                    f"{reel_views['pct_vs_median']:+.0f}% vs their median reel ({reel_views['median_views']:,.0f})."
                ),
                "metric": {
                    "type": "reel_views",
                    "severity": "good" if reel_views["pct_vs_median"] >= 0 else "warning",
                    **reel_views,
                },
            }
        )

    trend = engagement_trend(post_snapshots)
    if trend and trend["pct"] <= -notable_threshold_pct:
        highlights.append(
            {
                "content": (
                    f"@{handle}'s engagement is down {trend['pct']:.0f}% on recent posts vs "
                    f"earlier ones ({trend['recent_avg']:.0f} vs {trend['older_avg']:.0f} avg engagement)."
                ),
                "metric": {"type": "engagement_drop", "severity": "warning", **trend},
            }
        )

    cadence = posting_cadence_days(latest_posts)
    gap = posting_gap(latest_posts, cadence, now=now)
    if gap:
        highlights.append(
            {
                "content": (
                    f"@{handle} hasn't posted in {gap['gap_days']:.0f} days "
                    f"(usual cadence: every {cadence:.1f} days)."
                ),
                "metric": {"type": "posting_gap", "severity": "warning", "cadence_days": cadence, **gap},
            }
        )

    return highlights
