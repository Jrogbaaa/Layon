from unittest.mock import MagicMock

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
