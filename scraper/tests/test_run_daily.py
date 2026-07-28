import json
import socket
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest

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


def _patch_scrape_db(monkeypatch):
    """Stub the db/content-analysis surface run_instagram_scrape touches."""
    monkeypatch.setattr(run_daily.db, "get_or_create_influencer", lambda c, h: 1)
    monkeypatch.setattr(run_daily.db, "profile_scraped_today", lambda c, i: False)
    monkeypatch.setattr(run_daily.db, "insert_profile_snapshot", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "insert_post_snapshots", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "get_post_classifications", lambda c, i: {})
    monkeypatch.setattr(run_daily.db, "upsert_post_classifications", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "get_analyzed_shortcodes", lambda c, i: set())
    monkeypatch.setattr(run_daily.db, "get_ad_flags", lambda c, i, s: {})
    monkeypatch.setattr(run_daily.content_analysis, "analyze_posts", lambda posts, analyzed: [])
    monkeypatch.setattr(run_daily.db, "insert_post_content", lambda c, i, a: None)
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_all_post_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "insert_highlights", lambda c, i, h: None)


def test_run_instagram_scrape_skips_failing_handle_and_continues(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["good_handle", "bad_handle"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)

    def fake_scrape_profile(loader, handle):
        if handle == "bad_handle":
            raise Exception("profile not found")
        return {"profile": {"followers": 1, "following": 2, "media_count": 3, "bio": ""}, "posts": []}

    monkeypatch.setattr(run_daily.instagram_scraper, "scrape_profile", fake_scrape_profile)

    _patch_scrape_db(monkeypatch)
    snapshot_calls = []
    monkeypatch.setattr(
        run_daily.db, "insert_profile_snapshot", lambda c, i, p: snapshot_calls.append(i)
    )

    with patch("instaloader.Instaloader"):
        failed = run_daily.run_instagram_scrape(MagicMock())

    assert snapshot_calls == [1]
    assert failed == ["bad_handle"]


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

    _patch_scrape_db(monkeypatch)
    monkeypatch.setattr(run_daily.db, "get_or_create_influencer", lambda c, h: 7)

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

    _patch_scrape_db(monkeypatch)
    monkeypatch.setattr(run_daily.db, "get_or_create_influencer", lambda c, h: 7)
    highlight_calls = []
    monkeypatch.setattr(run_daily.db, "insert_highlights", lambda c, i, h: highlight_calls.append(i))

    def raise_network_error(url, timeout=None):
        raise Exception("network error")

    monkeypatch.setattr(run_daily.requests, "get", raise_network_error)

    with patch("instaloader.Instaloader"):
        run_daily.run_instagram_scrape(MagicMock())

    assert highlight_calls == [7]


def test_run_instagram_scrape_reuses_stored_classifications(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["good_handle"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)

    posts = [{"shortcode": "known"}, {"shortcode": "fresh"}]
    monkeypatch.setattr(
        run_daily.instagram_scraper,
        "scrape_profile",
        lambda loader, handle: {
            "profile": {"followers": 1, "following": 2, "media_count": 3, "bio": ""},
            "posts": posts,
        },
    )

    _patch_scrape_db(monkeypatch)
    monkeypatch.setattr(
        run_daily.db,
        "get_post_classifications",
        lambda c, i: {
            "known": {
                "shortcode": "known",
                "status": "paid",
                "decision_code": "instagram_paid_partnership",
                "evidence": {},
                "classifier_version": "brand-evidence-v1",
                "input_hash": "cached",
                "classified_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    inserted = []
    monkeypatch.setattr(run_daily.db, "upsert_post_classifications", lambda c, i, p: inserted.extend(p))

    def fake_classify_posts(posts, client, loader=None, known=None):
        assert known is not None and "known" in known
        return [
            {
                **post,
                "classification": {
                    "status": "organic",
                    "decision_code": "people_only_or_incidental_brand",
                    "evidence": {},
                    "classifier_version": "brand-evidence-v1",
                    "input_hash": f"fresh-{post['shortcode']}",
                    "classified_at": datetime.now(timezone.utc).isoformat(),
                },
                "is_ad": False,
            }
            if post["shortcode"] == "fresh"
            else {
                **post,
                "classification": known["known"],
                "is_ad": True,
            }
            for post in posts
        ]

    with patch("instaloader.Instaloader"):
        with patch("youfirst_scraper.ad_detection.genai.Client", return_value=MagicMock()):
            with patch("youfirst_scraper.ad_detection.classify_posts", side_effect=fake_classify_posts):
                run_daily.run_instagram_scrape(MagicMock())

    assert {p["shortcode"]: p["classification"]["status"] for p in inserted} == {
        "known": "paid",
        "fresh": "organic",
    }


def test_run_instagram_scrape_classifies_every_roster_profile(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["alpha", "beta"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)
    influencer_ids = {"alpha": 11, "beta": 22}
    monkeypatch.setattr(
        run_daily.instagram_scraper,
        "scrape_profile",
        lambda loader, handle: {
            "profile": {"followers": 100, "following": 2, "media_count": 3, "bio": ""},
            "posts": [{"shortcode": f"{handle}-post", "is_ad": False}],
        },
    )

    _patch_scrape_db(monkeypatch)
    monkeypatch.setattr(run_daily.db, "get_or_create_influencer", lambda c, h: influencer_ids[h])
    upserts = []
    monkeypatch.setattr(
        run_daily.db,
        "upsert_post_classifications",
        lambda c, influencer_id, posts: upserts.append((influencer_id, posts[0]["shortcode"])),
    )

    def classify(posts, client, loader=None, known=None):
        post = posts[0]
        return [{
            **post,
            "is_ad": False,
            "classification": {
                "status": "organic",
                "decision_code": "people_only_or_incidental_brand",
                "evidence": {},
                "classifier_version": "brand-evidence-v1",
                "input_hash": f"hash-{post['shortcode']}",
                "classified_at": datetime.now(timezone.utc).isoformat(),
            },
        }]

    with patch("instaloader.Instaloader"):
        with patch("youfirst_scraper.ad_detection.genai.Client", return_value=MagicMock()):
            with patch("youfirst_scraper.ad_detection.classify_posts", side_effect=classify):
                failed = run_daily.run_instagram_scrape(MagicMock())

    assert failed == []
    assert upserts == [(11, "alpha-post"), (22, "beta-post")]


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
            "generated_at": datetime.now(timezone.utc).isoformat(),
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


def test_run_recommendations_passes_none_when_headlines_are_stale(monkeypatch):
    monkeypatch.setattr(run_daily.db, "list_influencers", lambda c: [{"id": 1, "handle": "h", "persona": None}])
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [{"followers": 100}])
    monkeypatch.setattr(run_daily.db, "get_recent_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_latest_highlights", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_post_content_map", lambda c, i: {})
    monkeypatch.setattr(run_daily.db, "get_top_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "insert_recommendation", lambda c, i, m, content: None)
    # Kept-over row from two days ago: must not be presented as today's trends.
    monkeypatch.setattr(
        run_daily.db,
        "get_latest_trend_headlines",
        lambda c: {
            "generated_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "content": json.dumps(
                {"headlines": [{"text": {"en": "old trend", "es": "..."}, "source_url": None}]}
            ),
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

    assert calls["trend_items"] is None


def test_run_recommendations_continues_when_headline_fetch_raises(monkeypatch):
    monkeypatch.setattr(run_daily.db, "list_influencers", lambda c: [{"id": 1, "handle": "h", "persona": None}])
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [{"followers": 100}])
    monkeypatch.setattr(run_daily.db, "get_recent_posts", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_latest_highlights", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_post_content_map", lambda c, i: {})
    monkeypatch.setattr(run_daily.db, "get_top_posts", lambda c, i: [])
    monkeypatch.setattr(
        run_daily.db,
        "get_latest_trend_headlines",
        lambda c: (_ for _ in ()).throw(Exception("network error")),
    )

    calls = {}

    def fake_generate(
        handle, profile_snapshots, posts, persona=None, highlights=None, content_map=None,
        alltime_top_posts=None, trend_items=None,
    ):
        calls["trend_items"] = trend_items
        return "content"

    monkeypatch.setattr(run_daily.recommendations, "generate_recommendation", fake_generate)

    insert_calls = []
    monkeypatch.setattr(run_daily.db, "insert_recommendation", lambda c, i, m, content: insert_calls.append(content))

    # Must not raise — a headline fetch failure shouldn't abort the daily run.
    run_daily.run_recommendations(MagicMock())

    assert calls["trend_items"] is None
    assert len(insert_calls) == 1


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

    def fake_get_latest_trend_snapshots(c, limit=None):
        calls["limit"] = limit
        return [{"source_url": "https://a", "title": "t", "content_text": "body"}]

    monkeypatch.setattr(run_daily.db, "get_latest_trend_snapshots", fake_get_latest_trend_snapshots)
    monkeypatch.setattr(run_daily.trend_headlines, "generate_headlines", lambda snapshots: json.dumps({"headlines": []}))

    insert_calls = []
    monkeypatch.setattr(run_daily.db, "insert_trend_headlines", lambda c, model, content: insert_calls.append(content))

    run_daily.run_trend_headlines(MagicMock())

    assert calls["limit"] == 21
    assert len(insert_calls) == 1


def test_run_trend_headlines_dedupes_to_newest_snapshot_per_source(monkeypatch):
    monkeypatch.setattr(run_daily.config, "TREND_SOURCES", ["https://a", "https://b"])
    # Newest-first, as the db query returns: source a scraped today and yesterday,
    # source b only yesterday.
    monkeypatch.setattr(
        run_daily.db,
        "get_latest_trend_snapshots",
        lambda c, limit=None: [
            {"source_url": "https://a", "title": "a-today", "content_text": "body"},
            {"source_url": "https://a", "title": "a-yesterday", "content_text": "body"},
            {"source_url": "https://b", "title": "b-yesterday", "content_text": "body"},
        ],
    )

    seen = {}
    monkeypatch.setattr(
        run_daily.trend_headlines,
        "generate_headlines",
        lambda snapshots: seen.setdefault("snapshots", snapshots) and json.dumps({"headlines": []}),
    )
    monkeypatch.setattr(run_daily.db, "insert_trend_headlines", lambda c, model, content: None)

    run_daily.run_trend_headlines(MagicMock())

    assert [s["title"] for s in seen["snapshots"]] == ["a-today", "b-yesterday"]


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


def _profile(followers=100):
    return {"profile": {"followers": followers, "following": 2, "media_count": 3, "bio": ""}, "posts": []}


def test_run_instagram_scrape_skips_handle_already_scraped_today(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["done_handle"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)
    _patch_scrape_db(monkeypatch)
    monkeypatch.setattr(run_daily.db, "profile_scraped_today", lambda c, i: True)
    monkeypatch.setattr(
        run_daily.instagram_scraper,
        "scrape_profile",
        lambda loader, handle: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    with patch("instaloader.Instaloader"):
        failed = run_daily.run_instagram_scrape(MagicMock())

    assert failed == []


def test_run_instagram_scrape_aborts_roster_on_session_expiry(monkeypatch):
    import instaloader

    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["first", "second", "third"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)
    _patch_scrape_db(monkeypatch)

    scrape_calls = []

    def fake_scrape(loader, handle):
        scrape_calls.append(handle)
        raise instaloader.exceptions.LoginRequiredException("login required")

    monkeypatch.setattr(run_daily.instagram_scraper, "scrape_profile", fake_scrape)
    notify_calls = []
    monkeypatch.setattr(run_daily, "_notify", lambda title, message: notify_calls.append(title))

    with patch("instaloader.Instaloader"):
        failed = run_daily.run_instagram_scrape(MagicMock())

    assert scrape_calls == ["first"]
    assert failed == ["first", "second", "third"]
    assert len(notify_calls) == 1


def test_scrape_with_retry_recovers_from_transient_error(monkeypatch):
    import instaloader

    monkeypatch.setattr(run_daily, "TRANSIENT_RETRY_BACKOFF_SECONDS", 0)
    attempts = []

    def fake_scrape(loader, handle):
        attempts.append(handle)
        if len(attempts) < 2:
            raise instaloader.exceptions.ConnectionException("blip")
        return _profile()

    monkeypatch.setattr(run_daily.instagram_scraper, "scrape_profile", fake_scrape)

    result = run_daily._scrape_with_retry(MagicMock(), "h")

    assert len(attempts) == 2
    assert result["profile"]["followers"] == 100


def test_scrape_with_retry_gives_up_after_max_attempts(monkeypatch):
    import instaloader

    import pytest

    monkeypatch.setattr(run_daily, "TRANSIENT_RETRY_BACKOFF_SECONDS", 0)
    attempts = []

    def fake_scrape(loader, handle):
        attempts.append(handle)
        raise instaloader.exceptions.ConnectionException("down")

    monkeypatch.setattr(run_daily.instagram_scraper, "scrape_profile", fake_scrape)

    with pytest.raises(instaloader.exceptions.ConnectionException):
        run_daily._scrape_with_retry(MagicMock(), "h")

    assert len(attempts) == run_daily.TRANSIENT_RETRY_ATTEMPTS


def test_scrape_with_retry_does_not_retry_rate_limit(monkeypatch):
    import instaloader

    import pytest

    attempts = []

    def fake_scrape(loader, handle):
        attempts.append(handle)
        raise instaloader.exceptions.TooManyRequestsException("429")

    monkeypatch.setattr(run_daily.instagram_scraper, "scrape_profile", fake_scrape)

    with pytest.raises(instaloader.exceptions.TooManyRequestsException):
        run_daily._scrape_with_retry(MagicMock(), "h")

    assert len(attempts) == 1


def test_validate_profile_rejects_zero_followers():
    import pytest

    with pytest.raises(ValueError):
        run_daily._validate_profile("h", {"followers": 0}, [])


def test_validate_profile_rejects_missing_followers():
    import pytest

    with pytest.raises(ValueError):
        run_daily._validate_profile("h", {"followers": None}, [])


def test_validate_profile_rejects_large_swing():
    import pytest

    with pytest.raises(ValueError):
        run_daily._validate_profile("h", {"followers": 40}, [{"followers": 100}])


def test_validate_profile_accepts_normal_movement():
    run_daily._validate_profile("h", {"followers": 103}, [{"followers": 100}])


def test_validate_profile_accepts_first_snapshot():
    run_daily._validate_profile("h", {"followers": 5000}, [])


def test_run_instagram_scrape_rejects_anomalous_snapshot(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["h"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)
    _patch_scrape_db(monkeypatch)
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [{"followers": 100000}])
    monkeypatch.setattr(
        run_daily.instagram_scraper, "scrape_profile", lambda loader, handle: _profile(followers=100)
    )

    snapshot_calls = []
    monkeypatch.setattr(run_daily.db, "insert_profile_snapshot", lambda c, i, p: snapshot_calls.append(i))

    with patch("instaloader.Instaloader"):
        failed = run_daily.run_instagram_scrape(MagicMock())

    assert snapshot_calls == []
    assert failed == ["h"]


def test_wait_for_network_returns_true_once_dns_resolves(monkeypatch):
    monkeypatch.setattr(run_daily, "NETWORK_READY_DELAY_SECONDS", 0)
    attempts = []

    def flaky_getaddrinfo(host, port):
        attempts.append(host)
        if len(attempts) < 3:
            raise socket.gaierror("not ready")
        return [("info",)]

    monkeypatch.setattr(run_daily.socket, "getaddrinfo", flaky_getaddrinfo)

    assert run_daily.wait_for_network() is True
    assert len(attempts) == 3


def test_wait_for_network_gives_up_after_attempt_cap(monkeypatch):
    monkeypatch.setattr(run_daily, "NETWORK_READY_DELAY_SECONDS", 0)
    monkeypatch.setattr(run_daily, "NETWORK_READY_ATTEMPTS", 4)
    attempts = []

    def always_fails(host, port):
        attempts.append(host)
        raise socket.gaierror("no dns")

    monkeypatch.setattr(run_daily.socket, "getaddrinfo", always_fails)

    assert run_daily.wait_for_network() is False
    assert len(attempts) == 4


def test_wait_for_network_probes_the_supabase_host(monkeypatch):
    monkeypatch.setattr(run_daily.config, "SUPABASE_URL", "https://project-ref.supabase.co")
    attempts = []
    monkeypatch.setattr(
        run_daily.socket, "getaddrinfo", lambda host, port: attempts.append((host, port)) or [("info",)]
    )

    assert run_daily.wait_for_network() is True
    assert attempts == [("project-ref.supabase.co", 443)]


def test_wait_for_network_survives_non_gaierror_os_errors(monkeypatch):
    """getaddrinfo can raise other OSErrors while an interface is transitioning."""
    monkeypatch.setattr(run_daily, "NETWORK_READY_DELAY_SECONDS", 0)
    attempts = []

    def flaky_getaddrinfo(host, port):
        attempts.append(host)
        if len(attempts) < 2:
            raise OSError("interface going down")
        return [("info",)]

    monkeypatch.setattr(run_daily.socket, "getaddrinfo", flaky_getaddrinfo)

    assert run_daily.wait_for_network() is True


def test_main_exits_without_marking_done_when_network_never_comes_up(tmp_path, monkeypatch):
    monkeypatch.setattr(run_daily.config, "LAST_RUN_FILE", tmp_path / ".last_run")
    monkeypatch.setattr(run_daily, "wait_for_network", lambda: False)
    scrape_calls = []
    monkeypatch.setattr(run_daily, "run_instagram_scrape", lambda c: scrape_calls.append(c))
    notify_calls = []
    monkeypatch.setattr(run_daily, "_notify", lambda title, message: notify_calls.append(title))

    run_daily.main()

    assert scrape_calls == []
    assert not (tmp_path / ".last_run").exists()
    assert notify_calls == ["You First scraper: no network"]


def test_db_with_retry_recovers_from_transient_transport_error(monkeypatch):
    monkeypatch.setattr(run_daily, "TRANSIENT_RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(run_daily, "wait_for_network", lambda: True)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 2:
            raise httpx.ConnectError("nodename nor servname provided")
        return 42

    assert run_daily._db_with_retry("influencer lookup", flaky) == 42
    assert len(calls) == 2


def test_db_with_retry_waits_for_network_before_each_retry(monkeypatch):
    """The laptop sleeps mid-run, so a retry is worthless until DNS is back."""
    monkeypatch.setattr(run_daily, "TRANSIENT_RETRY_BACKOFF_SECONDS", 0)
    waits = []
    monkeypatch.setattr(run_daily, "wait_for_network", lambda: waits.append(1) or True)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise httpx.ConnectError("nodename nor servname provided")
        return "ok"

    assert run_daily._db_with_retry("influencer lookup", flaky) == "ok"
    assert len(waits) == 2


def test_db_with_retry_reraises_after_attempt_cap(monkeypatch):
    monkeypatch.setattr(run_daily, "TRANSIENT_RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(run_daily, "wait_for_network", lambda: True)
    calls = []

    def always_fails():
        calls.append(1)
        raise httpx.ConnectError("nodename nor servname provided")

    with pytest.raises(httpx.ConnectError):
        run_daily._db_with_retry("influencer lookup", always_fails)

    assert len(calls) == run_daily.TRANSIENT_RETRY_ATTEMPTS


def test_db_with_retry_does_not_retry_non_transport_errors(monkeypatch):
    """A missing table or bad query is dead on arrival — burning 90s on it helps nobody."""
    monkeypatch.setattr(run_daily, "TRANSIENT_RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(run_daily, "wait_for_network", lambda: True)
    calls = []

    def api_error():
        calls.append(1)
        raise ValueError("relation does not exist")

    with pytest.raises(ValueError):
        run_daily._db_with_retry("influencer lookup", api_error)

    assert len(calls) == 1


def test_run_instagram_scrape_retries_influencer_lookup_before_failing_handle(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["good_handle"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(run_daily, "TRANSIENT_RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(run_daily, "wait_for_network", lambda: True)
    monkeypatch.setattr(
        run_daily.instagram_scraper,
        "scrape_profile",
        lambda loader, handle: {
            "profile": {"followers": 1, "following": 2, "media_count": 3, "bio": ""},
            "posts": [],
        },
    )

    _patch_scrape_db(monkeypatch)
    lookups = []

    def flaky_lookup(c, h):
        lookups.append(h)
        if len(lookups) < 2:
            raise httpx.ConnectError("nodename nor servname provided")
        return 1

    monkeypatch.setattr(run_daily.db, "get_or_create_influencer", flaky_lookup)

    with patch("instaloader.Instaloader"):
        failed = run_daily.run_instagram_scrape(MagicMock())

    assert failed == []
    assert len(lookups) == 2


def test_run_instagram_scrape_retries_snapshot_history_before_failing_handle(monkeypatch):
    """The 07-16 and 07-21 lost days both died on this call, not the influencer lookup."""
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["good_handle"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(run_daily, "TRANSIENT_RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(run_daily, "wait_for_network", lambda: True)
    monkeypatch.setattr(
        run_daily.instagram_scraper,
        "scrape_profile",
        lambda loader, handle: {
            "profile": {"followers": 1, "following": 2, "media_count": 3, "bio": ""},
            "posts": [],
        },
    )

    _patch_scrape_db(monkeypatch)
    history_calls = []

    def flaky_history(c, i):
        history_calls.append(i)
        if len(history_calls) < 2:
            raise httpx.ReadTimeout("the read operation timed out")
        return []

    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", flaky_history)

    with patch("instaloader.Instaloader"):
        failed = run_daily.run_instagram_scrape(MagicMock())

    assert failed == []
    assert len(history_calls) >= 2


def test_main_does_not_mark_done_when_handles_failed(tmp_path, monkeypatch):
    monkeypatch.setattr(run_daily.config, "LAST_RUN_FILE", tmp_path / ".last_run")
    monkeypatch.setattr(run_daily.db, "get_client", lambda: MagicMock())
    monkeypatch.setattr(run_daily, "wait_for_network", lambda: True)
    monkeypatch.setattr(run_daily, "run_instagram_scrape", lambda c: ["missed_handle"])
    monkeypatch.setattr(run_daily, "run_trend_scrape", lambda c: None)
    monkeypatch.setattr(run_daily, "run_trend_headlines", lambda c: None)
    monkeypatch.setattr(run_daily, "run_recommendations", lambda c: None)
    monkeypatch.setattr(run_daily, "run_roster_briefing", lambda c: None)
    notify_calls = []
    monkeypatch.setattr(run_daily, "_notify", lambda title, message: notify_calls.append(message))

    run_daily.main()

    assert not (tmp_path / ".last_run").exists()
    assert notify_calls == ["Missing: missed_handle"]


def test_main_marks_done_when_all_handles_succeed(tmp_path, monkeypatch):
    monkeypatch.setattr(run_daily.config, "LAST_RUN_FILE", tmp_path / ".last_run")
    monkeypatch.setattr(run_daily.db, "get_client", lambda: MagicMock())
    monkeypatch.setattr(run_daily, "wait_for_network", lambda: True)
    monkeypatch.setattr(run_daily, "run_instagram_scrape", lambda c: [])
    monkeypatch.setattr(run_daily, "run_trend_scrape", lambda c: None)
    monkeypatch.setattr(run_daily, "run_trend_headlines", lambda c: None)
    monkeypatch.setattr(run_daily, "run_recommendations", lambda c: None)
    monkeypatch.setattr(run_daily, "run_roster_briefing", lambda c: None)

    run_daily.main()

    assert (tmp_path / ".last_run").read_text().strip() == date.today().isoformat()
