from unittest.mock import MagicMock, patch

from youfirst_scraper import instagram_scraper
from youfirst_scraper.instagram_scraper import _post_type


def _fake_post(is_video, typename):
    post = MagicMock()
    post.is_video = is_video
    post.typename = typename
    return post


def test_post_type_reel():
    assert _post_type(_fake_post(True, "GraphVideo")) == "reel"


def test_post_type_video_non_reel():
    assert _post_type(_fake_post(True, "GraphOther")) == "video"


def test_post_type_carousel():
    assert _post_type(_fake_post(False, "GraphSidecar")) == "carousel"


def test_post_type_photo():
    assert _post_type(_fake_post(False, "GraphImage")) == "photo"


def test_build_loader_loads_session_when_ig_username_set(monkeypatch):
    monkeypatch.setattr(instagram_scraper.config, "IG_USERNAME", "agencyaccount")

    fake_loader = MagicMock()
    with patch("instaloader.Instaloader", return_value=fake_loader):
        loader = instagram_scraper.build_loader()

    fake_loader.load_session_from_file.assert_called_once_with("agencyaccount")
    assert loader is fake_loader


def test_build_loader_handles_missing_session_gracefully(monkeypatch):
    monkeypatch.setattr(instagram_scraper.config, "IG_USERNAME", "agencyaccount")

    fake_loader = MagicMock()
    fake_loader.load_session_from_file.side_effect = FileNotFoundError()
    with patch("instaloader.Instaloader", return_value=fake_loader):
        loader = instagram_scraper.build_loader()

    assert loader is fake_loader


def test_build_loader_anonymous_when_no_username(monkeypatch):
    monkeypatch.setattr(instagram_scraper.config, "IG_USERNAME", "")

    fake_loader = MagicMock()
    with patch("instaloader.Instaloader", return_value=fake_loader):
        loader = instagram_scraper.build_loader()

    fake_loader.load_session_from_file.assert_not_called()
    assert loader is fake_loader
