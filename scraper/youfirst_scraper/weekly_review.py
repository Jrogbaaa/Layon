import json
import logging
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from google import genai
from google.genai import types

from . import config, metrics

logger = logging.getLogger(__name__)

MADRID = ZoneInfo("Europe/Madrid")
GEMINI_MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 2


def madrid_week(now: datetime | None = None) -> tuple[date, date]:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    local_date = now.astimezone(MADRID).date()
    start = local_date - timedelta(days=local_date.weekday())
    return start, start + timedelta(days=6)


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _strategy_status(strategy: dict | None, today: date, now: datetime) -> str:
    if not strategy or not any(
        strategy.get(key)
        for key in (
            "current_objective",
            "target_audience",
            "content_pillars",
            "development_formats",
            "tone",
            "guardrails",
            "commercial_direction",
            "posting_constraints",
        )
    ):
        return "missing"
    horizon = strategy.get("horizon")
    if horizon and horizon < today.isoformat():
        return "expired"
    reviewed = _parse_time(strategy.get("reviewed_at"))
    if not reviewed or now - reviewed.astimezone(timezone.utc) > timedelta(days=90):
        return "review_due"
    return "current"


def _recommendation_bullets(row: dict | None) -> list[dict]:
    if not row:
        return []
    try:
        parsed = json.loads(row["content"]) if isinstance(row["content"], str) else row["content"]
        return parsed["bullets"] if isinstance(parsed.get("bullets"), list) else []
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def build_evidence(
    influencers: list[dict],
    profiles_by_id: dict[int, list[dict]],
    posts_by_id: dict[int, list[dict]],
    highlights_by_id: dict[int, list[dict]],
    strategies_by_id: dict[int, dict | None],
    recommendations_by_id: dict[int, dict | None],
    actions_by_id: dict[int, list[dict]],
    now: datetime | None = None,
    stored_shortcodes_by_id: dict[int, set[str]] | None = None,
) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    start, end = madrid_week(now)
    talents = []
    allowed_metrics: set[str] = set()
    allowed_shortcodes: set[str] = set()
    stale_handles: set[str] = set()
    evidence_by_handle: dict[str, dict[str, list[str]]] = {}
    eligible_due: list[dict[str, str | None]] = []
    eligible_evaluated: list[dict[str, str | None]] = []
    win_evidence: list[dict[str, str]] = []
    risk_handles: set[str] = set()

    for influencer in influencers:
        influencer_id = influencer["id"]
        handle = influencer["handle"]
        profiles = profiles_by_id.get(influencer_id, [])
        posts = posts_by_id.get(influencer_id, [])
        stored_shortcodes = (
            {post["shortcode"] for post in posts}
            if stored_shortcodes_by_id is None
            else stored_shortcodes_by_id.get(influencer_id, set())
        )
        computed = metrics.compute_metrics(profiles, posts) if profiles else {
            "engagement_rate_pct": 0,
            "follower_delta": 0,
        }
        metric_strings = [
            f"{computed['engagement_rate_pct']}% engagement rate",
            f"{computed['follower_delta']:+d} followers since prior snapshot",
        ]
        talent_shortcodes: set[str] = set()
        if profiles:
            metric_strings.append(f"{profiles[-1]['followers']:,} followers")
        talent_metrics = set(metric_strings)
        allowed_metrics.update(metric_strings)

        latest_recommendation = recommendations_by_id.get(influencer_id)
        recommendation_id = latest_recommendation.get("id") if latest_recommendation else None
        actions = actions_by_id.get(influencer_id, [])
        answered = {
            action["bullet_index"]
            for action in actions
            if action.get("recommendation_id") == recommendation_id
        }
        unresolved = []
        for index, bullet in enumerate(_recommendation_bullets(latest_recommendation)):
            if index in answered:
                continue
            candidate_shortcode = bullet.get("shortcode")
            shortcode = candidate_shortcode if candidate_shortcode in stored_shortcodes else None
            if shortcode:
                allowed_shortcodes.add(shortcode)
                talent_shortcodes.add(shortcode)
            text = bullet.get("text", {})
            unresolved.append(
                {
                    "index": index,
                    "text": text.get("en") if isinstance(text, dict) else str(text),
                    "shortcode": shortcode,
                }
            )

        active = []
        due = []
        evaluated = []
        for action in actions:
            status = action.get("experiment_status")
            candidate_shortcode = action.get("linked_shortcode")
            shortcode = candidate_shortcode if candidate_shortcode in stored_shortcodes else None
            if shortcode:
                allowed_shortcodes.add(shortcode)
                talent_shortcodes.add(shortcode)
            summary = {
                "status": status,
                "shortcode": shortcode,
                "review_at": action.get("review_at"),
                "outcome": action.get("outcome"),
            }
            if status in ("planned", "published"):
                active.append(summary)
            review_at = _parse_time(action.get("review_at"))
            if status == "published" and review_at and review_at <= now:
                due.append(summary)
                eligible_due.append({"handle": handle, "shortcode": shortcode})
            evaluated_at = _parse_time(action.get("evaluated_at"))
            if (
                status == "evaluated"
                and evaluated_at
                and start <= evaluated_at.astimezone(MADRID).date() <= end
            ):
                evaluated.append(summary)
                eligible_evaluated.append({"handle": handle, "shortcode": shortcode})
                outcome = action.get("outcome") or {}
                delta = outcome.get("interaction_delta_pct")
                if delta is not None:
                    outcome_metric = f"{delta:+.1f}% interactions vs baseline"
                    allowed_metrics.add(outcome_metric)
                    talent_metrics.add(outcome_metric)

        unique_posts = {}
        for post in posts:
            code = post["shortcode"]
            engagement = post["likes"] + post["comments"]
            if code not in unique_posts or engagement > unique_posts[code]["engagement"]:
                unique_posts[code] = {"shortcode": code, "engagement": engagement}
        strongest_post = max(unique_posts.values(), key=lambda item: item["engagement"], default=None)
        if strongest_post:
            allowed_shortcodes.add(strongest_post["shortcode"])
            talent_shortcodes.add(strongest_post["shortcode"])
            strongest_post["metric"] = f"{strongest_post['engagement']:,} interactions"
            allowed_metrics.add(strongest_post["metric"])
            talent_metrics.add(strongest_post["metric"])
            win_evidence.append(
                {
                    "handle": handle,
                    "shortcode": strongest_post["shortcode"],
                    "metric": strongest_post["metric"],
                }
            )

        warnings = [
            {"content": row["content"], "metric": row.get("metric", {})}
            for row in highlights_by_id.get(influencer_id, [])
            if row.get("metric", {}).get("severity") == "warning"
        ]
        strategy_status = _strategy_status(
            strategies_by_id.get(influencer_id), now.astimezone(MADRID).date(), now
        )
        if strategy_status != "current":
            stale_handles.add(handle)
        if strategy_status != "current" or warnings:
            risk_handles.add(handle)
        evidence_by_handle[handle] = {
            "metrics": sorted(talent_metrics),
            "shortcodes": sorted(talent_shortcodes),
        }
        talents.append(
            {
                "handle": handle,
                "metrics": metric_strings,
                "strategy_status": strategy_status,
                "warnings": warnings,
                "unresolved_recommendations": unresolved,
                "active_experiments": active,
                "due_experiments": due,
                "recently_evaluated": evaluated,
                "strongest_post": strongest_post,
            }
        )

    return {
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "talents": talents,
        "allowed_handles": [item["handle"] for item in talents],
        "allowed_metrics": sorted(allowed_metrics),
        "allowed_shortcodes": sorted(allowed_shortcodes),
        "stale_handles": sorted(stale_handles),
        "evidence_by_handle": evidence_by_handle,
        "eligible_due": eligible_due,
        "eligible_evaluated": eligible_evaluated,
        "win_evidence": win_evidence,
        "risk_handles": sorted(risk_handles),
    }


