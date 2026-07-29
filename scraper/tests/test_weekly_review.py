import json
from datetime import datetime, timezone

import pytest

from youfirst_scraper import weekly_review


@pytest.mark.parametrize(
    ("now", "start", "end"),
    [
        (datetime(2026, 7, 27, 0, 1, tzinfo=timezone.utc), "2026-07-27", "2026-08-02"),
        (datetime(2026, 8, 2, 21, 59, tzinfo=timezone.utc), "2026-07-27", "2026-08-02"),
        (datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc), "2025-12-29", "2026-01-04"),
        (datetime(2026, 3, 29, 21, 30, tzinfo=timezone.utc), "2026-03-23", "2026-03-29"),
        (datetime(2026, 3, 29, 22, 30, tzinfo=timezone.utc), "2026-03-30", "2026-04-05"),
    ],
)
def test_madrid_week_boundaries(now, start, end):
    actual_start, actual_end = weekly_review.madrid_week(now)
    assert actual_start.isoformat() == start
    assert actual_end.isoformat() == end


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("development_formats", ["reel"]),
        ("commercial_direction", "Selective partnerships"),
        ("posting_constraints", "Weekdays only"),
    ],
)
def test_strategy_status_counts_every_substantive_field(field, value):
    strategy = {field: value, "reviewed_at": "2026-07-28T00:00:00Z"}

    assert weekly_review._strategy_status(
        strategy,
        datetime(2026, 7, 29, tzinfo=timezone.utc).date(),
        datetime(2026, 7, 29, tzinfo=timezone.utc),
    ) == "current"


def _evidence():
    return {
        "period_start": "2026-07-27",
        "period_end": "2026-08-02",
        "talents": [{"handle": "talent", "metrics": ["4.5% engagement rate"]}],
        "allowed_handles": ["talent"],
        "allowed_metrics": ["4.5% engagement rate", "+25.0% interactions vs baseline"],
        "allowed_shortcodes": ["abc"],
        "stale_handles": ["talent"],
        "evidence_by_handle": {"talent": {"metrics": ["4.5% engagement rate", "+25.0% interactions vs baseline"], "shortcodes": ["abc"]}},
        "eligible_due": [],
        "eligible_evaluated": [{"handle": "talent", "shortcode": "abc"}],
        "win_evidence": [{"handle": "talent", "shortcode": "abc", "metric": "4.5% engagement rate"}],
        "risk_handles": ["talent"],
    }


def _payload():
    item = {"title": {"en": "Priority", "es": "Prioridad"}, "handles": ["talent"], "metric": "4.5% engagement rate", "shortcode": "abc"}
    return {
        "top_priorities": [item],
        "strongest_creative_win": item,
        "primary_risk": {**item, "shortcode": None},
        "experiments": {"due": [], "recently_evaluated": [{**item, "metric": "+25.0% interactions vs baseline"}]},
        "stale_strategies": [{"handle": "talent", "status": {"en": "Review due", "es": "Revisión pendiente"}}],
        "suggested_conversations": [{"handle": "talent", "topic": {"en": "Craft", "es": "Oficio"}, "reason": {"en": "Evidence", "es": "Evidencia"}, "metric": "4.5% engagement rate", "shortcode": "abc"}],
    }


def test_payload_validation_accepts_all_required_bilingual_sections():
    weekly_review.validate_payload(_payload(), _evidence())


def test_payload_validation_rejects_invented_metric_handle_and_shortcode():
    for field, value in [("metric", "invented"), ("shortcode", "fake")]:
        payload = _payload()
        payload["top_priorities"][0] = {**payload["top_priorities"][0], field: value}
        with pytest.raises(ValueError):
            weekly_review.validate_payload(payload, _evidence())
    payload = _payload()
    payload["top_priorities"][0] = {**payload["top_priorities"][0], "handles": ["unknown"]}
    with pytest.raises(ValueError):
        weekly_review.validate_payload(payload, _evidence())


def test_payload_validation_rejects_wrong_priority_count_and_section_membership():
    payload = _payload()
    payload["top_priorities"] = []
    with pytest.raises(ValueError, match="exactly 1"):
        weekly_review.validate_payload(payload, _evidence())

    payload = _payload()
    evidence = _evidence()
    evidence["stale_handles"] = []
    with pytest.raises(ValueError, match="stale strategy"):
        weekly_review.validate_payload(payload, evidence)

    payload = _payload()
    payload["experiments"]["due"] = [payload["top_priorities"][0]]
    with pytest.raises(ValueError, match="eligible evidence"):
        weekly_review.validate_payload(payload, _evidence())


