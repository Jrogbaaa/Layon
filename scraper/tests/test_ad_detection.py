import json
from unittest.mock import MagicMock, patch

from youfirst_scraper import ad_detection


def _post(shortcode="abc", is_ad=False, caption="caption"):
    return {
        "shortcode": shortcode,
        "is_ad": is_ad,
        "caption": caption,
        "thumbnail_url": f"https://example.com/{shortcode}.jpg",
        "video_url": None,
    }


def _fake_media_response():
    response = MagicMock()
    response.content = b"fake-bytes"
    response.raise_for_status.return_value = None
    return response


def test_detect_ad_short_circuits_platform_declared_paid_partnership():
    client = MagicMock()
    result = ad_detection.detect_ad(client, _post(is_ad=True))
    assert result == "paid"
    client.models.generate_content.assert_not_called()


def test_detect_ad_returns_gemini_classification():
    client = MagicMock()
    response = MagicMock()
    response.text = json.dumps({"reason": "product held up", "classification": "paid"})
    client.models.generate_content.return_value = response

    with patch("youfirst_scraper.ad_detection.requests.get", return_value=_fake_media_response()):
        result = ad_detection.detect_ad(client, _post())

    assert result == "paid"


def test_detect_ad_falls_back_to_unsure_on_invalid_classification_value():
    client = MagicMock()
    response = MagicMock()
    response.text = json.dumps({"reason": "no idea", "classification": "maybe"})
    client.models.generate_content.return_value = response

    with patch("youfirst_scraper.ad_detection.requests.get", return_value=_fake_media_response()):
        result = ad_detection.detect_ad(client, _post())

    assert result == "unsure"


def test_detect_ad_falls_back_to_unsure_on_exception():
    client = MagicMock()
    client.models.generate_content.side_effect = Exception("gemini down")

    with patch("youfirst_scraper.ad_detection.requests.get", return_value=_fake_media_response()):
        result = ad_detection.detect_ad(client, _post())

    assert result == "unsure"


def _fetch_video_post(content_length):
    video_response = _fake_media_response()
    video_response.headers = {"Content-Length": str(content_length)}
    post = {**_post(), "video_url": "https://example.com/abc.mp4"}
    with patch(
        "youfirst_scraper.ad_detection.requests.get",
        side_effect=[video_response, _fake_media_response()],
    ) as fetch:
        _, mime_type = ad_detection._fetch_media_bytes(post)
    return mime_type, fetch


def test_fetch_media_bytes_uses_video_when_within_inline_limit():
    mime_type, fetch = _fetch_video_post(ad_detection.MAX_INLINE_MEDIA_BYTES)
    assert mime_type == "video/mp4"
    assert fetch.call_count == 1


def test_fetch_media_bytes_falls_back_to_thumbnail_when_video_exceeds_inline_limit():
    mime_type, fetch = _fetch_video_post(ad_detection.MAX_INLINE_MEDIA_BYTES + 1)
    assert mime_type == "image/jpeg"
    assert fetch.call_args_list[-1].args[0] == "https://example.com/abc.jpg"


def test_fetch_media_bytes_falls_back_to_thumbnail_when_size_is_unknown():
    mime_type, _ = _fetch_video_post(0)
    assert mime_type == "image/jpeg"


def test_detect_ads_sets_is_ad_per_post():
    posts = [_post("paid_post"), _post("organic_post"), _post("unsure_post")]

    def fake_detect_ad(client, post):
        return {"paid_post": "paid", "organic_post": "organic", "unsure_post": "unsure"}[post["shortcode"]]

    with patch("youfirst_scraper.ad_detection.genai.Client", return_value=MagicMock()):
        with patch("youfirst_scraper.ad_detection.detect_ad", side_effect=fake_detect_ad):
            results = ad_detection.detect_ads(posts)

    by_shortcode = {p["shortcode"]: p for p in results}
    assert by_shortcode["paid_post"]["is_ad"] is True
    assert by_shortcode["organic_post"]["is_ad"] is False
    assert by_shortcode["unsure_post"]["is_ad"] is False


def test_detect_ads_reuses_known_flags_without_calling_gemini():
    posts = [_post("already_known"), _post("brand_new")]

    with patch("youfirst_scraper.ad_detection.genai.Client", return_value=MagicMock()):
        with patch("youfirst_scraper.ad_detection.detect_ad", return_value="organic") as detect:
            results = ad_detection.detect_ads(posts, {"already_known": True})

    by_shortcode = {p["shortcode"]: p for p in results}
    assert by_shortcode["already_known"]["is_ad"] is True
    assert by_shortcode["brand_new"]["is_ad"] is False
    assert [call.args[1]["shortcode"] for call in detect.call_args_list] == ["brand_new"]


def test_detect_ads_skips_gemini_client_when_every_post_is_known():
    with patch("youfirst_scraper.ad_detection.genai.Client") as gemini_client:
        results = ad_detection.detect_ads([_post("known")], {"known": True})

    assert results[0]["is_ad"] is True
    gemini_client.assert_not_called()


def test_detect_ads_empty_list_returns_empty():
    assert ad_detection.detect_ads([]) == []
