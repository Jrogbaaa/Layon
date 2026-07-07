from datetime import datetime, timezone

from youfirst_scraper import metrics


def _parse(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def test_engagement_rate_basic():
    posts = [{"likes": 90, "comments": 10}, {"likes": 80, "comments": 20}]
    assert metrics.engagement_rate(posts, followers=1000) == 10.0


def test_engagement_rate_zero_followers():
    assert metrics.engagement_rate([{"likes": 1, "comments": 1}], followers=0) == 0.0


def test_engagement_rate_no_posts():
    assert metrics.engagement_rate([], followers=1000) == 0.0


def test_follower_delta_uses_closest_older_snapshot():
    snapshots = [
        {"followers": 1000, "captured_at": "2026-06-01T00:00:00Z"},
        {"followers": 1050, "captured_at": "2026-06-20T00:00:00Z"},
        {"followers": 1200, "captured_at": "2026-07-06T00:00:00Z"},
    ]
    assert metrics.follower_delta(snapshots) == 150


def test_follower_delta_falls_back_when_no_week_old_snapshot():
    snapshots = [{"followers": 1000, "captured_at": "2026-07-05T00:00:00Z"}, {"followers": 1100, "captured_at": "2026-07-06T00:00:00Z"}]
    assert metrics.follower_delta(snapshots) == 100


def test_follower_delta_single_snapshot():
    assert metrics.follower_delta([{"followers": 1000, "captured_at": "2026-07-06T00:00:00Z"}]) == 0


def test_format_performance_groups_by_type():
    posts = [
        {"post_type": "reel", "likes": 100, "comments": 20},
        {"post_type": "reel", "likes": 200, "comments": 40},
        {"post_type": "photo", "likes": 50, "comments": 10},
    ]
    result = metrics.format_performance(posts)
    assert result == {"reel": 180.0, "photo": 60.0}


def test_posting_cadence_days():
    posts = [
        {"posted_at": "2026-07-01T00:00:00Z"},
        {"posted_at": "2026-07-03T00:00:00Z"},
        {"posted_at": "2026-07-07T00:00:00Z"},
    ]
    assert metrics.posting_cadence_days(posts) == 3.0


def test_posting_cadence_days_insufficient_posts():
    assert metrics.posting_cadence_days([{"posted_at": "2026-07-01T00:00:00Z"}]) == 0.0


def test_median_engagement_uses_latest_capture_per_shortcode():
    rows = [
        {"shortcode": "a", "likes": 100, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
        {"shortcode": "a", "likes": 200, "comments": 0, "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "b", "likes": 50, "comments": 50, "captured_at": "2026-07-06T00:00:00Z"},
    ]
    assert metrics.median_engagement(rows) == 150.0


def test_post_outperformance_pct():
    assert metrics.post_outperformance_pct({"likes": 200, "comments": 0}, 100.0) == 100.0


def test_post_growth_over_time_requires_history():
    rows = [
        {
            "shortcode": "abc",
            "likes": 100,
            "comments": 10,
            "captured_at": "2026-06-20T00:00:00Z",
        },
        {
            "shortcode": "abc",
            "likes": 200,
            "comments": 20,
            "captured_at": "2026-07-06T00:00:00Z",
        },
    ]
    growth = metrics.post_growth_over_time(rows, "abc")
    assert growth is not None
    assert growth["engagement_pct"] == 100.0


def test_post_growth_over_time_skips_without_old_capture():
    rows = [
        {"shortcode": "abc", "likes": 100, "comments": 10, "captured_at": "2026-07-05T00:00:00Z"},
        {"shortcode": "abc", "likes": 200, "comments": 20, "captured_at": "2026-07-06T00:00:00Z"},
    ]
    assert metrics.post_growth_over_time(rows, "abc") is None


def test_top_reel_views_vs_median():
    rows = [
        {"shortcode": "r1", "post_type": "reel", "views": 1000, "likes": 1, "comments": 0, "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "r2", "post_type": "reel", "views": 2000, "likes": 1, "comments": 0, "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "p1", "post_type": "photo", "views": None, "likes": 1, "comments": 0, "captured_at": "2026-07-06T00:00:00Z"},
    ]
    result = metrics.top_reel_views_vs_median(rows)
    assert result is not None
    assert result["shortcode"] == "r2"
    assert result["pct_vs_median"] == 33.3


def test_compute_highlights_filters_below_threshold():
    profile_snapshots = [
        {"followers": 1000, "captured_at": "2026-06-20T00:00:00Z"},
        {"followers": 1100, "captured_at": "2026-07-06T00:00:00Z"},
    ]
    post_snapshots = [
        {"shortcode": "a", "post_type": "photo", "likes": 100, "comments": 0, "views": None, "posted_at": "2026-07-01T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "b", "post_type": "photo", "likes": 110, "comments": 0, "views": None, "posted_at": "2026-07-05T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
    ]
    highlights = metrics.compute_highlights(
        "handle", profile_snapshots, post_snapshots, now=_parse("2026-07-06T00:00:00Z")
    )
    assert highlights == []


def test_compute_highlights_emits_notable_outperformance():
    post_snapshots = [
        {"shortcode": "a", "post_type": "photo", "likes": 100, "comments": 0, "views": None, "posted_at": "2026-07-01T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "b", "post_type": "photo", "likes": 200, "comments": 0, "views": None, "posted_at": "2026-07-03T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "c", "post_type": "photo", "likes": 500, "comments": 0, "views": None, "posted_at": "2026-07-05T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
    ]
    highlights = metrics.compute_highlights("handle", [], post_snapshots, now=_parse("2026-07-06T00:00:00Z"))
    assert len(highlights) == 1
    assert highlights[0]["metric"]["type"] == "outperformance"
    assert "+150%" in highlights[0]["content"]


def test_engagement_trend_detects_drop():
    posts = [
        {"shortcode": "a", "likes": 100, "comments": 0, "posted_at": "2026-06-01T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "b", "likes": 100, "comments": 0, "posted_at": "2026-06-05T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "c", "likes": 20, "comments": 0, "posted_at": "2026-07-01T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "d", "likes": 20, "comments": 0, "posted_at": "2026-07-05T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
    ]
    trend = metrics.engagement_trend(posts)
    assert trend is not None
    assert trend["pct"] == -80.0


def test_engagement_trend_requires_at_least_four_posts():
    posts = [
        {"shortcode": "a", "likes": 100, "comments": 0, "posted_at": "2026-06-01T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
    ]
    assert metrics.engagement_trend(posts) is None


def test_posting_gap_flags_long_absence():
    posts = [{"posted_at": "2026-06-01T00:00:00Z"}]
    now = datetime(2026, 7, 6, tzinfo=timezone.utc)
    gap = metrics.posting_gap(posts, cadence_days=2.0, now=now)
    assert gap is not None
    assert gap["gap_days"] == 35.0


def test_posting_gap_none_within_cadence():
    posts = [{"posted_at": "2026-07-01T00:00:00Z"}]
    now = datetime(2026, 7, 3, tzinfo=timezone.utc)
    assert metrics.posting_gap(posts, cadence_days=2.0, now=now) is None


def test_compute_highlights_emits_engagement_drop_and_posting_gap():
    post_snapshots = [
        {"shortcode": "a", "post_type": "photo", "likes": 100, "comments": 0, "views": None, "posted_at": "2026-05-01T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "b", "post_type": "photo", "likes": 100, "comments": 0, "views": None, "posted_at": "2026-05-05T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "c", "post_type": "photo", "likes": 5, "comments": 0, "views": None, "posted_at": "2026-05-10T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
        {"shortcode": "d", "post_type": "photo", "likes": 5, "comments": 0, "views": None, "posted_at": "2026-05-15T00:00:00Z", "captured_at": "2026-07-06T00:00:00Z"},
    ]

    highlights = metrics.compute_highlights(
        "handle", [], post_snapshots, now=datetime(2026, 7, 6, tzinfo=timezone.utc)
    )

    types_ = {h["metric"]["type"] for h in highlights}
    assert "engagement_drop" in types_
    assert "posting_gap" in types_
    assert all(h["metric"]["severity"] == "warning" for h in highlights if h["metric"]["type"] in ("engagement_drop", "posting_gap"))


def test_compute_metrics_combines_all():
    profile_snapshots = [
        {"followers": 1000, "captured_at": "2026-07-05T00:00:00Z"},
        {"followers": 1100, "captured_at": "2026-07-06T00:00:00Z"},
    ]
    posts = [
        {"post_type": "reel", "likes": 100, "comments": 10, "posted_at": "2026-07-01T00:00:00Z"},
        {"post_type": "photo", "likes": 50, "comments": 5, "posted_at": "2026-07-03T00:00:00Z"},
    ]
    result = metrics.compute_metrics(profile_snapshots, posts)
    assert result["follower_delta"] == 100
    assert result["format_performance"] == {"reel": 110.0, "photo": 55.0}
    assert result["posting_cadence_days"] == 2.0
