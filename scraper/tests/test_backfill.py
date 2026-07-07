from unittest.mock import MagicMock

from youfirst_scraper import backfill


def test_run_recommendations_calls_generate_recommendation_with_current_signature(monkeypatch):
    monkeypatch.setattr(backfill.db, "list_influencers", lambda c: [{"id": 1, "handle": "h", "persona": "Comedian"}])
    monkeypatch.setattr(backfill.db, "get_profile_snapshots", lambda c, i: [{"followers": 100}])
    monkeypatch.setattr(backfill.db, "get_recent_posts", lambda c, i: [])
    monkeypatch.setattr(backfill.db, "get_latest_highlights", lambda c, i: [{"content": "notable", "metric": {}}])
    monkeypatch.setattr(backfill.db, "get_post_content_map", lambda c, i: {"abc": {"summary": "s", "analysis": {}}})
    monkeypatch.setattr(backfill.db, "insert_recommendation", lambda c, i, m, content: None)

    calls = {}

    def fake_generate(handle, profile_snapshots, posts, persona=None, highlights=None, content_map=None):
        calls["args"] = (handle, persona, highlights, content_map)
        return "content"

    monkeypatch.setattr(backfill.recommendations, "generate_recommendation", fake_generate)

    backfill.run_recommendations(MagicMock())

    handle, persona, highlights, content_map = calls["args"]
    assert handle == "h"
    assert persona == "Comedian"
    assert highlights == [{"content": "notable", "metric": {}}]
    assert content_map == {"abc": {"summary": "s", "analysis": {}}}


def test_run_recommendations_skips_influencer_without_profile_history(monkeypatch):
    monkeypatch.setattr(backfill.db, "list_influencers", lambda c: [{"id": 1, "handle": "h", "persona": None}])
    monkeypatch.setattr(backfill.db, "get_profile_snapshots", lambda c, i: [])

    monkeypatch.setattr(
        backfill.recommendations,
        "generate_recommendation",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    backfill.run_recommendations(MagicMock())
