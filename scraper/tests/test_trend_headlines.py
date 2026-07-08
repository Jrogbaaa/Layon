import json
from unittest.mock import MagicMock, patch

from youfirst_scraper import trend_headlines


def _snapshots():
    return [
        {"source_url": "https://a.example", "title": "Trend Report A", "content_text": "Reels are up this week."},
        {"source_url": "https://b.example", "title": "Trend Report B", "content_text": "Carousels declining."},
    ]


def _valid_headlines_response():
    return json.dumps(
        {
            "headlines": [
                {"text": {"en": "Reels are surging", "es": "Los reels están subiendo"}, "source_url": "https://a.example"},
                {"text": {"en": "Carousels losing steam", "es": "Los carruseles pierden fuerza"}, "source_url": "https://b.example"},
            ]
        }
    )


def test_build_prompt_includes_each_source_title_url_and_text():
    prompt = trend_headlines.build_prompt(_snapshots())
    assert "Trend Report A" in prompt
    assert "https://a.example" in prompt
    assert "Reels are up this week." in prompt
    assert "Trend Report B" in prompt
    assert "BOTH English and Spanish" in prompt


def test_build_prompt_truncates_long_source_text():
    long_text = "z" * 10000
    snapshots = [{"source_url": "https://a.example", "title": "A", "content_text": long_text}]
    prompt = trend_headlines.build_prompt(snapshots)
    assert prompt.count("z") == trend_headlines.MAX_CHARS_PER_SOURCE


def test_validate_rejects_missing_headlines_key():
    try:
        trend_headlines._validate({"other": "shape"})
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_validate_rejects_empty_list():
    try:
        trend_headlines._validate({"headlines": []})
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_validate_rejects_headline_missing_language():
    try:
        trend_headlines._validate({"headlines": [{"text": {"en": "only english"}, "source_url": None}]})
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_generate_headlines_returns_valid_json():
    fake_response = MagicMock()
    fake_response.text = _valid_headlines_response()
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("youfirst_scraper.trend_headlines.genai.Client", return_value=fake_client):
        result = trend_headlines.generate_headlines(_snapshots())

    parsed = json.loads(result)
    assert parsed["headlines"][0]["text"]["en"] == "Reels are surging"
    fake_client.models.generate_content.assert_called_once()


def test_generate_headlines_normalizes_unknown_source_url_to_none():
    response = json.dumps(
        {"headlines": [{"text": {"en": "e", "es": "s"}, "source_url": "https://not-a-real-source.example"}]}
    )
    fake_response = MagicMock()
    fake_response.text = response
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("youfirst_scraper.trend_headlines.genai.Client", return_value=fake_client):
        result = trend_headlines.generate_headlines(_snapshots())

    parsed = json.loads(result)
    assert parsed["headlines"][0]["source_url"] is None


def test_generate_headlines_retries_once_then_succeeds():
    bad_response = MagicMock()
    bad_response.text = "not json"
    good_response = MagicMock()
    good_response.text = _valid_headlines_response()

    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = [bad_response, good_response]

    with patch("youfirst_scraper.trend_headlines.genai.Client", return_value=fake_client):
        result = trend_headlines.generate_headlines(_snapshots())

    assert json.loads(result)["headlines"][0]["text"]["es"] == "Los reels están subiendo"
    assert fake_client.models.generate_content.call_count == 2


def test_generate_headlines_returns_none_after_two_failed_attempts():
    bad_response = MagicMock()
    bad_response.text = "not json"
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = bad_response

    with patch("youfirst_scraper.trend_headlines.genai.Client", return_value=fake_client):
        result = trend_headlines.generate_headlines(_snapshots())

    assert result is None
    assert fake_client.models.generate_content.call_count == 2
