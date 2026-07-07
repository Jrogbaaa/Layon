import json
from unittest.mock import MagicMock, patch

from youfirst_scraper import content_analysis


def _post(shortcode, likes, comments, post_type="photo", views=None, video_url=None):
    return {
        "shortcode": shortcode,
        "likes": likes,
        "comments": comments,
        "post_type": post_type,
        "views": views,
        "video_url": video_url,
        "thumbnail_url": f"https://example.com/{shortcode}.jpg",
        "caption": "caption",
    }


def test_select_posts_to_analyze_picks_above_median_engagement():
    posts = [_post("low", 1, 0), _post("high", 100, 20)]
    selected = content_analysis.select_posts_to_analyze(posts, already_analyzed=set())
    assert [p["shortcode"] for p in selected] == ["high"]


def test_select_posts_to_analyze_includes_high_view_reels():
    posts = [
        _post("low_engagement_reel", 1, 0, post_type="reel", views=9000, video_url="v"),
        _post("high_engagement_photo", 100, 20),
    ]
    selected = content_analysis.select_posts_to_analyze(posts, already_analyzed=set())
    shortcodes = {p["shortcode"] for p in selected}
    assert "low_engagement_reel" in shortcodes


def test_select_posts_to_analyze_skips_already_analyzed():
    posts = [_post("a", 100, 20)]
    selected = content_analysis.select_posts_to_analyze(posts, already_analyzed={"a"})
    assert selected == []


def test_select_posts_to_analyze_caps_at_max_per_run():
    posts = [_post(f"p{i}", 100 + i, 0) for i in range(10)]
    selected = content_analysis.select_posts_to_analyze(posts, already_analyzed=set())
    assert len(selected) == content_analysis.MAX_POSTS_PER_RUN


def test_analyze_post_sends_video_and_parses_json_response():
    post = _post("abc", 100, 20, post_type="reel", video_url="https://example.com/abc.mp4")

    fake_response = MagicMock()
    fake_response.text = json.dumps(
        {"summary": "Baila con su perro", "topic": "mascotas", "format": "baile", "hook": "musica viral"}
    )
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    fake_media_response = MagicMock()
    fake_media_response.content = b"fake-bytes"
    fake_media_response.raise_for_status.return_value = None

    with patch("youfirst_scraper.content_analysis.requests.get", return_value=fake_media_response):
        result = content_analysis.analyze_post(fake_client, post)

    assert result["summary"] == "Baila con su perro"
    assert result["analysis"]["topic"] == "mascotas"
    fake_client.models.generate_content.assert_called_once()


def test_analyze_posts_skips_failures_and_continues():
    posts = [_post("bad", 100, 0), _post("good", 100, 0)]

    def fake_analyze(client, post):
        if post["shortcode"] == "bad":
            raise Exception("download failed")
        return {"summary": "ok", "analysis": {"topic": "t", "format": "f", "hook": "h"}}

    with patch("youfirst_scraper.content_analysis.genai.Client", return_value=MagicMock()):
        with patch("youfirst_scraper.content_analysis.analyze_post", side_effect=fake_analyze):
            results = content_analysis.analyze_posts(posts, already_analyzed=set())

    assert len(results) == 1
    assert results[0]["shortcode"] == "good"
