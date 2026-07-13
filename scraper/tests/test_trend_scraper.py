from unittest.mock import patch

from youfirst_scraper.trend_scraper import scrape_trend_source


def _fake_response(text, content_type="text/html"):
    return type(
        "Resp",
        (),
        {"text": text, "headers": {"Content-Type": content_type}, "raise_for_status": lambda self: None},
    )()


def test_scrape_trend_source_extracts_title_and_text():
    html = "<html><head><title>Trends 2026</title></head><body><script>ignored()</script><p>Hello world</p></body></html>"

    fake_response = _fake_response(html)

    with patch("youfirst_scraper.trend_scraper.requests.get", return_value=fake_response):
        result = scrape_trend_source("https://example.com")

    assert result["title"] == "Trends 2026"
    assert "Hello world" in result["content_text"]
    assert "ignored()" not in result["content_text"]


def test_scrape_trend_source_parses_google_trends_rss():
    rss = """<?xml version="1.0"?>
<rss xmlns:ht="https://trends.google.com/trending/rss" version="2.0"><channel>
<title>Daily Search Trends</title>
<item><title>la revuelta</title><ht:approx_traffic>200,000+</ht:approx_traffic>
<ht:news_item><ht:news_item_title>Broncano entrevista a Rosalia en La Revuelta</ht:news_item_title></ht:news_item>
</item></channel></rss>"""

    fake_response = _fake_response(rss, content_type="application/xml")

    with patch("youfirst_scraper.trend_scraper.requests.get", return_value=fake_response):
        result = scrape_trend_source("https://trends.google.com/trending/rss?geo=ES")

    assert result["title"] == "Daily Search Trends"
    assert "la revuelta" in result["content_text"]
    assert "Broncano entrevista a Rosalia" in result["content_text"]


def test_scrape_trend_source_detects_rss_without_content_type_header():
    rss = '<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>' \
          "<item><title>named item</title></item></channel></rss>"

    fake_response = _fake_response(rss, content_type="text/plain")

    with patch("youfirst_scraper.trend_scraper.requests.get", return_value=fake_response):
        result = scrape_trend_source("https://example.com/feed")

    assert result["title"] == "T"
    assert "named item" in result["content_text"]
