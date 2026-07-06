from unittest.mock import MagicMock, patch

from youfirst_scraper import recommendations


def test_build_prompt_includes_handle_metrics_and_trends():
    computed_metrics = {
        "engagement_rate_pct": 5.5,
        "follower_delta": 120,
        "format_performance": {"reel": 200.0},
        "posting_cadence_days": 2.5,
    }
    posts = [{"caption": "Beach day"}]
    trends = [{"source_url": "https://example.com", "title": "2026 Trends", "content_text": "Reels are up"}]

    prompt = recommendations.build_prompt("dante_caro", computed_metrics, posts, trends)

    assert "dante_caro" in prompt
    assert "5.5%" in prompt
    assert "Beach day" in prompt
    assert "2026 Trends" in prompt
    assert "Reels are up" in prompt


def test_build_prompt_handles_no_trends_or_posts():
    computed_metrics = {
        "engagement_rate_pct": 0.0,
        "follower_delta": 0,
        "format_performance": {},
        "posting_cadence_days": 0.0,
    }
    prompt = recommendations.build_prompt("handle", computed_metrics, [], [])
    assert "No trend data available." in prompt
    assert "(no recent posts)" in prompt


def test_generate_recommendation_calls_gemini_with_built_prompt():
    profile_snapshots = [{"followers": 1000}, {"followers": 1100}]
    posts = [{"post_type": "reel", "likes": 10, "comments": 1, "posted_at": "2026-07-01T00:00:00Z", "caption": "hi"}]
    trends = []

    fake_response = MagicMock()
    fake_response.text = "Recommendation text"
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("youfirst_scraper.recommendations.genai.Client", return_value=fake_client):
        result = recommendations.generate_recommendation("handle", profile_snapshots, posts, trends)

    assert result == "Recommendation text"
    fake_client.models.generate_content.assert_called_once()
    _, kwargs = fake_client.models.generate_content.call_args
    assert kwargs["model"] == recommendations.GEMINI_MODEL
    assert "handle" in kwargs["contents"]
