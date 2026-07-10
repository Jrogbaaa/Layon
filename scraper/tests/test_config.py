from youfirst_scraper import config


def test_trend_sources_are_live_spanish_feeds():
    assert len(config.TREND_SOURCES) == 3
    assert "newengen.com" not in " ".join(config.TREND_SOURCES)
    assert all(".es" in url or "elpais" in url or "google.com" in url for url in config.TREND_SOURCES)
