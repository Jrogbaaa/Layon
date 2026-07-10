import json
from datetime import date
from unittest.mock import MagicMock, patch

from youfirst_scraper import run_daily


def test_already_ran_today_false_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(run_daily.config, "LAST_RUN_FILE", tmp_path / ".last_run")
    assert run_daily.already_ran_today() is False


def test_already_ran_today_true_when_marked(tmp_path, monkeypatch):
    last_run_file = tmp_path / ".last_run"
    last_run_file.write_text(date.today().isoformat())
    monkeypatch.setattr(run_daily.config, "LAST_RUN_FILE", last_run_file)
    assert run_daily.already_ran_today() is True


def test_already_ran_today_false_when_stale(tmp_path, monkeypatch):
    last_run_file = tmp_path / ".last_run"
    last_run_file.write_text("2000-01-01")
    monkeypatch.setattr(run_daily.config, "LAST_RUN_FILE", last_run_file)
    assert run_daily.already_ran_today() is False


def test_mark_ran_today_writes_today(tmp_path, monkeypatch):
    last_run_file = tmp_path / ".last_run"
    monkeypatch.setattr(run_daily.config, "LAST_RUN_FILE", last_run_file)
    run_daily.mark_ran_today()
    assert last_run_file.read_text().strip() == date.today().isoformat()


def test_run_instagram_scrape_skips_failing_handle_and_continues(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["good_handle", "bad_handle"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)

    def fake_scrape_profile(loader, handle):
        if handle == "bad_handle":
            raise instaloader_exception()
        return {"profile": {"followers": 1, "following": 2, "media_count": 3, "bio": ""}, "posts": []}

    def instaloader_exception():
        return Exception("profile not found")

    monkeypatch.setattr(run_daily.instagram_scraper, "scrape_profile", fake_scrape_profile)

    client = MagicMock()
    client_calls = []
    monkeypatch.setattr(run_daily.db, "get_or_create_influencer", lambda c, h: client_calls.append(h) or 1)
    monkeypatch.setattr(run_daily.db, "insert_profile_snapshot", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "insert_post_snapshots", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "get_analyzed_shortcodes", lambda c, i: set())
    monkeypatch.setattr(run_daily.content_analysis, "analyze_posts", lambda posts, analyzed: [])
    monkeypatch.setattr(run_daily.db, "insert_post_content", lambda c, i, a: None)
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_all_post_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "insert_highlights", lambda c, i, h: None)

    with patch("instaloader.Instaloader"):
        run_daily.run_instagram_scrape(client)

    assert client_calls == ["good_handle"]


def test_run_instagram_scrape_uploads_avatar(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["good_handle"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)

    monkeypatch.setattr(
        run_daily.instagram_scraper,
        "scrape_profile",
        lambda loader, handle: {
            "profile": {
                "followers": 1,
                "following": 2,
                "media_count": 3,
                "bio": "",
                "avatar_source_url": "https://instagram.example/pic.jpg",
            },
            "posts": [],
        },
    )

    monkeypatch.setattr(run_daily.db, "get_or_create_influencer", lambda c, h: 7)
    monkeypatch.setattr(run_daily.db, "insert_profile_snapshot", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "insert_post_snapshots", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "get_analyzed_shortcodes", lambda c, i: set())
    monkeypatch.setattr(run_daily.content_analysis, "analyze_posts", lambda posts, analyzed: [])
    monkeypatch.setattr(run_daily.db, "insert_post_content", lambda c, i, a: None)
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_all_post_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "insert_highlights", lambda c, i, h: None)

    fake_response = MagicMock()
    fake_response.content = b"fake-image-bytes"
    fake_response.raise_for_status = lambda: None
    monkeypatch.setattr(run_daily.requests, "get", lambda url, timeout=None: fake_response)

    upload_calls = []
    monkeypatch.setattr(
        run_daily.db,
        "upload_avatar",
        lambda c, handle, image_bytes: upload_calls.append((handle, image_bytes)) or "https://cdn.example/good_handle.jpg",
    )
    avatar_update_calls = []
    monkeypatch.setattr(
        run_daily.db,
        "update_influencer_avatar",
        lambda c, influencer_id, url: avatar_update_calls.append((influencer_id, url)),
    )

    with patch("instaloader.Instaloader"):
        run_daily.run_instagram_scrape(MagicMock())

    assert upload_calls == [("good_handle", b"fake-image-bytes")]
    assert avatar_update_calls == [(7, "https://cdn.example/good_handle.jpg")]


