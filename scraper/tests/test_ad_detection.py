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


def test_detect_ads_sets_is_ad_and_ad_classification_per_post():
    posts = [_post("paid_post"), _post("organic_post"), _post("unsure_post")]

    def fake_detect_ad(client, post):
        return {"paid_post": "paid", "organic_post": "organic", "unsure_post": "unsure"}[post["shortcode"]]

    with patch("youfirst_scraper.ad_detection.genai.Client", return_value=MagicMock()):
        with patch("youfirst_scraper.ad_detection.detect_ad", side_effect=fake_detect_ad):
            results = ad_detection.detect_ads(posts)

    by_shortcode = {p["shortcode"]: p for p in results}
    assert by_shortcode["paid_post"]["is_ad"] is True
    assert by_shortcode["paid_post"]["ad_classification"] == "paid"
    assert by_shortcode["organic_post"]["is_ad"] is False
    assert by_shortcode["unsure_post"]["is_ad"] is False
    assert by_shortcode["unsure_post"]["ad_classification"] == "unsure"


def test_detect_ads_empty_list_returns_empty():
    assert ad_detection.detect_ads([]) == []
