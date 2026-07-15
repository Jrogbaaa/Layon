from unittest.mock import MagicMock

from youfirst_scraper import backfill_ads


def test_dedupe_posts_keeps_one_row_per_influencer_and_shortcode():
    rows = [
        {"influencer_id": 1, "shortcode": "a", "is_ad": False},
        {"influencer_id": 1, "shortcode": "a", "is_ad": True},  # later capture, same post
        {"influencer_id": 1, "shortcode": "b", "is_ad": False},
        {"influencer_id": 2, "shortcode": "a", "is_ad": False},  # different influencer, same shortcode
    ]

    deduped = backfill_ads._dedupe_posts(rows)

    keys = {(row["influencer_id"], row["shortcode"]) for row in deduped}
    assert keys == {(1, "a"), (1, "b"), (2, "a")}
    assert len(deduped) == 3


def test_dedupe_posts_empty_list():
    assert backfill_ads._dedupe_posts([]) == []


def _fake_post(shortcode, is_video=False, video_url=None, url="https://example.com/p.jpg"):
    post = MagicMock()
    post.shortcode = shortcode
    post.is_video = is_video
    post.video_url = video_url
    post.url = url
    return post


def test_media_urls_by_shortcode_stops_early_once_all_needed_found():
    posts = [_fake_post("a"), _fake_post("b"), _fake_post("c")]
    profile = MagicMock()
    profile.get_posts.return_value = iter(posts)
    loader = MagicMock()

    from unittest.mock import patch

    with patch("youfirst_scraper.backfill_ads.instaloader.Profile.from_username", return_value=profile):
        found = backfill_ads._media_urls_by_shortcode(loader, "handle", needed={"a", "b"})

    assert set(found.keys()) == {"a", "b"}
    # "c" was never consumed because iteration stopped once "a" and "b" were found.
    assert next(profile.get_posts.return_value, None) is not None


def test_media_urls_by_shortcode_returns_video_url_for_video_posts():
    posts = [_fake_post("a", is_video=True, video_url="https://example.com/a.mp4")]
    profile = MagicMock()
    profile.get_posts.return_value = iter(posts)
    loader = MagicMock()

    from unittest.mock import patch

    with patch("youfirst_scraper.backfill_ads.instaloader.Profile.from_username", return_value=profile):
        found = backfill_ads._media_urls_by_shortcode(loader, "handle", needed={"a"})

    assert found["a"]["video_url"] == "https://example.com/a.mp4"


def test_media_urls_by_shortcode_gives_up_after_safety_cap():
    # None of these match "needed", so the loop should stop at len(needed) + 50
    # instead of exhausting a long profile history.
    posts = [_fake_post(str(i)) for i in range(200)]
    profile = MagicMock()
    profile.get_posts.return_value = iter(posts)
    loader = MagicMock()

    from unittest.mock import patch

    with patch("youfirst_scraper.backfill_ads.instaloader.Profile.from_username", return_value=profile):
        found = backfill_ads._media_urls_by_shortcode(loader, "handle", needed={"missing"})

    assert found == {}
    # Only checked+ len(needed)+50 = 51 posts before giving up.
    remaining = list(profile.get_posts.return_value)
    assert len(remaining) == len(posts) - 51
