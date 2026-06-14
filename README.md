# War Thunder Air Compare

A small web app for War Thunder: save the aircraft you fly, then type the name
of an aircraft you've run into. It pulls both aircraft's stats and shows a
head-to-head comparison (max speed, turn time, climb rate, countermeasures,
primary armament) plus a verdict on your odds in a dogfight: **good**,
**average**, or **poor**. All figures are Realistic Battles values.

## How it works

- **Scraper** (`scraper/`) discovers every aircraft from the wiki's aviation
  catalogue and parses each unit page into a SQLite database. It crawls slowly -
  one aircraft every few minutes by default - so a full pass takes about a week
  and then repeats, keeping the load on the wiki light. Progress is stored in
  the database, so it resumes after a restart.
- **Web app** (`app/`) is a Flask API plus a static frontend. It opens the
  database read-only, so the scraper can keep writing while the site serves
  traffic.

### API

| Endpoint | Description |
| --- | --- |
| `GET /api/aircraft?q=<term>` | Autocomplete search by name |
| `GET /api/aircraft/<slug-or-name>` | Full stats for one aircraft |
| `GET /api/compare?mine=<a>&target=<b>` | Comparison and verdict |
| `GET /healthz` | Health check and aircraft count |

## Development

```sh
make install        # create a virtualenv and install dependencies
make test           # run the unit tests
make scrape-once    # scrape a couple of aircraft into ./planes.db
make serve          # serve the app on http://localhost:8080
```

Then visit <http://localhost:8080>, set your aircraft, and search for a target.

The database location is set with `WTAC_DB_PATH` (defaults to `planes.db`), and
the crawl delay with `WTAC_CRAWL_DELAY` (seconds).

## Container

The image runs either role through its entrypoint:

```sh
docker build -t warthunder-air-compare .
docker run -p 8080:8080 -v wtac-data:/data warthunder-air-compare web
docker run -v wtac-data:/data warthunder-air-compare scraper
```

Images are published to `ghcr.io/dgowing95/warthunder-air-compare` by the
GitHub Actions workflow on every push to `main`.

## Deployment

The `chart/` directory holds a generic Helm chart (web + scraper containers
sharing one persistent volume). Its defaults are deliberately neutral -
deployment specifics such as hostname, ingress class and TLS issuer are supplied
through values overrides at deploy time.