def build_prompt(evidence: dict) -> str:
    return f"""You are preparing the shared weekly coaching review for a talent agency.
Use ONLY the supplied evidence. Do not invent handles, metrics, posts, links, causes, or private
context. Keep experiment claims directional, never causal. Write all narrative in English and
Spanish. Use exact supplied metric strings and shortcode values or null.

Evidence for Madrid week {evidence['period_start']} through {evidence['period_end']}:
{json.dumps(evidence['talents'], ensure_ascii=False, default=str)}

Return only JSON in this exact shape:
{{"top_priorities":[{{"title":{{"en":"...","es":"..."}},"handles":["handle"],"metric":"exact supplied metric or null","shortcode":"supplied shortcode or null"}}],"strongest_creative_win":{{"title":{{"en":"...","es":"..."}},"handles":["handle"],"metric":"exact supplied metric or null","shortcode":"supplied shortcode or null"}},"primary_risk":{{"title":{{"en":"...","es":"..."}},"handles":["handle"],"metric":"exact supplied metric or null","shortcode":null}},"experiments":{{"due":[],"recently_evaluated":[]}},"stale_strategies":[{{"handle":"handle","status":{{"en":"...","es":"..."}}}}],"suggested_conversations":[{{"handle":"handle","topic":{{"en":"...","es":"..."}},"reason":{{"en":"...","es":"..."}},"metric":"exact supplied metric or null","shortcode":"supplied shortcode or null"}}]}}

Every item in experiments.due and experiments.recently_evaluated uses the same shape as a
top_priorities item. Return exactly three top priorities when at least three talents are supplied;
otherwise return one per supplied talent. Include stale_strategies only for evidence rows whose
strategy_status is missing, expired, or review_due. Include experiment items only from the
matching due_experiments or recently_evaluated evidence arrays. Use null for win/risk only when
there is no supporting evidence. Represent every stale profile and every eligible due or recently
evaluated experiment. Return at least one suggested conversation when talents are supplied.
"""


