from youfirst_scraper import roster_patterns


def test_influencer_status_computes_engagement_and_delta():
    profile_snapshots = [
        {"followers": 1000, "captured_at": "2026-06-01T00:00:00Z"},
        {"followers": 1100, "captured_at": "2026-07-06T00:00:00Z"},
    ]
    post_snapshots = [
        {"shortcode": "a", "post_type": "reel", "likes": 90, "comments": 10, "captured_at": "2026-07-06T00:00:00Z"},
    ]
    status = roster_patterns.influencer_status("handle", profile_snapshots, post_snapshots)
    assert status["handle"] == "handle"
    assert status["followers"] == 1100
    assert status["follower_delta"] == 100
    assert status["engagement_rate_pct"] == round(100 / 1100 * 100, 2)


def test_content_patterns_finds_shared_topic_across_two_handles():
    handle_posts = {
        "a": [
            {"shortcode": "a1", "likes": 100, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
            {"shortcode": "a2", "likes": 10, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
        ],
        "b": [
            {"shortcode": "b1", "likes": 200, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
            {"shortcode": "b2", "likes": 20, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
        ],
    }
    handle_content = {
        "a": {"a1": {"summary": "s", "analysis": {"topic": "values", "format": "carousel", "hook": "h"}}},
        "b": {"b1": {"summary": "s", "analysis": {"topic": "values", "format": "reel", "hook": "h2"}}},
    }

    patterns = roster_patterns.content_patterns(handle_content, handle_posts)

    topic_patterns = [p for p in patterns if p["attribute"] == "topic" and p["value"] == "values"]
    assert len(topic_patterns) == 1
    assert topic_patterns[0]["handles"] == ["a", "b"]
    assert len(topic_patterns[0]["evidence"]) == 2


def test_content_patterns_ignores_single_handle_matches():
    handle_posts = {
        "a": [
            {"shortcode": "a1", "likes": 100, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
            {"shortcode": "a2", "likes": 10, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
        ],
    }
    handle_content = {
        "a": {"a1": {"summary": "s", "analysis": {"topic": "values"}}},
    }

    patterns = roster_patterns.content_patterns(handle_content, handle_posts)

    assert patterns == []


def test_content_patterns_ignores_posts_below_threshold():
    handle_posts = {
        "a": [
            {"shortcode": "a1", "likes": 11, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
            {"shortcode": "a2", "likes": 10, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
        ],
        "b": [
            {"shortcode": "b1", "likes": 21, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
            {"shortcode": "b2", "likes": 20, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
        ],
    }
    handle_content = {
        "a": {"a1": {"summary": "s", "analysis": {"topic": "values"}}},
        "b": {"b1": {"summary": "s", "analysis": {"topic": "values"}}},
    }

    patterns = roster_patterns.content_patterns(handle_content, handle_posts)

    assert patterns == []


def test_content_patterns_handles_missing_analysis_gracefully():
    handle_posts = {
        "a": [
            {"shortcode": "a1", "likes": 100, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
            {"shortcode": "a2", "likes": 10, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"},
        ],
    }
    handle_content = {
        "a": {"a1": {"summary": "s", "analysis": {}}},
    }

    patterns = roster_patterns.content_patterns(handle_content, handle_posts)

    assert patterns == []


def test_compute_roster_patterns_builds_statuses_and_patterns():
    influencers = [{"id": 1, "handle": "a"}, {"id": 2, "handle": "b"}]
    profile_snapshots_by_id = {
        1: [{"followers": 1000, "captured_at": "2026-07-01T00:00:00Z"}],
        2: [{"followers": 2000, "captured_at": "2026-07-01T00:00:00Z"}],
    }
    post_snapshots_by_id = {
        1: [{"shortcode": "a1", "likes": 100, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"}],
        2: [{"shortcode": "b1", "likes": 200, "comments": 0, "captured_at": "2026-07-01T00:00:00Z"}],
    }
    content_map_by_id = {
        1: {"a1": {"summary": "s", "analysis": {"topic": "values"}}},
        2: {"b1": {"summary": "s", "analysis": {"topic": "values"}}},
    }

    result = roster_patterns.compute_roster_patterns(
        influencers, profile_snapshots_by_id, post_snapshots_by_id, content_map_by_id
    )

    assert len(result["statuses"]) == 2
    assert {s["handle"] for s in result["statuses"]} == {"a", "b"}
