import json
from unittest.mock import MagicMock, patch

from youfirst_scraper import recommendations


def _metrics():
    return {
        "engagement_rate_pct": 5.5,
        "follower_delta": 120,
        "format_performance": {"reel": 200.0},
        "posting_cadence_days": 2.5,
    }


def _valid_bullet_response():
    return json.dumps(
        {
            "bullets": [
                {
                    "text": {"en": "Do another reel like this", "es": "Haz otro reel similar"},
                    "reason": {"en": "2x median", "es": "2x mediana"},
                    "shortcode": None,
                }
            ]
        }
    )


def test_build_prompt_includes_handle_and_metrics():
    prompt = recommendations.build_prompt("dante_caro", _metrics(), [])
    assert "dante_caro" in prompt
    assert "5.5%" in prompt


def test_build_prompt_ranks_top_performers_with_content_summary():
    posts = [
        {"shortcode": "low", "post_type": "photo", "likes": 10, "comments": 0, "views": None, "caption": "meh"},
        {
            "shortcode": "high",
            "post_type": "reel",
            "likes": 900,
            "comments": 100,
            "views": 50000,
            "caption": "raw caption",
        },
    ]
    content_map = {"high": {"summary": "Baila una coreografía de moda con su perro", "analysis": {}}}

    prompt = recommendations.build_prompt("handle", _metrics(), posts, content_map=content_map)

    assert "Baila una coreografía de moda con su perro" in prompt
    assert prompt.index("[high]") < prompt.index("[low]")


def test_build_prompt_falls_back_to_caption_when_unanalyzed():
    posts = [{"shortcode": "abc", "post_type": "photo", "likes": 10, "comments": 5, "views": None, "caption": "Beach day"}]
    prompt = recommendations.build_prompt("handle", _metrics(), posts)
    assert "Beach day" in prompt


def test_build_prompt_handles_no_posts():
    prompt = recommendations.build_prompt("handle", _metrics(), [])
    assert "(no recent posts)" in prompt


def test_build_prompt_dedupes_repeated_shortcode_snapshots():
    posts = [
        {"shortcode": "abc", "post_type": "photo", "likes": 10, "comments": 0, "views": None, "caption": "v1"},
        {"shortcode": "abc", "post_type": "photo", "likes": 50, "comments": 5, "views": None, "caption": "v1"},
    ]
    prompt = recommendations.build_prompt("handle", _metrics(), posts)
    assert prompt.count("[abc]") == 1


def test_build_prompt_includes_persona_when_given():
    prompt = recommendations.build_prompt(
        "antonlofer", _metrics(), [], persona="Comedian — adapt trends into sketches"
    )
    assert "Comedian — adapt trends into sketches" in prompt
    assert "off-brand format" in prompt


def test_build_prompt_omits_persona_section_when_none():
    prompt = recommendations.build_prompt("handle", _metrics(), [], persona=None)
    assert "persona/brand" not in prompt


def test_build_prompt_targets_spanish_audience_for_context():
    prompt = recommendations.build_prompt("handle", _metrics(), [])
    assert "Spain / Spanish-speaking" in prompt


def test_build_prompt_requests_bilingual_output():
    prompt = recommendations.build_prompt("handle", _metrics(), [])
    assert "BOTH English and Spanish" in prompt


def test_build_prompt_omits_trend_section_when_no_trend_items():
    prompt = recommendations.build_prompt("handle", _metrics(), [], trend_items=None)
    assert "trending in Spain" not in prompt
    prompt = recommendations.build_prompt("handle", _metrics(), [], trend_items=[])
    assert "trending in Spain" not in prompt


def test_build_prompt_includes_trend_items_and_naming_instruction():
    trend_items = ["La Revuelta's viral interview with Rosalia", "OT 2026 gala shock elimination"]
    prompt = recommendations.build_prompt("handle", _metrics(), [], trend_items=trend_items)
    assert "La Revuelta's viral interview with Rosalia" in prompt
    assert "OT 2026 gala shock elimination" in prompt
    assert "NAME the specific show" in prompt
    assert "vague placeholder" in prompt


def test_build_prompt_includes_highlights():
    highlights = [{"content": "Post abc performed +120% vs their typical post.", "metric": {"type": "outperformance"}}]
    prompt = recommendations.build_prompt("handle", _metrics(), [], highlights=highlights)
    assert "Post abc performed +120%" in prompt
    assert "lead with the standout stat" in prompt


def test_build_prompt_includes_alltime_top_posts_and_ceiling():
    alltime_top_posts = [
        {"shortcode": "big_win", "post_type": "reel", "likes": 190000, "comments": 10000, "views": 2000000, "caption": "huge reel"},
    ]
    prompt = recommendations.build_prompt("maria", _metrics(), [], alltime_top_posts=alltime_top_posts)
    assert "[big_win]" in prompt
    assert "what GOOD looks like for @maria" in prompt
    assert "~200,000 engagement" in prompt