def test_payload_validation_rejects_cross_talent_evidence_and_omitted_sections():
    evidence = _evidence()
    evidence["allowed_handles"].append("other")
    evidence["evidence_by_handle"]["other"] = {"metrics": ["9.9% engagement rate"], "shortcodes": ["other-post"]}
    evidence["allowed_metrics"].append("9.9% engagement rate")
    evidence["allowed_shortcodes"].append("other-post")
    payload = _payload()
    payload["top_priorities"][0] = {**payload["top_priorities"][0], "metric": "9.9% engagement rate", "shortcode": "other-post"}
    payload["top_priorities"].append({**payload["top_priorities"][0], "handles": ["other"]})
    with pytest.raises(ValueError, match="misattributes"):
        weekly_review.validate_payload(payload, evidence)

    for section in ("stale_strategies", "suggested_conversations"):
        payload = _payload()
        payload[section] = []
        with pytest.raises(ValueError):
            weekly_review.validate_payload(payload, _evidence())

    for section in ("strongest_creative_win", "primary_risk"):
        payload = _payload()
        payload[section] = None
        with pytest.raises(ValueError):
            weekly_review.validate_payload(payload, _evidence())

    payload = _payload()
    payload["experiments"]["recently_evaluated"] = []
    with pytest.raises(ValueError, match="eligible evidence"):
        weekly_review.validate_payload(payload, _evidence())


def test_build_evidence_shapes_unresolved_experiments_strategy_and_allowed_values():
    now = datetime(2026, 7, 29, 12, tzinfo=timezone.utc)
    evidence = weekly_review.build_evidence(
        [{"id": 1, "handle": "talent"}],
        {1: [{"followers": 1000, "following": 10, "media_count": 5, "captured_at": "2026-07-28T00:00:00Z"}]},
        {1: [{"shortcode": "abc", "post_type": "reel", "likes": 100, "comments": 10, "views": 1000, "caption": "x", "posted_at": "2026-07-20T00:00:00Z", "captured_at": "2026-07-28T00:00:00Z", "is_ad": False}]},
        {1: [{"content": "Cadence fell", "metric": {"severity": "warning"}, "captured_at": "2026-07-28T00:00:00Z"}]},
        {1: None},
        {1: {"id": 9, "content": json.dumps({"bullets": [{"text": {"en": "Do it", "es": "Hazlo"}, "shortcode": "abc"}]})}},
        {1: [{"recommendation_id": 8, "bullet_index": 0, "experiment_status": "published", "linked_shortcode": "abc", "review_at": "2026-07-28T00:00:00Z", "outcome": None, "evaluated_at": None}]},
        now,
    )
    talent = evidence["talents"][0]
    assert talent["strategy_status"] == "missing"
    assert talent["unresolved_recommendations"][0]["shortcode"] == "abc"
    assert len(talent["due_experiments"]) == 1
    assert "talent" in evidence["allowed_handles"]
    assert "abc" in evidence["allowed_shortcodes"]
    assert "1,000 followers" in evidence["evidence_by_handle"]["talent"]["metrics"]
    assert evidence["stale_handles"] == ["talent"]
    assert evidence["eligible_due"] == [{"handle": "talent", "shortcode": "abc"}]


def test_build_evidence_does_not_trust_recommendation_shortcode_without_stored_post():
    evidence = weekly_review.build_evidence(
        [{"id": 1, "handle": "talent"}],
        {1: []},
        {1: [{"shortcode": "REAL123", "post_type": "reel", "likes": 10, "comments": 1, "views": 100, "caption": "x", "posted_at": "2026-07-20T00:00:00Z", "captured_at": "2026-07-28T00:00:00Z", "is_ad": False}]},
        {1: []},
        {1: None},
        {1: {"id": 9, "content": json.dumps({"bullets": [{"text": {"en": "Do it", "es": "Hazlo"}, "shortcode": "INVENTED999"}]})}},
        {1: []},
        datetime(2026, 7, 29, tzinfo=timezone.utc),
    )

    assert evidence["talents"][0]["unresolved_recommendations"][0]["shortcode"] is None
    assert "INVENTED999" not in evidence["allowed_shortcodes"]
    assert "INVENTED999" not in evidence["evidence_by_handle"]["talent"]["shortcodes"]


def test_recent_evaluation_uses_madrid_date_at_monday_boundary():
    evidence = weekly_review.build_evidence(
        [{"id": 1, "handle": "talent"}],
        {1: []},
        {1: [{"shortcode": "abc", "post_type": "reel", "likes": 1, "comments": 0, "views": 10, "caption": "x", "posted_at": "2026-07-20T00:00:00Z", "captured_at": "2026-07-27T00:00:00Z", "is_ad": False}]},
        {1: []},
        {1: None},
        {1: None},
        {1: [{"recommendation_id": 1, "bullet_index": 0, "experiment_status": "evaluated", "linked_shortcode": "abc", "review_at": None, "outcome": {"interaction_delta_pct": 12.0}, "evaluated_at": "2026-07-26T22:30:00Z"}]},
        datetime(2026, 7, 27, 12, tzinfo=timezone.utc),
    )

    assert len(evidence["talents"][0]["recently_evaluated"]) == 1
    assert evidence["eligible_evaluated"] == [{"handle": "talent", "shortcode": "abc"}]
