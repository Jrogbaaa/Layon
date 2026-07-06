from youfirst_scraper import metrics


def test_engagement_rate_basic():
    posts = [{"likes": 90, "comments": 10}, {"likes": 80, "comments": 20}]
    assert metrics.engagement_rate(posts, followers=1000) == 10.0


def test_engagement_rate_zero_followers():
    assert metrics.engagement_rate([{"likes": 1, "comments": 1}], followers=0) == 0.0


def test_engagement_rate_no_posts():
    assert metrics.engagement_rate([], followers=1000) == 0.0


def test_follower_delta():
    snapshots = [{"followers": 1000}, {"followers": 1050}, {"followers": 1200}]
    assert metrics.follower_delta(snapshots) == 200


def test_follower_delta_single_snapshot():
    assert metrics.follower_delta([{"followers": 1000}]) == 0


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


def test_compute_metrics_combines_all():
    profile_snapshots = [{"followers": 1000}, {"followers": 1100}]
    posts = [
        {"post_type": "reel", "likes": 100, "comments": 10, "posted_at": "2026-07-01T00:00:00Z"},
        {"post_type": "photo", "likes": 50, "comments": 5, "posted_at": "2026-07-03T00:00:00Z"},
    ]
    result = metrics.compute_metrics(profile_snapshots, posts)
    assert result["follower_delta"] == 100
    assert result["format_performance"] == {"reel": 110.0, "photo": 55.0}
    assert result["posting_cadence_days"] == 2.0
