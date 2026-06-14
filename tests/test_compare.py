import json

from app.compare import compare


def _aircraft(**overrides):
    base = {
        "slug": "test",
        "name": "Test",
        "nation": "usa",
        "rank": "V",
        "br_rb": 8.0,
        "max_speed_min": 1000.0,
        "max_speed_max": 1000.0,
        "turn_time_min": 20.0,
        "turn_time_max": 20.0,
        "climb_rate_min": 100.0,
        "climb_rate_max": 100.0,
        "armament": "2 × 20 mm cannon",
        "suspended_armament": json.dumps([]),
        "countermeasures": None,
    }
    base.update(overrides)
    return base


def test_better_aircraft_wins():
    mine = _aircraft(turn_time_min=15.0, turn_time_max=15.0,
                     climb_rate_min=150.0, climb_rate_max=150.0,
                     max_speed_min=1200.0, max_speed_max=1200.0)
    target = _aircraft()
    result = compare(mine, target)
    assert result["verdict"] == "good"
    speed = next(d for d in result["dimensions"] if d["label"] == "Max speed")
    assert speed["winner"] == "mine"


def test_worse_aircraft_loses():
    mine = _aircraft()
    target = _aircraft(turn_time_min=12.0, turn_time_max=12.0,
                       climb_rate_min=180.0, climb_rate_max=180.0,
                       max_speed_min=1400.0, max_speed_max=1400.0)
    result = compare(mine, target)
    assert result["verdict"] == "poor"


def test_evenly_matched_is_average():
    result = compare(_aircraft(), _aircraft())
    assert result["verdict"] == "average"


def test_turn_time_lower_is_better():
    mine = _aircraft(turn_time_min=18.0, turn_time_max=18.0)
    target = _aircraft(turn_time_min=25.0, turn_time_max=25.0)
    turn = next(d for d in compare(mine, target)["dimensions"]
                if d["label"] == "Turn time")
    assert turn["winner"] == "mine"


def test_missing_stat_is_unknown():
    mine = _aircraft(max_speed_min=None, max_speed_max=None)
    speed = next(d for d in compare(mine, _aircraft())["dimensions"]
                 if d["label"] == "Max speed")
    assert speed["winner"] == "unknown"


def test_countermeasures_edge():
    mine = _aircraft(countermeasures="Flares/Chaff")
    target = _aircraft()
    cm = next(d for d in compare(mine, target)["dimensions"]
              if d["label"] == "Countermeasures")
    assert cm["winner"] == "mine"