def test_build_prompt_omits_alltime_section_when_none():
    prompt = recommendations.build_prompt("handle", _metrics(), [], alltime_top_posts=None)
    assert "what GOOD looks like" not in prompt


def test_build_prompt_omits_alltime_section_when_empty_list():
    prompt = recommendations.build_prompt("handle", _metrics(), [], alltime_top_posts=[])
    assert "what GOOD looks like" not in prompt


def test_build_prompt_renames_recent_heading_when_alltime_present():
    alltime_top_posts = [{"shortcode": "x", "post_type": "reel", "likes": 100, "comments": 10, "views": None, "caption": "c"}]
    prompt = recommendations.build_prompt("handle", _metrics(), [], alltime_top_posts=alltime_top_posts)
    assert "Recent posts ranked by engagement" in prompt


def test_build_prompt_requests_bullet_json_shape():
    prompt = recommendations.build_prompt("handle", _metrics(), [])
    assert '"bullets"' in prompt
    assert '"shortcode"' in prompt
    assert '"en"' in prompt
    assert '"es"' in prompt


def test_generate_recommendation_calls_gemini_and_returns_valid_json():
    profile_snapshots = [{"followers": 1000}, {"followers": 1100}]
    posts = [{"shortcode": "xyz", "post_type": "reel", "likes": 10, "comments": 1, "posted_at": "2026-07-01T00:00:00Z", "caption": "hi"}]

    fake_response = MagicMock()
    fake_response.text = _valid_bullet_response()
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("youfirst_scraper.recommendations.genai.Client", return_value=fake_client):
        result = recommendations.generate_recommendation("handle", profile_snapshots, posts)

    parsed = json.loads(result)
    assert parsed["bullets"][0]["text"]["es"] == "Haz otro reel similar"
    assert parsed["bullets"][0]["text"]["en"] == "Do another reel like this"
    fake_client.models.generate_content.assert_called_once()
    _, kwargs = fake_client.models.generate_content.call_args
    assert kwargs["model"] == recommendations.GEMINI_MODEL
    assert "handle" in kwargs["contents"]


def test_generate_recommendation_passes_trend_items_into_prompt():
    profile_snapshots = [{"followers": 1000}]
    posts = []

    fake_response = MagicMock()
    fake_response.text = _valid_bullet_response()
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("youfirst_scraper.recommendations.genai.Client", return_value=fake_client):
        recommendations.generate_recommendation(
            "handle", profile_snapshots, posts, trend_items=["La Revuelta's viral interview with Rosalia"]
        )

    _, kwargs = fake_client.models.generate_content.call_args
    assert "La Revuelta's viral interview with Rosalia" in kwargs["contents"]


def test_generate_recommendation_retries_once_on_malformed_json_then_succeeds():
    profile_snapshots = [{"followers": 1000}]
    posts = []

    bad_response = MagicMock()
    bad_response.text = "not json at all"
    good_response = MagicMock()
    good_response.text = _valid_bullet_response()

    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = [bad_response, good_response]

    with patch("youfirst_scraper.recommendations.genai.Client", return_value=fake_client):
        result = recommendations.generate_recommendation("handle", profile_snapshots, posts)

    assert json.loads(result)["bullets"][0]["text"]["en"] == "Do another reel like this"
    assert fake_client.models.generate_content.call_count == 2


def test_generate_recommendation_returns_none_after_two_failed_attempts():
    profile_snapshots = [{"followers": 1000}]
    posts = []

    bad_response = MagicMock()
    bad_response.text = "not json at all"

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = bad_response

    with patch("youfirst_scraper.recommendations.genai.Client", return_value=fake_client):
        result = recommendations.generate_recommendation("handle", profile_snapshots, posts)

    assert result is None
    assert fake_client.models.generate_content.call_count == 2


def test_generate_recommendation_returns_none_when_bullets_key_missing():
    profile_snapshots = [{"followers": 1000}]
    posts = []

    fake_response = MagicMock()
    fake_response.text = json.dumps({"other": "shape"})
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("youfirst_scraper.recommendations.genai.Client", return_value=fake_client):
        result = recommendations.generate_recommendation("handle", profile_snapshots, posts)

    assert result is None


def test_generate_recommendation_returns_none_when_bullet_missing_language():
    profile_snapshots = [{"followers": 1000}]
    posts = []

    fake_response = MagicMock()
    fake_response.text = json.dumps({"bullets": [{"text": {"en": "only english"}, "reason": {"en": "r"}}]})
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("youfirst_scraper.recommendations.genai.Client", return_value=fake_client):
        result = recommendations.generate_recommendation("handle", profile_snapshots, posts)

    assert result is None
