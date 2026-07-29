import json
from unittest.mock import MagicMock, patch

from youfirst_scraper import db, post_strategy


def _posts():
    return [
        {"shortcode": "a", "post_type": "reel", "caption": "Workshop", "likes": 10, "comments": 1},
        {"shortcode": "b", "post_type": "photo", "caption": "Race day", "likes": 8, "comments": 1},
    ]


def test_prompt_uses_only_supplied_stored_evidence_and_active_pillars():
    prompt = post_strategy.build_tagging_prompt(
        ["craft", "race"], _posts(), {"a": {"summary": "Stored summary", "analysis": {"hook": "detail"}}}
    )
    assert "Stored summary" in prompt
    assert "Workshop" in prompt
    assert '"craft"' in prompt
    assert "external data" in prompt


def test_generate_tags_accepts_active_pillars_and_null():
    response = MagicMock()
    response.text = json.dumps({"tags": [{"shortcode": "a", "pillar": "craft"}, {"shortcode": "b", "pillar": None}]})
    client = MagicMock()
    client.models.generate_content.return_value = response
    with patch("youfirst_scraper.post_strategy.genai.Client", return_value=client):
        tags = post_strategy.generate_tags(["craft"], _posts(), {})
    assert tags == [{"shortcode": "a", "pillar": "craft"}, {"shortcode": "b", "pillar": None}]


def test_generate_tags_rejects_removed_or_invented_pillar():
    response = MagicMock()
    response.text = json.dumps({"tags": [{"shortcode": "a", "pillar": "invented"}, {"shortcode": "b", "pillar": None}]})
    client = MagicMock()
    client.models.generate_content.return_value = response
    with patch("youfirst_scraper.post_strategy.genai.Client", return_value=client):
        assert post_strategy.generate_tags(["craft"], _posts(), {}) is None


def test_tag_influencer_preserves_manual_and_retags_stale_automatic(monkeypatch):
    class FakeDb:
        written = None
        flagged = False

        def get_talent_strategy(self, client, influencer_id):
            return {"content_pillars": ["craft"], "updated_at": "new-version"}

        def get_post_strategy_tags(self, client, influencer_id):
            return [
                {"shortcode": "a", "pillar": "removed", "source": "manual", "strategy_updated_at": "old", "removed_pillar": False},
                {"shortcode": "b", "pillar": "race", "source": "automatic", "strategy_updated_at": "old", "removed_pillar": False},
            ]

        def flag_removed_manual_post_tags(self, client, influencer_id, pillars, existing):
            self.flagged = True

        def get_recent_posts(self, client, influencer_id, limit):
            return _posts()

        def get_post_content_map(self, client, influencer_id):
            return {}

        def upsert_automatic_post_strategy_tags(self, client, influencer_id, tags, version, manual_shortcodes):
            self.written = (tags, version, manual_shortcodes)

    fake_db = FakeDb()
    monkeypatch.setattr(post_strategy, "generate_tags", lambda pillars, posts, content: [{"shortcode": "b", "pillar": "craft"}])
    assert post_strategy.tag_influencer(object(), fake_db, 1) == 1
    assert fake_db.flagged is True
    assert fake_db.written == ([{"shortcode": "b", "pillar": "craft"}], "new-version", {"a"})


def test_tag_influencer_clears_stale_automatic_when_strategy_removes_all_pillars(monkeypatch):
    class FakeDb:
        written = None

        def get_talent_strategy(self, client, influencer_id):
            return {"content_pillars": [], "updated_at": "empty-version"}

        def get_post_strategy_tags(self, client, influencer_id):
            return [{"shortcode": "b", "pillar": "old", "source": "automatic", "strategy_updated_at": "old", "removed_pillar": False}]

        def flag_removed_manual_post_tags(self, *args):
            pass

        def get_recent_posts(self, client, influencer_id, limit):
            return _posts()

        def get_post_content_map(self, client, influencer_id):
            raise AssertionError("No Gemini/content call is needed when no pillars remain")

        def upsert_automatic_post_strategy_tags(self, client, influencer_id, tags, version, manual_shortcodes):
            self.written = (tags, version)

    fake = FakeDb()
    monkeypatch.setattr(post_strategy, "generate_tags", lambda *args: (_ for _ in ()).throw(AssertionError("Gemini should not run")))
    assert post_strategy.tag_influencer(object(), fake, 1) == 2
    assert fake.written == ([{"shortcode": "a", "pillar": None}, {"shortcode": "b", "pillar": None}], "empty-version")


def test_manual_unassigned_is_not_flagged_as_removed():
    assert db.manual_pillar_removed(None, []) is False
    assert db.manual_pillar_removed("old", []) is True
    assert db.manual_pillar_removed("craft", ["craft"]) is False
