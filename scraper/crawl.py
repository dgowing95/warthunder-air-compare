"""Self-paced crawler for the War Thunder aircraft wiki.

The crawler discovers every aircraft from the wiki's aviation catalogue and
then refreshes one aircraft at a time with a configurable delay between
requests. The delay is sized so that a full pass over the catalogue takes about
a week, which keeps the load on the wiki gentle and naturally re-scrapes each
aircraft roughly weekly. Progress is kept in the database, so the crawler
resumes where it left off after a restart.
"""

import argparse
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests

from .parse import parse_unit, serialise

BASE_URL = "https://wiki.warthunder.com"
CATALOGUE_PATH = "/aviation"
USER_AGENT = (
    "warthunder-air-compare/1.0 "
    "(+https://github.com/dgowing95/warthunder-air-compare)"
)

DEFAULT_DELAY = float(os.environ.get("WTAC_CRAWL_DELAY", "480"))
# Re-run discovery once per pass so newly added aircraft are picked up.
DISCOVERY_INTERVAL = float(os.environ.get("WTAC_DISCOVERY_INTERVAL", "604800"))

_UNIT_LINK = re.compile(r"/unit/([a-z0-9_\-.]+)")
_SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")

_COLUMNS = [
    "slug", "name", "image_url", "nation", "rank", "br_rb",
    "max_speed_min", "max_speed_max", "max_speed_alt",
    "turn_time_min", "turn_time_max",
    "climb_rate_min", "climb_rate_max",
    "max_altitude", "wing_loading", "takeoff_run", "crew",
    "armament", "suspended_armament", "countermeasures",
    "last_scraped", "raw",
]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def db_path():
    return os.environ.get("WTAC_DB_PATH", "planes.db")


def connect():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    with open(_SCHEMA, encoding="utf-8") as handle:
        conn.executescript(handle.read())
    conn.commit()


def _session():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def _get(session, url, timeout=30):
    for attempt in range(5):
        response = session.get(url, timeout=timeout)
        if response.status_code == 200:
            return response.text
        if response.status_code == 429 or response.status_code >= 500:
            time.sleep(min(60, 5 * (attempt + 1)))
            continue
        response.raise_for_status()
    response.raise_for_status()
    return None


def discover(conn, session):
    """Find every aircraft slug in the catalogue and record new ones."""
    html = _get(session, urljoin(BASE_URL, CATALOGUE_PATH))
    slugs = sorted(set(_UNIT_LINK.findall(html)))
    now = _now()
    new = 0
    for slug in slugs:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO scrape_state (slug, discovered_at, status) "
            "VALUES (?, ?, 'pending')",
            (slug, now),
        )
        new += cursor.rowcount
    conn.commit()
    print(f"discovery: {len(slugs)} aircraft in catalogue, {new} new", flush=True)
    return slugs


def _upsert_aircraft(conn, record):
    row = serialise(record)
    row["last_scraped"] = _now()
    placeholders = ", ".join("?" for _ in _COLUMNS)
    columns = ", ".join(_COLUMNS)
    conn.execute(
        f"INSERT OR REPLACE INTO aircraft ({columns}) VALUES ({placeholders})",
        [row.get(column) for column in _COLUMNS],
    )


def scrape_one(conn, session, slug):
    now = _now()
    conn.execute(
        "UPDATE scrape_state SET last_attempt = ? WHERE slug = ?", (now, slug)
    )
    conn.commit()
    try:
        html = _get(session, urljoin(BASE_URL, f"/unit/{slug}"))
        record = parse_unit(html, slug)
        _upsert_aircraft(conn, record)
        conn.execute(
            "UPDATE scrape_state SET last_success = ?, status = 'ok', error = NULL "
            "WHERE slug = ?",
            (_now(), slug),
        )
        conn.commit()
        print(f"scraped {slug}: {record['name']}", flush=True)
        return True
    except Exception as error:  # noqa: BLE001 - record and continue crawling
        conn.execute(
            "UPDATE scrape_state SET status = 'error', error = ? WHERE slug = ?",
            (str(error), slug),
        )
        conn.commit()
        print(f"failed {slug}: {error}", file=sys.stderr, flush=True)
        return False


def next_slug(conn):
    row = conn.execute(
        "SELECT slug FROM scrape_state "
        "ORDER BY (last_success IS NOT NULL), last_success ASC LIMIT 1"
    ).fetchone()
    return row["slug"] if row else None


def crawl_once(conn, session, slugs):
    """Scrape an explicit list of slugs (used for tests and seeding)."""
    for slug in slugs:
        conn.execute(
            "INSERT OR IGNORE INTO scrape_state (slug, discovered_at, status) "
            "VALUES (?, ?, 'pending')",
            (slug, _now()),
        )
    conn.commit()
    for slug in slugs:
        scrape_one(conn, session, slug)


def run(delay):
    conn = connect()
    init_db(conn)
    session = _session()
    last_discovery = 0.0
    while True:
        if time.monotonic() - last_discovery >= DISCOVERY_INTERVAL:
            try:
                discover(conn, session)
                last_discovery = time.monotonic()
            except Exception as error:  # noqa: BLE001
                print(f"discovery failed: {error}", file=sys.stderr, flush=True)
        slug = next_slug(conn)
        if not slug:
            time.sleep(delay)
            continue
        scrape_one(conn, session, slug)
        time.sleep(delay)


def main(argv=None):
    parser = argparse.ArgumentParser(description="War Thunder wiki crawler")
    parser.add_argument(
        "--delay", type=float, default=DEFAULT_DELAY,
        help="seconds to wait between requests in continuous mode",
    )
    parser.add_argument(
        "--once", nargs="+", metavar="SLUG",
        help="scrape the given slugs and exit",
    )
    parser.add_argument(
        "--discover", action="store_true",
        help="refresh the catalogue of aircraft and exit",
    )
    args = parser.parse_args(argv)

    if args.once:
        conn = connect()
        init_db(conn)
        crawl_once(conn, _session(), args.once)
        return
    if args.discover:
        conn = connect()
        init_db(conn)
        discover(conn, _session())
        return

    run(args.delay)


if __name__ == "__main__":
    main()
