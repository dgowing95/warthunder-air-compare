import os

from scraper.parse import parse_unit

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _parse(slug):
    with open(os.path.join(FIXTURES, f"{slug}.html"), encoding="utf-8") as handle:
        return parse_unit(handle.read(), slug)


def test_lightning_f6():
    record = _parse("lightning_f6")
    assert record["name"] == "Lightning F.6"
    assert record["image_url"] == (
        "https://static.encyclopedia.warthunder.com/images/lightning_f6.png"
    )
    assert record["nation"] == "britain"
    assert record["rank"] == "VI"
    assert record["br_rb"] == 9.3
    # RB turn time: upgraded 26 s, stock 28.2 s.
    assert record["turn_time_min"] == 26.0
    assert record["turn_time_max"] == 28.2
    assert record["climb_rate_max"] == 150.0
    assert record["max_speed_max"] == 2290.0
    assert record["max_altitude"] == 16000.0
    assert record["wing_loading"] == 430.0
    assert record["crew"] == 1
    assert "30 mm ADEN" in record["armament"]
    assert record["countermeasures"] is None
    assert any("Firestreak" in setup for setup in record["suspended_armament"])


def test_f111c():
    record = _parse("f_111c_raaf")
    assert record["name"] == "F-111C"
    assert record["image_url"] == (
        "https://static.encyclopedia.warthunder.com/images/f_111c_raaf.png"
    )
    assert record["nation"] == "australia"
    assert record["rank"] == "VII"
    assert record["br_rb"] == 11.7
    # RB turn time is published as a range (stock vs upgraded).
    assert record["turn_time_min"] == 33.0
    assert record["turn_time_max"] == 34.6
    assert record["crew"] == 2
    assert record["countermeasures"] == "Flares/Chaff"
    # The F-111C has no fixed offensive cannon and no structured setup list.
    assert record["armament"] is None
    assert record["suspended_armament"] == []
