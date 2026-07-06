from unittest.mock import patch

from youfirst_scraper.trend_scraper import scrape_trend_source


def test_scrape_trend_source_extracts_title_and_text():
    html = "<html><head><title>Trends 2026</title></head><body><script>ignored()</script><p>Hello world</p></body></html>"

    fake_response = type("Resp", (), {"text": html, "raise_for_status": lambda self: None})()

    with patch("youfirst_scraper.trend_scraper.requests.get", return_value=fake_response):
        result = scrape_trend_source("https://example.com")

    assert result["title"] == "Trends 2026"
    assert "Hello world" in result["content_text"]
    assert "ignored()" not in result["content_text"]
