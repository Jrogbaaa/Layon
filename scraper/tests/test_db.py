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
