"""Head-to-head comparison and dogfight verdict.

Each dimension is scored from the player's point of view: +1 when their aircraft
is favoured, -1 when the target is, 0 when they're level or the data is missing.
The weighted total is normalised against the dimensions we actually had data for
and mapped to good / average / poor, so the verdict degrades gracefully when the
wiki is missing a stat."""

import json
import re

GOOD = "good"
AVERAGE = "average"
POOR = "poor"

# Weight of each dimension in the overall verdict.
WEIGHTS = {
    "turn_time": 1.0,
    "max_speed": 1.0,
    "climb_rate": 1.0,
    "armament": 1.0,
    "countermeasures": 0.5,
}


def _representative(row, stat, higher_is_better):
    values = [row.get(f"{stat}_min"), row.get(f"{stat}_max")]
    values = [value for value in values if value is not None]
    if not values:
        return None
    return max(values) if higher_is_better else min(values)


def _winner(mine, target, higher_is_better):
    if mine is None or target is None:
        return None
    if mine == target:
        return "tie"
    if higher_is_better:
        return "mine" if mine > target else "target"
    return "mine" if mine < target else "target"


def _cannon_score(armament, suspended):
    """Rough firepower estimate: cannon calibre x count, plus a missile bonus."""
    score = 0.0
    if armament:
        count = re.search(r"(\d+)\s*[x×]", armament)
        calibre = re.search(r"(\d+(?:\.\d+)?)\s*mm", armament)
        n = int(count.group(1)) if count else 1
        mm = float(calibre.group(1)) if calibre else 0.0
        score += n * mm
    text = " ".join(suspended).lower() if suspended else ""
    if "air-to-air" in text or "missile" in text:
        score += 30.0
    return score


def _suspended_list(row):
    raw = row.get("suspended_armament")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return []


def _stat_dimension(label, mine, target, higher_is_better, fmt):
    winner = _winner(mine, target, higher_is_better)
    return {
        "label": label,
        "mine": fmt(mine) if mine is not None else None,
        "target": fmt(target) if target is not None else None,
        "winner": winner if winner is not None else "unknown",
    }


def _km_h(value):
    return f"{value:.0f} km/h"


def _seconds(value):
    return f"{value:g} s"


def _m_s(value):
    return f"{value:.0f} m/s"


def _summary(row):
    return {
        "slug": row.get("slug"),
        "name": row.get("name"),
        "nation": row.get("nation"),
        "rank": row.get("rank"),
        "br_rb": row.get("br_rb"),
    }


def compare(mine, target):
    dimensions = []
    score = 0.0
    available = 0.0

    pairs = [
        ("Max speed", "max_speed", True, _km_h),
        ("Turn time", "turn_time", False, _seconds),
        ("Rate of climb", "climb_rate", True, _m_s),
    ]
    for label, stat, higher, fmt in pairs:
        mine_value = _representative(mine, stat, higher)
        target_value = _representative(target, stat, higher)
        dimension = _stat_dimension(label, mine_value, target_value, higher, fmt)
        dimensions.append(dimension)
        if dimension["winner"] in ("mine", "target"):
            available += WEIGHTS[stat]
            score += WEIGHTS[stat] * (1 if dimension["winner"] == "mine" else -1)

    # Countermeasures: having flares/chaff against missiles is an edge.
    mine_cm = mine.get("countermeasures")
    target_cm = target.get("countermeasures")
    cm_winner = "tie"
    if bool(mine_cm) != bool(target_cm):
        cm_winner = "mine" if mine_cm else "target"
        available += WEIGHTS["countermeasures"]
        score += WEIGHTS["countermeasures"] * (1 if mine_cm else -1)
    dimensions.append({
        "label": "Countermeasures",
        "mine": mine_cm or "None",
        "target": target_cm or "None",
        "winner": cm_winner,
    })

    # Armament: fixed cannon plus a bonus for guided/suspended missiles.
    mine_arm = _cannon_score(mine.get("armament"), _suspended_list(mine))
    target_arm = _cannon_score(target.get("armament"), _suspended_list(target))
    arm_winner = _winner(mine_arm, target_arm, True)
    if mine_arm == 0 and target_arm == 0:
        arm_winner = "unknown"
    if arm_winner in ("mine", "target"):
        available += WEIGHTS["armament"]
        score += WEIGHTS["armament"] * (1 if arm_winner == "mine" else -1)
    dimensions.append({
        "label": "Primary armament",
        "mine": mine.get("armament") or "None",
        "target": target.get("armament") or "None",
        "winner": arm_winner,
    })

    ratio = score / available if available else 0.0
    if ratio >= 0.2:
        verdict = GOOD
    elif ratio <= -0.2:
        verdict = POOR
    else:
        verdict = AVERAGE

    return {
        "mine": _summary(mine),
        "target": _summary(target),
        "dimensions": dimensions,
        "verdict": verdict,
        "score": round(ratio, 3),
    }
