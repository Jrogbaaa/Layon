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


def test_snapshot_update_is_scoped_to_influencer_and_shortcode():
    client = MagicMock()
    query = MagicMock()
    client.table.return_value.update.return_value = query
    query.eq.return_value = query

    backfill_ads._update_snapshot_classification(client, 7, "shared-code", "paid")

    client.table.assert_called_once_with("post_snapshots")
    client.table.return_value.update.assert_called_once_with({"is_ad": True})
    assert [call.args for call in query.eq.call_args_list] == [
        ("influencer_id", 7),
        ("shortcode", "shared-code"),
    ]
    query.execute.assert_called_once_with()


def test_fetch_post_snapshot_page_uses_stable_range():
    client = MagicMock()
    query = MagicMock()
    client.table.return_value.select.return_value = query
    query.in_.return_value = query
    query.order.return_value = query
    query.range.return_value = query
    query.execute.return_value.data = [{"id": 1001, "shortcode": "a", "influencer_id": 7}]

    rows = backfill_ads._fetch_post_snapshot_page(client, [7, 8], 1000, page_size=500)

    assert rows == [{"id": 1001, "shortcode": "a", "influencer_id": 7}]
    query.in_.assert_called_once_with("influencer_id", [7, 8])
    query.order.assert_called_once_with("id")
    query.range.assert_called_once_with(1000, 1499)


def test_load_posts_to_backfill_paginates_before_deduping(monkeypatch):
    first_page = [
        {"id": i, "influencer_id": 1, "shortcode": f"post-{i}", "is_ad": False}
        for i in range(3)
    ]
    second_page = [
        {"id": 4, "influencer_id": 1, "shortcode": "post-1", "is_ad": True},
        {"id": 5, "influencer_id": 2, "shortcode": "post-x", "is_ad": False},
    ]
    fetches = []

    def fetch(client, active_ids, start, page_size):
        fetches.append((active_ids, start, page_size))
        return first_page if start == 0 else second_page

    monkeypatch.setattr(backfill_ads, "_fetch_post_snapshot_page", fetch)

    posts = backfill_ads._load_posts_to_backfill(MagicMock(), [1, 2], page_size=3)

    assert fetches == [([1, 2], 0, 3), ([1, 2], 3, 3)]
    assert {(post["influencer_id"], post["shortcode"]) for post in posts} == {
        (1, "post-0"),
        (1, "post-1"),
        (1, "post-2"),
        (2, "post-x"),
    }
    assert next(post for post in posts if post["shortcode"] == "post-1")["is_ad"] is True


def _fake_post(shortcode, is_video=False, video_url=None, url="https://example.com/p.jpg"):
    post = MagicMock()
    post.shortcode = shortcode
    post.is_video = is_video
    post.video_url = video_url
    post.url = url
    post.typename = "GraphVideo" if is_video else "GraphImage"
    post.likes = 10
    post._node = {"comments": 2}
    post.caption = f"caption for {shortcode}"
    post.date_utc = MagicMock()
    post.date_utc.isoformat.return_value = "2026-07-01T12:00:00"
    post.caption_mentions = []
    post.tagged_users = []
    post.sponsor_users = []
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


def test_media_urls_by_shortcode_preserves_live_paid_partnership_flag():
    post = _fake_post("a")
    post._node["iphone_struct"] = {
        "is_paid_partnership": True,
        "sponsor_tags": [{"sponsor": {"username": "brand"}}],
        "usertags": None,
    }
    profile = MagicMock()
    profile.get_posts.return_value = iter([post])
    loader = MagicMock()

    from unittest.mock import patch

    with patch("youfirst_scraper.backfill_ads.instaloader.Profile.from_username", return_value=profile):
        found = backfill_ads._media_urls_by_shortcode(loader, "handle", needed={"a"})

    assert found["a"]["is_ad"] is True
    assert found["a"]["sponsor_users"] == ["brand"]


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
