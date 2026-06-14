import json

from flask import Flask, jsonify, request, send_from_directory

from . import db
from .compare import compare

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
