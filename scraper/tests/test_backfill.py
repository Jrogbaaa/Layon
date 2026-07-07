from unittest.mock import MagicMock, patch

from youfirst_scraper import backfill


def test_run_backfill_scrape_uploads_avatar(monkeypatch):
    monkeypatch.setattr(backfill.config, "load_roster", lambda: ["good_handle"])
    monkeypatch.setattr(backfill.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)

    monkeypatch.setattr(
        backfill.instagram_scraper,
        "scrape_profile",
        lambda loader, handle, post_limit=None: {
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

    monkeypatch.setattr(backfill.db, "get_or_create_influencer", lambda c, h: 9)
    monkeypatch.setattr(backfill.db, "insert_profile_snapshot", lambda c, i, p: None)
    monkeypatch.setattr(backfill.db, "insert_post_snapshots", lambda c, i, p: None)
    monkeypatch.setattr(backfill.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(backfill.db, "get_all_post_snapshots", lambda c, i: [])
    monkeypatch.setattr(backfill.db, "insert_highlights", lambda c, i, h: None)

    fake_response = MagicMock()
    fake_response.content = b"fake-image-bytes"
    fake_response.raise_for_status = lambda: None
    monkeypatch.setattr(backfill.requests, "get", lambda url, timeout=None: fake_response)

    upload_calls = []
    monkeypatch.setattr(
        backfill.db,
        "upload_avatar",
        lambda c, handle, image_bytes: upload_calls.append((handle, image_bytes)) or "https://cdn.example/good_handle.jpg",
    )
    avatar_update_calls = []
    monkeypatch.setattr(
        backfill.db,
        "update_influencer_avatar",
        lambda c, influencer_id, url: avatar_update_calls.append((influencer_id, url)),
    )

    with patch("instaloader.Instaloader"):
        backfill.run_backfill_scrape(MagicMock())

    assert upload_calls == [("good_handle", b"fake-image-bytes")]
    assert avatar_update_calls == [(9, "https://cdn.example/good_handle.jpg")]


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
