"""
Lytica · Sourcing Leverage Check
Navvai lead magnet, AUDIT-LITE Flask skeleton.

Render settings
  Runtime  Python 3
  Build    pip install -r requirements.txt
  Start    gunicorn app:app

Env vars
  ADMIN_KEY           required, gates /admin/leads
  ANTHROPIC_API_KEY   reserved slot, unused by this build
  LEAD_WEBHOOK_URL    optional, each lead is POSTed here as JSON
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
LEAD_WEBHOOK_URL = os.environ.get("LEAD_WEBHOOK_URL", "")

# Render wipes the disk on every deploy unless a disk is attached, so the
# console log line below is the durable record. This file is a local convenience.
LEAD_FILE = os.environ.get("LEAD_FILE", "leads.jsonl")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/healthz")
def healthz():
    return jsonify(ok=True, service="lytica-sourcing-leverage-check")


@app.route("/api/lead", methods=["POST"])
def api_lead():
    payload = request.get_json(silent=True) or {}
    lead = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "first_name": str(payload.get("first_name", ""))[:120],
        "last_name": str(payload.get("last_name", ""))[:120],
        "company": str(payload.get("company", ""))[:200],
        "email": str(payload.get("email", ""))[:200],
        "lane": str(payload.get("lane", ""))[:20],
        "seat": str(payload.get("seat", ""))[:120],
        "verdict": str(payload.get("verdict", ""))[:80],
        "weakest_area": str(payload.get("weakest_area", ""))[:80],
        "weakest_score": payload.get("weakest_score"),
        "scores": payload.get("scores"),
        "goal": str(payload.get("goal", ""))[:400],
        "answers": payload.get("answers"),
        "user_agent": request.headers.get("User-Agent", "")[:300],
    }

    if not lead["email"]:
        return jsonify(ok=False, error="email required"), 400

    # the durable record: Render keeps stdout
    print("LEAD " + json.dumps(lead, ensure_ascii=False), flush=True)

    try:
        with open(LEAD_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(lead, ensure_ascii=False) + "\n")
    except OSError as exc:
        print("LEAD_FILE_WRITE_FAILED " + str(exc), flush=True)

    # a webhook failure must never block capture
    if LEAD_WEBHOOK_URL:
        try:
            req = urllib.request.Request(
                LEAD_WEBHOOK_URL,
                data=json.dumps(lead).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5).read()
        except (urllib.error.URLError, OSError, ValueError) as exc:
            print("WEBHOOK_FAILED " + str(exc), flush=True)

    return jsonify(ok=True)


@app.route("/admin/leads")
def admin_leads():
    if not ADMIN_KEY:
        return jsonify(ok=False, error="ADMIN_KEY is not set on this service"), 503
    if request.args.get("key", "") != ADMIN_KEY:
        return jsonify(ok=False, error="bad key"), 401

    rows = []
    try:
        with open(LEAD_FILE, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except FileNotFoundError:
        pass

    return jsonify(
        ok=True,
        count=len(rows),
        note="This file resets on every deploy unless a Render disk is attached. "
        "The full record is in the service logs, one line per lead prefixed LEAD.",
        leads=rows[::-1],
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
