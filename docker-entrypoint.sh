#!/bin/sh
set -e

role="${1:-web}"

case "$role" in
    web)
        exec gunicorn --bind 0.0.0.0:8080 --workers "${WEB_WORKERS:-2}" \
            --access-logfile - app:app
        ;;
    scraper)
        exec python -m scraper.crawl
        ;;
    *)
        # Allow running arbitrary commands (e.g. one-off scrapes).
        exec "$@"
        ;;
esac
