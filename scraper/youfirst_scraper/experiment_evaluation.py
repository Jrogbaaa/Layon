from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import median

REVIEW_DAYS = 7
SNAPSHOT_WINDOW_HOURS = 36


def _dt(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def closest_mature_snapshot(
    snapshots: list[dict], published_at: str | datetime, window_hours: int = SNAPSHOT_WINDOW_HOURS
) -> dict | None:
    target = _dt(published_at) + timedelta(days=REVIEW_DAYS)
    bounded = []
    for snapshot in snapshots:
        captured = _dt(snapshot["captured_at"])
        distance = abs((captured - target).total_seconds())
        if distance <= window_hours * 3600:
            bounded.append((distance, captured, snapshot))
    if not bounded:
        return None
    # When equally close, prefer the later capture so engagement is never understated.
    return min(bounded, key=lambda item: (item[0], -item[1].timestamp()))[2]


def confidence_for_sample(sample_size: int) -> str:
    if sample_size < 3:
        return "insufficient"
    if sample_size <= 5:
        return "directional"
    return "strong"


def _delta_pct(actual: float | int | None, baseline: float | int | None) -> float | None:
    if actual is None or baseline is None or baseline <= 0:
        return None
    return round((actual - baseline) / baseline * 100, 1)


def evaluate_experiment(
    action: dict,
    snapshots: list[dict],
    tags: dict[str, str | None],
    classifications: dict[str, str],
) -> dict | None:
    shortcode = action.get("linked_shortcode")
    published_at = action.get("published_at")
    if not shortcode or not published_at:
        return None

    by_shortcode: dict[str, list[dict]] = {}
    for snapshot in snapshots:
        by_shortcode.setdefault(snapshot["shortcode"], []).append(snapshot)
    target_rows = by_shortcode.get(shortcode, [])
    target_snapshot = closest_mature_snapshot(target_rows, published_at)
    if not target_snapshot:
        return None

    target_meta = max(target_rows, key=lambda row: _dt(row["captured_at"]))
    target_posted = _dt(target_meta["posted_at"])
    target_type = target_meta["post_type"]
    target_paid = classifications.get(
        shortcode, "paid" if target_meta.get("is_ad") else "organic"
    )
    target_pillar = tags.get(shortcode)

    candidates: list[tuple[dict, str | None]] = []
    for candidate_shortcode, rows in by_shortcode.items():
        if candidate_shortcode == shortcode:
            continue
        meta = max(rows, key=lambda row: _dt(row["captured_at"]))
        if _dt(meta["posted_at"]) >= target_posted or meta["post_type"] != target_type:
            continue
        paid = classifications.get(
            candidate_shortcode, "paid" if meta.get("is_ad") else "organic"
        )
        if paid != target_paid:
            continue
        mature = closest_mature_snapshot(rows, meta["posted_at"])
        if mature:
            candidates.append((mature, tags.get(candidate_shortcode)))

    pillar_matches = [item for item in candidates if target_pillar and item[1] == target_pillar]
    if len(pillar_matches) >= 3:
        cohort_rows = [item[0] for item in pillar_matches]
        cohort = "format_paid_pillar"
        cohort_pillar = target_pillar
    else:
        cohort_rows = [item[0] for item in candidates]
        cohort = "format_paid"
        cohort_pillar = None

    interaction_values = [row["likes"] + row["comments"] for row in cohort_rows]
    view_values = [row["views"] for row in cohort_rows if row.get("views") is not None]
    interaction_baseline = median(interaction_values) if interaction_values else None
    views_baseline = median(view_values) if view_values else None
    target_interactions = target_snapshot["likes"] + target_snapshot["comments"]
    sample_size = len(cohort_rows)

    baseline = {
        "interactions_median": interaction_baseline,
        "views_median": views_baseline,
        "sample_size": sample_size,
        "cohort": cohort,
        "post_type": target_type,
        "paid_status": target_paid,
        "pillar": cohort_pillar,
    }
    return {
        "target": {
            "interactions": target_interactions,
            "views": target_snapshot.get("views"),
            "captured_at": target_snapshot["captured_at"],
        },
        "baseline": baseline,
        "interaction_delta_pct": _delta_pct(target_interactions, interaction_baseline),
        "views_delta_pct": _delta_pct(target_snapshot.get("views"), views_baseline),
        "confidence": confidence_for_sample(sample_size),
        "disclaimer": "Directional comparison only; this does not establish causal lift.",
    }


def evaluate_due_experiments(client, db_module, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    completed = 0
    for action in db_module.get_due_experiments(client, now.isoformat()):
        influencer_id = action["influencer_id"]
        raw_classifications = db_module.get_post_classifications(client, influencer_id)
        classifications = (
            {shortcode: row["status"] for shortcode, row in raw_classifications.items()}
            if isinstance(raw_classifications, dict)
            else {row["shortcode"]: row["status"] for row in raw_classifications}
        )
        outcome = evaluate_experiment(
            action,
            db_module.get_experiment_post_snapshots(client, influencer_id),
            {row["shortcode"]: row.get("pillar") for row in db_module.get_post_strategy_tags(client, influencer_id)},
            classifications,
        )
        if outcome and db_module.mark_experiment_evaluated(client, action["id"], outcome, now.isoformat()):
            completed += 1
    return completed
