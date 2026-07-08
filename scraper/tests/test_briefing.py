import json
from unittest.mock import MagicMock, patch

from youfirst_scraper import briefing


def _pattern_facts():
    return {
        "statuses": [
            {"handle": "a", "followers": 1000, "engagement_rate_pct": 5.0, "follower_delta": 10},
            {"handle": "b", "followers": 2000, "engagement_rate_pct": 3.0, "follower_delta": -5},
        ],
        "patterns": [
            {
                "attribute": "topic",
                "value": "values",
                "handles": ["a", "b"],
                "evidence": [
                    {"handle": "a", "shortcode": "a1", "pct": 350.0, "engagement": 4500, "median_engagement": 1000},
                    {"handle": "b", "shortcode": "b1", "pct": 120.0, "engagement": 2200, "median_engagement": 1000},
                ],
            }
        ],
    }


def _valid_briefing_response():
    return json.dumps(
        {
            "summary": {"en": "Roster is stable overall.", "es": "El roster está estable en general."},
            "patterns": [
                {
                    "finding": {"en": "Values content wins for @a and @b", "es": "El contenido de valores gana para @a y @b"},
                    "evidence": "+350% and +120%",
                    "handles": ["a", "b"],
                }
            ],
            "actions": [
                {
                    "handle": "a",
                    "action": {"en": "Post another values carousel", "es": "Publica otro carrusel de valores"},
                    "reason": {"en": "+350% vs median", "es": "+350% vs mediana"},
                    "shortcode": "a1",
                }
            ],
        }
    )


def test_build_prompt_includes_statuses_and_patterns():
    prompt = briefing.build_prompt(_pattern_facts())
    assert "@a" in prompt
    assert "@b" in prompt
    assert 'topic="values"' in prompt
    assert "BOTH English and Spanish" in prompt


def test_build_prompt_handles_no_patterns():
    prompt = briefing.build_prompt({"statuses": [], "patterns": []})
    assert "no influencers with data yet" in prompt
    assert "no cross-influencer content pattern found" in prompt


def test_build_prompt_includes_existing_recommendations_context():
    prompt = briefing.build_prompt(_pattern_facts(), recommendations_by_handle={"a": "Do X"})
    assert "@a: Do X" in prompt


def test_generate_briefing_returns_valid_json():
    fake_response = MagicMock()
    fake_response.text = _valid_briefing_response()
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("youfirst_scraper.briefing.genai.Client", return_value=fake_client):
        result = briefing.generate_briefing(_pattern_facts())

    parsed = json.loads(result)
    assert parsed["summary"]["en"] == "Roster is stable overall."
    assert parsed["actions"][0]["handle"] == "a"
    fake_client.models.generate_content.assert_called_once()


def test_generate_briefing_retries_once_then_succeeds():
    bad_response = MagicMock()
    bad_response.text = "not json"
    good_response = MagicMock()
    good_response.text = _valid_briefing_response()

    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = [bad_response, good_response]

    with patch("youfirst_scraper.briefing.genai.Client", return_value=fake_client):
        result = briefing.generate_briefing(_pattern_facts())

    assert json.loads(result)["summary"]["es"] == "El roster está estable en general."
    assert fake_client.models.generate_content.call_count == 2


def test_generate_briefing_returns_none_after_two_failures():
    bad_response = MagicMock()
    bad_response.text = "not json"
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = bad_response

    with patch("youfirst_scraper.briefing.genai.Client", return_value=fake_client):
        result = briefing.generate_briefing(_pattern_facts())

    assert result is None
    assert fake_client.models.generate_content.call_count == 2


def test_generate_briefing_strips_leading_at_from_handles():
    response_with_at_signs = json.dumps(
        {
            "summary": {"en": "ok", "es": "ok"},
            "patterns": [
                {
                    "finding": {"en": "f", "es": "f"},
                    "evidence": "e",
                    "handles": ["@a", "@b"],
                }
            ],
            "actions": [
                {
                    "handle": "@a",
                    "action": {"en": "do x", "es": "haz x"},
                    "reason": {"en": "r", "es": "r"},
                    "shortcode": None,
                }
            ],
        }
    )
    fake_response = MagicMock()
    fake_response.text = response_with_at_signs
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("youfirst_scraper.briefing.genai.Client", return_value=fake_client):
        result = briefing.generate_briefing(_pattern_facts())

    parsed = json.loads(result)
    assert parsed["patterns"][0]["handles"] == ["a", "b"]
    assert parsed["actions"][0]["handle"] == "a"


def test_generate_briefing_returns_none_when_summary_missing_language():
    fake_response = MagicMock()
    fake_response.text = json.dumps({"summary": {"en": "only english"}, "patterns": [], "actions": []})
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("youfirst_scraper.briefing.genai.Client", return_value=fake_client):
        result = briefing.generate_briefing(_pattern_facts())

    assert result is None
