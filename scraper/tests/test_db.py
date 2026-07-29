import json
from unittest.mock import MagicMock

from youfirst_scraper import db


def test_upload_avatar_uploads_and_returns_public_url():
    client = MagicMock()
    bucket = client.storage.from_.return_value
    bucket.get_public_url.return_value = "https://supabase.example/storage/v1/object/public/avatars/somehandle.jpg"

    result = db.upload_avatar(client, "somehandle", b"fake-image-bytes")

    client.storage.from_.assert_called_with("avatars")
    bucket.upload.assert_called_once()
    args, kwargs = bucket.upload.call_args
    assert args[0] == "somehandle.jpg"
    assert args[1] == b"fake-image-bytes"
    assert kwargs["file_options"]["upsert"] == "true"
    assert result == "https://supabase.example/storage/v1/object/public/avatars/somehandle.jpg"


def test_update_influencer_avatar_updates_by_id():
    client = MagicMock()
    table = client.table.return_value
    update = table.update.return_value

    db.update_influencer_avatar(client, 42, "https://example.com/a.jpg")

    client.table.assert_called_with("influencers")
    table.update.assert_called_with({"avatar_url": "https://example.com/a.jpg"})
    update.eq.assert_called_with("id", 42)
    update.eq.return_value.execute.assert_called_once()


def test_insert_roster_briefing_writes_model_and_content():
    client = MagicMock()
    table = client.table.return_value

    db.insert_roster_briefing(client, "gemini-2.5-flash", '{"summary": {}}')

    client.table.assert_called_with("roster_briefings")
    table.insert.assert_called_once_with({"model": "gemini-2.5-flash", "content": '{"summary": {}}'})


def test_get_latest_roster_briefing_returns_none_when_empty():
    client = MagicMock()
    execute = client.table.return_value.select.return_value.order.return_value.limit.return_value.execute
    execute.return_value.data = []

    assert db.get_latest_roster_briefing(client) is None


def test_get_latest_recommendation_returns_first_row():
    client = MagicMock()
    execute = client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute
    execute.return_value.data = [{"content": "x", "generated_at": "2026-07-01T00:00:00Z"}]

    result = db.get_latest_recommendation(client, 7)

    assert result == {"content": "x", "generated_at": "2026-07-01T00:00:00Z"}


def test_get_top_posts_queries_view_ordered_by_engagement():
    client = MagicMock()
    execute = client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute
    execute.return_value.data = [{"shortcode": "abc", "engagement": 200000}]

    result = db.get_top_posts(client, 7)

    client.table.assert_called_with("top_posts")
    client.table.return_value.select.return_value.eq.assert_called_with("influencer_id", 7)
    client.table.return_value.select.return_value.eq.return_value.order.assert_called_with("engagement", desc=True)
    assert result == [{"shortcode": "abc", "engagement": 200000}]


def test_insert_trend_headlines_writes_model_and_content():
    client = MagicMock()
    table = client.table.return_value

    db.insert_trend_headlines(client, "gemini-2.5-flash", '{"headlines": []}')

    client.table.assert_called_with("trend_headlines")
    table.insert.assert_called_once_with({"model": "gemini-2.5-flash", "content": '{"headlines": []}'})


def test_get_latest_trend_headlines_returns_none_when_empty():
    client = MagicMock()
    execute = client.table.return_value.select.return_value.order.return_value.limit.return_value.execute
    execute.return_value.data = []

    assert db.get_latest_trend_headlines(client) is None


def test_get_latest_trend_headlines_returns_first_row():
    client = MagicMock()
    execute = client.table.return_value.select.return_value.order.return_value.limit.return_value.execute
    execute.return_value.data = [{"content": '{"headlines": []}', "generated_at": "2026-07-01T00:00:00Z", "model": "gemini-2.5-flash"}]

    result = db.get_latest_trend_headlines(client)

    assert result["content"] == '{"headlines": []}'


def test_recommendation_context_attaches_bullet_and_linked_post_referent():
    rows = [
        {
            "recommendation_id": 7,
            "bullet_index": 1,
            "decision": "not_relevant",
            "shared_note": "",
            "linked_shortcode": "POST456",
            "recommendations": {
                "content": json.dumps(
                    {
                        "bullets": [
                            {"text": {"en": "First", "es": "Primera"}, "shortcode": "POST123"},
                            {"text": {"en": "Rejected idea", "es": "Idea rechazada"}, "shortcode": "POST456"},
                        ]
                    }
                )
            },
        }
    ]

    enriched = db._with_recommendation_context(rows)

    assert enriched[0]["recommendation_text"] == {"en": "Rejected idea", "es": "Idea rechazada"}
    assert enriched[0]["recommendation_shortcode"] == "POST456"
    assert enriched[0]["linked_shortcode"] == "POST456"
    assert "recommendations" not in enriched[0]


def test_get_all_post_snapshots_keeps_newest_window_in_chronological_order():
    client = MagicMock()
    query = client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value
    query.execute.return_value.data = [
        {"shortcode": "newest", "captured_at": "2026-07-29T00:00:00Z"},
        {"shortcode": "older", "captured_at": "2026-07-28T00:00:00Z"},
    ]

    rows = db.get_all_post_snapshots(client, 7, limit=500)

    client.table.return_value.select.return_value.eq.return_value.order.assert_called_with(
        "captured_at", desc=True
    )
    assert [row["shortcode"] for row in rows] == ["older", "newest"]


def test_get_stored_post_shortcodes_paginates_complete_history():
    client = MagicMock()
    execute = client.table.return_value.select.return_value.eq.return_value.range.return_value.execute
    first = MagicMock(data=[{"shortcode": "A"}, {"shortcode": "B"}])
    second = MagicMock(data=[{"shortcode": "C"}])
    execute.side_effect = [first, second]

    shortcodes = db.get_stored_post_shortcodes(client, 7, page_size=2)

    assert shortcodes == {"A", "B", "C"}
    ranges = client.table.return_value.select.return_value.eq.return_value.range.call_args_list
    assert [call.args for call in ranges] == [(0, 1), (2, 3)]
