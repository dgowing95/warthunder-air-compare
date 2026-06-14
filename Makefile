IMAGE ?= ghcr.io/dgowing95/warthunder-air-compare
TAG ?= latest
DB ?= planes.db

.PHONY: install test scrape-once serve docker-build docker-push

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt pytest

test:
	.venv/bin/python -m pytest -q

# Scrape a couple of aircraft into a local database for development.
scrape-once:
	WTAC_DB_PATH=$(DB) .venv/bin/python -m scraper.crawl --once lightning_f6 f_111c_raaf

serve:
	WTAC_DB_PATH=$(DB) .venv/bin/gunicorn --bind 0.0.0.0:8080 app:app

docker-build:
	docker build -t $(IMAGE):$(TAG) .

docker-push:
	docker push $(IMAGE):$(TAG)
