import json

from flask import Flask, jsonify, request, send_from_directory

from . import db
from .compare import bracket, compare

app = Flask(__name__, static_folder="static", static_url_path="")


def _public(row):
    record = dict(row)
    record.pop("raw", None)
    raw = record.get("suspended_armament")
    if raw:
        try:
            record["suspended_armament"] = json.loads(raw)
        except (TypeError, ValueError):
            record["suspended_armament"] = []
    else:
        record["suspended_armament"] = []
    return record


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/bracket")
def bracket_page():
    return send_from_directory(app.static_folder, "bracket.html")


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "aircraft": db.count()})


@app.get("/api/aircraft")
def api_search():
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify([])
    return jsonify(db.search(term))


@app.get("/api/aircraft/<path:identifier>")
def api_get(identifier):
    row = db.get(identifier)
    if not row:
        return jsonify({"error": "aircraft not found"}), 404
    return jsonify(_public(row))


@app.get("/api/compare")
def api_compare():
    mine = request.args.get("mine", "").strip()
    target = request.args.get("target", "").strip()
    if not mine or not target:
        return jsonify({"error": "both 'mine' and 'target' are required"}), 400
    mine_row = db.get(mine)
    if not mine_row:
        return jsonify({"error": f"aircraft not found: {mine}"}), 404
    target_row = db.get(target)
    if not target_row:
        return jsonify({"error": f"aircraft not found: {target}"}), 404
    return jsonify(compare(mine_row, target_row))


def _page_args():
    def _int(name, default):
        try:
            return int(request.args.get(name, default))
        except (TypeError, ValueError):
            return default
    limit = max(1, min(_int("limit", 20), 1000))
    offset = max(0, _int("offset", 0))
    return limit, offset


@app.get("/api/bracket")
def api_bracket():
    mine = request.args.get("mine", "").strip()
    if not mine:
        return jsonify({"error": "'mine' is required"}), 400
    mine_row = db.get(mine)
    if not mine_row:
        return jsonify({"error": f"aircraft not found: {mine}"}), 404
    br = mine_row.get("br_rb")
    if br is None:
        return jsonify({"error": "aircraft has no battle rating"}), 422
    limit, offset = _page_args()
    low, high, slug = br - 1.0, br + 1.0, mine_row.get("slug")
    total = db.count_br_range(low, high, exclude=slug)
    opponents = db.by_br_range(low, high, exclude=slug, limit=limit, offset=offset)
    payload = bracket(mine_row, opponents)
    payload.update({"total": total, "offset": offset, "limit": limit})
    return jsonify(payload)
