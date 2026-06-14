# CLAUDE.md

Guidance for working in this repository.

## What this is

A web app that compares War Thunder aircraft and rates dogfight odds. A scraper
fills a SQLite database from the War Thunder wiki; a Flask app serves an API and
a static frontend that reads from it. **Only Realistic Battles (RB) stats are
used** — Arcade values are deliberately discarded.

## Layout

```
app/             Flask API + static frontend
  __init__.py    app factory, routes, serves static/
  db.py          read-only SQLite access
  compare.py     head-to-head comparison + good/average/poor verdict
  static/        index.html, style.css, main.js (vanilla JS, no build step)
scraper/         wiki crawler
  parse.py       pure HTML -> dict parser (no I/O)
  crawl.py       self-paced crawler, catalogue discovery, DB writes, CLI
  schema.sql     aircraft + scrape_state tables
tests/           pytest; fixtures/ holds saved wiki HTML
chart/           generic Helm chart (web + scraper containers, shared PVC)
Dockerfile       single image; entrypoint picks the web or scraper role
```

## Development

```sh
make install      # venv + dependencies (creates .venv/)
make test         # pytest
make scrape-once  # scrape a couple of aircraft into ./planes.db
make serve        # gunicorn on http://localhost:8080
```

Environment variables:
- `WTAC_DB_PATH` — database path (default `planes.db`).
- `WTAC_CRAWL_DELAY` — seconds between requests in continuous crawl mode.

Scraper CLI:
- `python -m scraper.crawl` — continuous self-paced crawl.
- `python -m scraper.crawl --once <slug> [<slug> …]` — scrape specific slugs and exit.
- `python -m scraper.crawl --discover` — refresh the catalogue of slugs and exit.

## Data source and parsing

Stats come from the **new** wiki at `https://wiki.warthunder.com/unit/<slug>`,
which is server-rendered HTML (parseable with requests + BeautifulSoup). The
**old** wiki (`old-wiki.warthunder.com`) is free-form prose — do not use it.

- **Slugs are not guessable** (e.g. `lightning_f6`, `f_111c_raaf`). Discover them
  from `https://wiki.warthunder.com/aviation`, which links every aircraft via
  `/unit/<slug>`.
- Performance stats render four spans (stock/upgraded × Arcade/Realistic). Read
  only the RB spans: `show-char-rb-mod-ref` (upgraded) and
  `show-char-rb-mod-basic` (stock). Use the RB battle rating from
  `.game-unit_br-item` where `.mode` is `RB`.
- Stats split by game mode are stored as `_min`/`_max` (e.g. `turn_time_min`,
  `turn_time_max`). `compare.py` picks the favourable end per metric (lowest turn
  time, highest speed/climb).

Parsing quirks to keep in mind:
- Text contains non-breaking spaces; normalise with `_clean()` in `parse.py`.
- Suspended armament: only treat `Setup N` lines as ordnance. Other lines in
  that block (e.g. "Max weight") are weight/balance data, not weapons.
- Some aircraft have **no fixed offensive cannon** (no `weapon-title`); their
  `armament` is legitimately `None`. The comparison treats missing stats as
  `unknown` and the verdict degrades gracefully.

## Architecture notes

- `parse.py` does no I/O so it is unit-tested directly against saved fixtures in
  `tests/fixtures/`. When changing parsing, update or add a fixture and assert
  against it rather than hitting the network in tests.
- The web app opens the database **read-only** and tolerates a missing/empty
  database (returns empty results), since the first crawl may still be running.
- The crawler keeps progress in `scrape_state`, so it resumes after a restart
  and refreshes oldest-first.
- Web and scraper run from one image (entrypoint arg `web` or `scraper`) and, in
  the chart, share one volume holding the SQLite file.

## Conventions

- Standard library + the few pinned deps in `requirements.txt`; no frontend
  build tooling.
- Keep the Helm chart's defaults generic — deployment specifics (hostname,
  ingress class, TLS, storage class) are supplied via values overrides, not
  defaults.
