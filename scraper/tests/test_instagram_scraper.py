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


def test_view_count_for_video():
    post = MagicMock()
    post.is_video = True
    post._node = {"video_view_count": 12345}
    assert instagram_scraper._view_count(post) == 12345


def test_view_count_reads_play_count_fallback():
    post = MagicMock()
    post.is_video = True
    post._node = {"play_count": 999}
    assert instagram_scraper._view_count(post) == 999


def test_view_count_none_for_photo():
    post = MagicMock()
    post.is_video = False
    assert instagram_scraper._view_count(post) is None


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


def test_scrape_profile_includes_avatar_source_url(monkeypatch):
    fake_profile = MagicMock()
    fake_profile.followers = 100
    fake_profile.followees = 10
    fake_profile.mediacount = 5
    fake_profile.biography = "bio"
    fake_profile.profile_pic_url = "https://instagram.example/pic.jpg"
    fake_profile.get_posts.return_value = []

    monkeypatch.setattr(
        instagram_scraper.instaloader.Profile, "from_username", lambda ctx, handle: fake_profile
    )

    result = instagram_scraper.scrape_profile(MagicMock(), "somehandle")

    assert result["profile"]["avatar_source_url"] == "https://instagram.example/pic.jpg"


def test_comment_count_reads_timeline_key():
    post = MagicMock()
    post._node = {"comments": 42}
    assert instagram_scraper._comment_count(post) == 42


def test_comment_count_raises_when_key_missing():
    import pytest

    post = MagicMock()
    post.shortcode = "abc123"
    post._node = {}
    with pytest.raises(KeyError):
        instagram_scraper._comment_count(post)


def test_view_count_none_and_warns_for_video_without_keys(caplog):
    post = MagicMock()
    post.is_video = True
    post.shortcode = "abc123"
    post._node = {}
    with caplog.at_level("WARNING"):
        assert instagram_scraper._view_count(post) is None
    assert "No view-count key" in caplog.text
