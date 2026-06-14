"""Turn a War Thunder wiki unit page into a flat stats dictionary.

Only Realistic Battles (RB) figures are kept. The wiki renders four values for
performance stats - stock/upgraded for both Arcade and Realistic - in spans
tagged with mode/modification classes. We read the two RB spans
(``show-char-rb-mod-ref`` = upgraded, ``show-char-rb-mod-basic`` = stock) and
discard the Arcade ones.
"""

import json
import re

from bs4 import BeautifulSoup

_NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def _clean(text):
    if text is None:
        return None
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _to_float(text):
    if not text:
        return None
    match = _NUMBER.search(text)
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def _rb_values(value_el):
    """Return the RB numbers inside a chars value element.

    Falls back to the element's plain text for stats that aren't split by game
    mode (e.g. max altitude, crew)."""
    if value_el is None:
        return []
    numbers = []
    for css_class in ("show-char-rb-mod-ref", "show-char-rb-mod-basic"):
        for span in value_el.select("." + css_class):
            value = _to_float(span.get_text())
            if value is not None:
                numbers.append(value)
    if numbers:
        return numbers
    value = _to_float(value_el.get_text())
    return [value] if value is not None else []


def _min_max(value_el):
    values = _rb_values(value_el)
    if not values:
        return None, None
    return min(values), max(values)


def _single(value_el):
    values = _rb_values(value_el)
    return values[0] if values else None


def _collect_chars(soup):
    """Map every stat label on the page to its value element (first wins)."""
    chars = {}
    for block in soup.select(".game-unit_chars-block"):
        header = block.select_one(".game-unit_chars-header")
        if not header:
            continue
        key = header.get_text(strip=True).lower()
        if key and key not in chars:
            chars[key] = block.select_one(".game-unit_chars-value")
    return chars


def _nation(soup):
    flag = soup.select_one("img.game-unit_template-flag")
    if flag and flag.get("src"):
        match = re.search(r"country_([a-z]+)", flag["src"])
        if match:
            return match.group(1)
    return None


def _image_url(soup):
    image = soup.select_one("img.game-unit_template-image")
    if image and image.get("src"):
        return image["src"].strip()
    return None


def _battle_rating_rb(soup):
    for item in soup.select(".game-unit_br-item"):
        mode = item.select_one(".mode")
        value = item.select_one(".value")
        if mode and value and mode.get_text(strip=True).upper() == "RB":
            return _to_float(value.get_text())
    return None


def _max_speed_altitude(soup):
    for block in soup.select(".game-unit_chars-block"):
        header = block.select_one(".game-unit_chars-header")
        if header and header.get_text(strip=True).lower() == "max speed":
            subline = block.select_one(".game-unit_chars-subline")
            if subline:
                return _to_float(subline.get_text())
    return None


def _primary_armament(soup):
    title = soup.select_one("#weapon .game-unit_weapon-title")
    return _clean(title.get_text(" ", strip=True)) if title else None


def _suspended_armament(soup):
    for block in soup.select(".block"):
        header = block.select_one(".block-header")
        if header and header.get_text(strip=True).lower() == "suspended armament":
            setups = []
            for line in block.select(".game-unit_chars-line"):
                header = line.select_one(".game-unit_chars-header")
                value = line.select_one(".game-unit_chars-value")
                if not header or not value:
                    continue
                if not header.get_text(strip=True).lower().startswith("setup"):
                    continue
                text = _clean(value.get_text(" ", strip=True))
                if text:
                    setups.append(text)
            return setups
    return []


def _countermeasures(html):
    for label in ("Flares/Chaff", "Flares", "Chaff"):
        if label in html:
            return label
    return None


def parse_unit(html, slug):
    soup = BeautifulSoup(html, "lxml")
    chars = _collect_chars(soup)

    name_el = soup.select_one(".game-unit_name")
    crew = _single(chars.get("crew"))

    record = {
        "slug": slug,
        "name": _clean(name_el.get_text(strip=True)) if name_el else slug,
        "image_url": _image_url(soup),
        "nation": _nation(soup),
        "rank": None,
        "br_rb": _battle_rating_rb(soup),
        "max_speed_min": None,
        "max_speed_max": None,
        "max_speed_alt": _max_speed_altitude(soup),
        "turn_time_min": None,
        "turn_time_max": None,
        "climb_rate_min": None,
        "climb_rate_max": None,
        "max_altitude": _single(chars.get("max altitude")),
        "wing_loading": _single(chars.get("wing loading")),
        "takeoff_run": _single(chars.get("takeoff run")),
        "crew": int(crew) if crew is not None else None,
        "armament": _primary_armament(soup),
        "suspended_armament": _suspended_armament(soup),
        "countermeasures": _countermeasures(html),
    }

    rank_el = soup.select_one(".game-unit_rank .game-unit_card-info_value")
    if rank_el:
        record["rank"] = rank_el.get_text(strip=True)

    record["max_speed_min"], record["max_speed_max"] = _min_max(chars.get("max speed"))
    record["turn_time_min"], record["turn_time_max"] = _min_max(chars.get("turn time"))
    record["climb_rate_min"], record["climb_rate_max"] = _min_max(chars.get("rate of climb"))

    return record


def serialise(record):
    """Prepare a parsed record for storage (lists become JSON text)."""
    row = dict(record)
    row["suspended_armament"] = json.dumps(row.get("suspended_armament") or [])
    row["raw"] = json.dumps(record, default=str)
    return row