def _bilingual(value: object) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("en"), str)
        and bool(value["en"].strip())
        and isinstance(value.get("es"), str)
        and bool(value["es"].strip())
    )


def validate_payload(parsed: object, evidence: dict) -> None:
    if not isinstance(parsed, dict):
        raise ValueError("response is not an object")
    required = ("top_priorities", "strongest_creative_win", "primary_risk", "experiments", "stale_strategies", "suggested_conversations")
    if any(key not in parsed for key in required):
        raise ValueError("missing weekly review section")
    expected_priorities = min(3, len(evidence["allowed_handles"]))
    if not isinstance(parsed["top_priorities"], list) or len(parsed["top_priorities"]) != expected_priorities:
        raise ValueError(f"top priorities must contain exactly {expected_priorities} items")
    experiments = parsed["experiments"]
    if not isinstance(experiments, dict) or not isinstance(experiments.get("due"), list) or not isinstance(experiments.get("recently_evaluated"), list):
        raise ValueError("invalid experiments section")

    handles = set(evidence["allowed_handles"])
    metrics_set = set(evidence["allowed_metrics"])
    shortcodes = set(evidence["allowed_shortcodes"])
    stale_handles = set(evidence.get("stale_handles", []))
    evidence_by_handle = evidence.get("evidence_by_handle", {})

    items = list(parsed["top_priorities"]) + list(experiments["due"]) + list(experiments["recently_evaluated"])
    for optional in (parsed["strongest_creative_win"], parsed["primary_risk"]):
        if optional is not None:
            items.append(optional)
    for item in items:
        if not isinstance(item, dict) or not _bilingual(item.get("title")):
            raise ValueError("review item missing bilingual title")
        if not isinstance(item.get("handles"), list) or not item["handles"] or any(handle not in handles for handle in item["handles"]):
            raise ValueError("review item uses unknown handle")
        if item.get("metric") is not None and item["metric"] not in metrics_set:
            raise ValueError("review item invents metric")
        if item.get("shortcode") is not None and item["shortcode"] not in shortcodes:
            raise ValueError("review item invents shortcode")
        if not any(
            (item.get("metric") is None or item["metric"] in evidence_by_handle.get(handle, {}).get("metrics", []))
            and (item.get("shortcode") is None or item["shortcode"] in evidence_by_handle.get(handle, {}).get("shortcodes", []))
            for handle in item["handles"]
        ):
            raise ValueError("review item misattributes evidence to handle")

    if not isinstance(parsed["stale_strategies"], list):
        raise ValueError("stale strategies must be a list")
    returned_stale = []
    for item in parsed["stale_strategies"]:
        if item.get("handle") not in stale_handles or not _bilingual(item.get("status")):
            raise ValueError("invalid stale strategy item")
        returned_stale.append(item["handle"])
    if len(returned_stale) != len(stale_handles) or set(returned_stale) != stale_handles:
        raise ValueError("stale strategy section omits eligible profile")

    for section, expected in (
        (experiments["due"], evidence.get("eligible_due", [])),
        (experiments["recently_evaluated"], evidence.get("eligible_evaluated", [])),
    ):
        returned = []
        for item in section:
            if len(item["handles"]) != 1:
                raise ValueError("experiment item must name exactly one handle")
            returned.append((item["handles"][0], item.get("shortcode")))
        expected_pairs = [(item["handle"], item.get("shortcode")) for item in expected]
        if Counter(returned) != Counter(expected_pairs):
            raise ValueError("experiment section does not match eligible evidence")

    win = parsed["strongest_creative_win"]
    win_pairs = {(item["handle"], item["shortcode"]) for item in evidence.get("win_evidence", [])}
    if win_pairs:
        if win is None or not any((handle, win.get("shortcode")) in win_pairs for handle in win["handles"]):
            raise ValueError("creative win omits supporting post evidence")
    elif win is not None:
        raise ValueError("creative win supplied without post evidence")

    risk = parsed["primary_risk"]
    risk_handles = set(evidence.get("risk_handles", []))
    if risk_handles:
        if risk is None or not set(risk["handles"]).intersection(risk_handles):
            raise ValueError("primary risk omits supporting risk evidence")
    elif risk is not None:
        raise ValueError("primary risk supplied without risk evidence")
    if not isinstance(parsed["suggested_conversations"], list):
        raise ValueError("suggested conversations must be a list")
    if handles and not parsed["suggested_conversations"]:
        raise ValueError("suggested conversations must not be empty for a roster")
    for item in parsed["suggested_conversations"]:
        if item.get("handle") not in handles or not _bilingual(item.get("topic")) or not _bilingual(item.get("reason")):
            raise ValueError("invalid conversation")
        if item.get("metric") is not None and item["metric"] not in metrics_set:
            raise ValueError("conversation invents metric")
        if item.get("shortcode") is not None and item["shortcode"] not in shortcodes:
            raise ValueError("conversation invents shortcode")
        if not any(
            (item.get("metric") is None or item["metric"] in evidence_by_handle.get(handle, {}).get("metrics", []))
            and (item.get("shortcode") is None or item["shortcode"] in evidence_by_handle.get(handle, {}).get("shortcodes", []))
            for handle in [item["handle"]]
        ):
            raise ValueError("conversation misattributes evidence to handle")


def generate_weekly_review(evidence: dict) -> str | None:
    prompt = build_prompt(evidence)
    client = genai.Client(api_key=config.GOOGLE_API_KEY)
    last_error = None
    for attempt in range(MAX_ATTEMPTS):
        contents = prompt if attempt == 0 else f"{prompt}\nPrevious response invalid: {last_error}. Return only valid JSON."
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        try:
            parsed = json.loads(response.text)
            validate_payload(parsed, evidence)
            return json.dumps(parsed)
        except (json.JSONDecodeError, TypeError, ValueError, KeyError, AttributeError) as error:
            last_error = error
            logger.warning("Weekly review invalid on attempt %d: %s", attempt + 1, error)
    return None