def test_run_instagram_scrape_continues_when_avatar_download_fails(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["good_handle"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)

    monkeypatch.setattr(
        run_daily.instagram_scraper,
        "scrape_profile",
        lambda loader, handle: {
            "profile": {
                "followers": 1,
                "following": 2,
                "media_count": 3,
                "bio": "",
                "avatar_source_url": "https://instagram.example/pic.jpg",
            },
            "posts": [],
        },
    )

    monkeypatch.setattr(run_daily.db, "get_or_create_influencer", lambda c, h: 7)
    monkeypatch.setattr(run_daily.db, "insert_profile_snapshot", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "insert_post_snapshots", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "get_analyzed_shortcodes", lambda c, i: set())
    monkeypatch.setattr(run_daily.content_analysis, "analyze_posts", lambda posts, analyzed: [])
    monkeypatch.setattr(run_daily.db, "insert_post_content", lambda c, i, a: None)
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_all_post_snapshots", lambda c, i: [])
    highlight_calls = []
    monkeypatch.setattr(run_daily.db, "insert_highlights", lambda c, i, h: highlight_calls.append(i))

    def raise_network_error(url, timeout=None):
        raise Exception("network error")

    monkeypatch.setattr(run_daily.requests, "get", raise_network_error)

    with patch("instaloader.Instaloader"):
        run_daily.run_instagram_scrape(MagicMock())

    assert highlight_calls == [7]


def test_run_trend_scrape_skips_already_scraped_source(monkeypatch):
    monkeypatch.setattr(run_daily.config, "TREND_SOURCES", ["https://example.com/a"])
    monkeypatch.setattr(run_daily.db, "trend_source_scraped_today", lambda c, url: True)

    insert_calls = []
    monkeypatch.setattr(run_daily.db, "insert_trend_snapshot", lambda c, url, title, text: insert_calls.append(url))
    monkeypatch.setattr(
        run_daily.trend_scraper,
        "scrape_trend_source",
        lambda url: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    run_daily.run_trend_scrape(MagicMock())

    assert insert_calls == []


def test_run_recommendations_passes_latest_trend_headline_texts(monkeypatch):
    monkeypatch.setattr(run_daily.db, "list_influencers", lambda c: [{"id": 1, "handle": "h", "persona": None}])
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [{"followers": 100}])
    monkeypatch.setattr(run_daily.db, "get_recent_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_latest_highlights", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_post_content_map", lambda c, i: {})
    monkeypatch.setattr(run_daily.db, "get_top_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "insert_recommendation", lambda c, i, m, content: None)
    monkeypatch.setattr(
        run_daily.db,
        "get_latest_trend_headlines",
        lambda c: {
            "content": json.dumps(
                {"headlines": [{"text": {"en": "OT 2026 gala shock elimination", "es": "..."}, "source_url": None}]}
            )
        },
    )

    calls = {}

    def fake_generate(
        handle, profile_snapshots, posts, persona=None, highlights=None, content_map=None,
        alltime_top_posts=None, trend_items=None,
    ):
        calls["trend_items"] = trend_items
        return "content"

    monkeypatch.setattr(run_daily.recommendations, "generate_recommendation", fake_generate)

    run_daily.run_recommendations(MagicMock())

    assert calls["trend_items"] == ["OT 2026 gala shock elimination"]


def test_run_recommendations_passes_none_when_no_headlines(monkeypatch):
    monkeypatch.setattr(run_daily.db, "list_influencers", lambda c: [{"id": 1, "handle": "h", "persona": None}])
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [{"followers": 100}])
    monkeypatch.setattr(run_daily.db, "get_recent_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_latest_highlights", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_post_content_map", lambda c, i: {})
    monkeypatch.setattr(run_daily.db, "get_top_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "insert_recommendation", lambda c, i, m, content: None)
    monkeypatch.setattr(run_daily.db, "get_latest_trend_headlines", lambda c: None)

    calls = {}

    def fake_generate(
        handle, profile_snapshots, posts, persona=None, highlights=None, content_map=None,
        alltime_top_posts=None, trend_items=None,
    ):
        calls["trend_items"] = trend_items
        return "content"

    monkeypatch.setattr(run_daily.recommendations, "generate_recommendation", fake_generate)

    run_daily.run_recommendations(MagicMock())

    assert calls["trend_items"] is None


def test_run_recommendations_passes_alltime_top_posts(monkeypatch):
    monkeypatch.setattr(run_daily.db, "list_influencers", lambda c: [{"id": 1, "handle": "h", "persona": None}])
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [{"followers": 100}])
    monkeypatch.setattr(run_daily.db, "get_recent_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_latest_highlights", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_post_content_map", lambda c, i: {})
    top_posts = [{"shortcode": "abc", "likes": 190000, "comments": 10000}]
    monkeypatch.setattr(run_daily.db, "get_top_posts", lambda c, i: top_posts)
    monkeypatch.setattr(run_daily.db, "insert_recommendation", lambda c, i, m, content: None)
    monkeypatch.setattr(run_daily.db, "get_latest_trend_headlines", lambda c: None)

    calls = {}

    def fake_generate(
        handle, profile_snapshots, posts, persona=None, highlights=None, content_map=None,
        alltime_top_posts=None, trend_items=None,
    ):
        calls["alltime_top_posts"] = alltime_top_posts
        return "content"

    monkeypatch.setattr(run_daily.recommendations, "generate_recommendation", fake_generate)

    run_daily.run_recommendations(MagicMock())

    assert calls["alltime_top_posts"] == top_posts


def test_run_recommendations_skips_insert_when_generation_returns_none(monkeypatch):
    monkeypatch.setattr(run_daily.db, "list_influencers", lambda c: [{"id": 1, "handle": "h", "persona": None}])
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [{"followers": 100}])
    monkeypatch.setattr(run_daily.db, "get_recent_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_latest_highlights", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_post_content_map", lambda c, i: {})
    monkeypatch.setattr(run_daily.db, "get_top_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_latest_trend_headlines", lambda c: None)
    monkeypatch.setattr(run_daily.recommendations, "generate_recommendation", lambda *a, **k: None)

    insert_calls = []
    monkeypatch.setattr(run_daily.db, "insert_recommendation", lambda c, i, m, content: insert_calls.append(content))

    run_daily.run_recommendations(MagicMock())

    assert insert_calls == []


def test_run_roster_briefing_skips_when_no_influencers(monkeypatch):
    monkeypatch.setattr(run_daily.db, "list_influencers", lambda c: [])
    monkeypatch.setattr(
        run_daily.briefing,
        "generate_briefing",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    run_daily.run_roster_briefing(MagicMock())


def test_run_roster_briefing_generates_and_stores(monkeypatch):
    monkeypatch.setattr(
        run_daily.db, "list_influencers", lambda c: [{"id": 1, "handle": "a"}, {"id": 2, "handle": "b"}]
    )
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_all_post_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_post_content_map", lambda c, i: {})
    monkeypatch.setattr(
        run_daily.db,
        "get_latest_recommendation",
        lambda c, i: {"content": json.dumps({"bullets": [{"text": {"en": "Do X", "es": "Haz X"}}]})},
    )

    calls = {}

    def fake_generate(pattern_facts, recommendations_by_handle=None):
        calls["recs"] = recommendations_by_handle
        return json.dumps({"summary": {"en": "ok", "es": "ok"}, "patterns": [], "actions": []})

    monkeypatch.setattr(run_daily.briefing, "generate_briefing", fake_generate)

    insert_calls = []
    monkeypatch.setattr(
        run_daily.db, "insert_roster_briefing", lambda c, model, content: insert_calls.append((model, content))
    )

    run_daily.run_roster_briefing(MagicMock())

    assert calls["recs"] == {"a": "Do X", "b": "Do X"}
    assert len(insert_calls) == 1


def test_run_roster_briefing_skips_insert_when_generation_returns_none(monkeypatch):
    monkeypatch.setattr(run_daily.db, "list_influencers", lambda c: [{"id": 1, "handle": "a"}])
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_all_post_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_post_content_map", lambda c, i: {})
    monkeypatch.setattr(run_daily.db, "get_latest_recommendation", lambda c, i: None)
    monkeypatch.setattr(run_daily.briefing, "generate_briefing", lambda *a, **k: None)

    insert_calls = []
    monkeypatch.setattr(
        run_daily.db, "insert_roster_briefing", lambda c, model, content: insert_calls.append(content)
    )

    run_daily.run_roster_briefing(MagicMock())

    assert insert_calls == []


def test_run_roster_briefing_does_not_crash_pipeline_on_unexpected_error(monkeypatch):
    monkeypatch.setattr(run_daily.db, "list_influencers", lambda c: [{"id": 1, "handle": "a"}])
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_all_post_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_post_content_map", lambda c, i: {})
    monkeypatch.setattr(run_daily.db, "get_latest_recommendation", lambda c, i: None)

    def raise_unexpected(*args, **kwargs):
        raise KeyError("handles")

    monkeypatch.setattr(run_daily.briefing, "generate_briefing", raise_unexpected)

    insert_calls = []
    monkeypatch.setattr(
        run_daily.db, "insert_roster_briefing", lambda c, model, content: insert_calls.append(content)
    )

    # Must not raise — an unexpected failure here shouldn't crash main()'s daily run.
    run_daily.run_roster_briefing(MagicMock())

    assert insert_calls == []


def test_run_trend_headlines_skips_when_no_snapshots(monkeypatch):
    monkeypatch.setattr(run_daily.db, "get_latest_trend_snapshots", lambda c, limit=None: [])
    monkeypatch.setattr(
        run_daily.trend_headlines,
        "generate_headlines",
        lambda snapshots: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    run_daily.run_trend_headlines(MagicMock())


def test_run_trend_headlines_uses_all_source_count_as_limit(monkeypatch):
    monkeypatch.setattr(run_daily.config, "TREND_SOURCES", ["https://a", "https://b", "https://c"])
    calls = {}
    monkeypatch.setattr(
        run_daily.db,
        "get_latest_trend_snapshots",
        lambda c, limit=None: calls.setdefault("limit", limit) or [{"source_url": "https://a", "title": "t", "content_text": "body"}],
    )
    monkeypatch.setattr(run_daily.trend_headlines, "generate_headlines", lambda snapshots: json.dumps({"headlines": []}))

    insert_calls = []
    monkeypatch.setattr(run_daily.db, "insert_trend_headlines", lambda c, model, content: insert_calls.append(content))

    run_daily.run_trend_headlines(MagicMock())

    assert calls["limit"] == 3
    assert len(insert_calls) == 1


def test_run_trend_headlines_keeps_previous_when_generation_returns_none(monkeypatch):
    monkeypatch.setattr(
        run_daily.db,
        "get_latest_trend_snapshots",
        lambda c, limit=None: [{"source_url": "https://a", "title": "t", "content_text": "body"}],
    )
    monkeypatch.setattr(run_daily.trend_headlines, "generate_headlines", lambda snapshots: None)

    insert_calls = []
    monkeypatch.setattr(run_daily.db, "insert_trend_headlines", lambda c, model, content: insert_calls.append(content))

    run_daily.run_trend_headlines(MagicMock())

    assert insert_calls == []


def test_run_trend_scrape_skips_failing_source_and_continues(monkeypatch):
    monkeypatch.setattr(run_daily.config, "TREND_SOURCES", ["https://example.com/a", "https://example.com/b"])
    monkeypatch.setattr(run_daily.db, "trend_source_scraped_today", lambda c, url: False)

    def fake_scrape(url):
        if url == "https://example.com/a":
            raise Exception("network error")
        return {"title": "Title", "content_text": "Body text"}

    monkeypatch.setattr(run_daily.trend_scraper, "scrape_trend_source", fake_scrape)

    insert_calls = []
    monkeypatch.setattr(
        run_daily.db, "insert_trend_snapshot", lambda c, url, title, text: insert_calls.append(url)
    )

    run_daily.run_trend_scrape(MagicMock())

    assert insert_calls == ["https://example.com/b"]
