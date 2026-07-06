from youfirst_scraper import config


def test_trend_sources_are_spanish_market_and_count_four():
    assert len(config.TREND_SOURCES) == 4
    assert "newengen.com" not in " ".join(config.TREND_SOURCES)
