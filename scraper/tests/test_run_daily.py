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


def test_run_recommendations_does_not_fetch_trends(monkeypatch):
    monkeypatch.setattr(run_daily.db, "list_influencers", lambda c: [{"id": 1, "handle": "h", "persona": None}])
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [{"followers": 100}])
    monkeypatch.setattr(run_daily.db, "get_recent_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_latest_highlights", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_post_content_map", lambda c, i: {})
    monkeypatch.setattr(run_daily.db, "insert_recommendation", lambda c, i, m, content: None)

    calls = {}

    def fake_generate(handle, profile_snapshots, posts, persona=None, highlights=None, content_map=None):
        calls["args"] = (handle, persona, highlights, content_map)
        return "content"

    monkeypatch.setattr(run_daily.recommendations, "generate_recommendation", fake_generate)
    monkeypatch.setattr(run_daily.db, "get_latest_trend_snapshots", lambda c, limit=None: (_ for _ in ()).throw(AssertionError("should not be called")))

    run_daily.run_recommendations(MagicMock())

    assert calls["args"][0] == "h"


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
