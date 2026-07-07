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
