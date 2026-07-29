from datetime import datetime, timedelta, timezone

from youfirst_scraper import experiment_evaluation as evaluation


def _snapshot(shortcode, posted, interactions, *, hours=168, views=None, post_type="reel", is_ad=False):
    return {
        "shortcode": shortcode,
        "post_type": post_type,
        "likes": interactions - 1,
        "comments": 1,
        "views": views,
        "posted_at": posted.isoformat(),
        "captured_at": (posted + timedelta(hours=hours)).isoformat(),
        "is_ad": is_ad,
    }


def test_closest_mature_snapshot_uses_plus_minus_36_hours_and_later_tie():
    posted = datetime(2026, 7, 1, tzinfo=timezone.utc)
    rows = [
        _snapshot("x", posted, 10, hours=130),  # outside window
        _snapshot("x", posted, 20, hours=167),
        _snapshot("x", posted, 30, hours=169),
        _snapshot("x", posted, 40, hours=205),  # outside window
    ]
    assert evaluation.closest_mature_snapshot(rows, posted)["likes"] == 29


def test_evaluation_prefers_pillar_cohort_with_three_mature_comparisons():
    target_posted = datetime(2026, 7, 20, tzinfo=timezone.utc)
    rows = [_snapshot("target", target_posted, 200, views=2000)]
    tags = {"target": "craft"}
    classifications = {"target": "organic"}
    for i, value in enumerate([80, 100, 120]):
        posted = target_posted - timedelta(days=10 + i)
        code = f"pillar-{i}"
        rows.append(_snapshot(code, posted, value, views=value * 10))
        tags[code] = "craft"
        classifications[code] = "organic"
    rows.append(_snapshot("other", target_posted - timedelta(days=20), 1000, views=10000))
    tags["other"] = "other"
    classifications["other"] = "organic"

    outcome = evaluation.evaluate_experiment(
        {"linked_shortcode": "target", "published_at": target_posted.isoformat()},
        rows,
        tags,
        classifications,
    )

    assert outcome["baseline"]["cohort"] == "format_paid_pillar"
    assert outcome["baseline"]["sample_size"] == 3
    assert outcome["baseline"]["interactions_median"] == 100
    assert outcome["interaction_delta_pct"] == 100.0
    assert outcome["views_delta_pct"] == 100.0
    assert outcome["confidence"] == "directional"
    assert "does not establish causal" in outcome["disclaimer"]


def test_evaluation_falls_back_without_three_pillar_matches_and_never_mixes_paid():
    target_posted = datetime(2026, 7, 20, tzinfo=timezone.utc)
    rows = [_snapshot("target", target_posted, 150)]
    tags = {"target": "craft"}
    classifications = {"target": "organic"}
    for code, pillar, paid, value in [
        ("a", "craft", "organic", 50),
        ("b", "craft", "organic", 100),
        ("c", "other", "organic", 150),
        ("paid", "craft", "paid", 5000),
    ]:
        rows.append(_snapshot(code, target_posted - timedelta(days=10 + len(rows)), value, is_ad=paid == "paid"))
        tags[code] = pillar
        classifications[code] = paid

    outcome = evaluation.evaluate_experiment(
        {"linked_shortcode": "target", "published_at": target_posted.isoformat()}, rows, tags, classifications
    )
    assert outcome["baseline"]["cohort"] == "format_paid"
    assert outcome["baseline"]["sample_size"] == 3
    assert outcome["baseline"]["interactions_median"] == 100


def test_evaluation_requires_target_snapshot_in_window():
    posted = datetime(2026, 7, 1, tzinfo=timezone.utc)
    rows = [_snapshot("target", posted, 100, hours=220)]
    assert evaluation.evaluate_experiment(
        {"linked_shortcode": "target", "published_at": posted.isoformat()}, rows, {}, {}
    ) is None


def test_confidence_thresholds_are_exact():
    assert evaluation.confidence_for_sample(0) == "insufficient"
    assert evaluation.confidence_for_sample(2) == "insufficient"
    assert evaluation.confidence_for_sample(3) == "directional"
    assert evaluation.confidence_for_sample(5) == "directional"
    assert evaluation.confidence_for_sample(6) == "strong"


def test_due_evaluation_is_idempotent_when_database_update_loses_race():
    posted = datetime(2026, 7, 1, tzinfo=timezone.utc)

    class FakeDb:
        def get_due_experiments(self, client, now):
            return [{"id": 1, "influencer_id": 2, "linked_shortcode": "target", "published_at": posted.isoformat()}]

        def get_experiment_post_snapshots(self, client, influencer_id):
            return [_snapshot("target", posted, 100)]

        def get_post_strategy_tags(self, client, influencer_id):
            return []

        def get_post_classifications(self, client, influencer_id):
            return {"target": {"status": "organic"}}

        def mark_experiment_evaluated(self, client, action_id, outcome, now):
            return False

    assert evaluation.evaluate_due_experiments(object(), FakeDb()) == 0


def test_completed_experiment_is_not_rewritten_on_second_daily_pass():
    posted = datetime(2026, 7, 1, tzinfo=timezone.utc)

    class FakeDb:
        due = True
        writes = 0

        def get_due_experiments(self, client, now):
            return [{"id": 1, "influencer_id": 2, "linked_shortcode": "target", "published_at": posted.isoformat()}] if self.due else []

        def get_experiment_post_snapshots(self, client, influencer_id):
            return [_snapshot("target", posted, 100)]

        def get_post_strategy_tags(self, client, influencer_id):
            return []

        def get_post_classifications(self, client, influencer_id):
            return {"target": {"status": "organic"}}

        def mark_experiment_evaluated(self, client, action_id, outcome, now):
            self.writes += 1
            self.due = False
            return True

    fake = FakeDb()
    assert evaluation.evaluate_due_experiments(object(), fake) == 1
    assert evaluation.evaluate_due_experiments(object(), fake) == 0
    assert fake.writes == 1
