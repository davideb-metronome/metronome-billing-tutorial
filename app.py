"""
Episode 3: HTTP endpoint for sending usage events

 This runs a thin Flask HTTP boundary. The POST
 route `/api/generate` accepts JSON from external clients (curl today,
 a frontend later), validates it, then forwards a well-formed event to
 the Metronome client (SDK wrapper). The browser never calls Metronome
 directly; only the server does.
"""

import logging
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from config import METRONOME_BEARER_TOKEN, EVENT_TYPE, DEMO_CUSTOMER_ALIAS
from services.metronome_client import MetronomeClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

if not METRONOME_BEARER_TOKEN:
    raise RuntimeError("METRONOME_BEARER_TOKEN is not set. Configure it in .env")

if not DEMO_CUSTOMER_ALIAS:
    raise RuntimeError("DEMO_CUSTOMER_ALIAS is not set. Configure it in .env")

client = MetronomeClient(METRONOME_BEARER_TOKEN)


@app.post("/api/generate")
def generate_image():
    """Accepts JSON and emits a usage event.


    Quick curl:
      curl -sS -X POST http://localhost:5000/api/generate \
        -H 'Content-Type: application/json' \
        -d '{"tier":"ultra","transaction_id":"ep3-demo-001","model":"nova-v2","region":"us-west-2"}'
    """
    data = request.get_json(silent=True) or {}

    # Always use the ingest alias from env for this episode.
    ingest_alias = DEMO_CUSTOMER_ALIAS

    # Validate tier (required; concise)
    allowed = {"standard", "high-res", "ultra"}
    tier = (data.get("tier") or "").strip().lower()
    if tier not in allowed:
        return jsonify({
            "error": "Invalid or missing 'tier'",
            "allowed": sorted(allowed),
        }), 400

   

    # Build properties as strings per Metronome guidelines
    properties = {
        "image_type": tier,
        "num_images": "1",
        "model": str(data.get("model", "nova-v2")),
        "region": str(data.get("region", "us-west-2")),
    }

  
    transaction_id = (data.get("transaction_id") or "").strip()
    if not transaction_id:
        return jsonify({
            "error": "Missing 'transaction_id' (idempotency key). Provide a stable, unique string per action.",
        }), 400

    # Always use server time (UTC) for this episode
    timestamp = datetime.now(timezone.utc)

    try:
        client.send_usage_event(
            customer_id=ingest_alias,
            event_type=EVENT_TYPE,
            properties=properties,
            timestamp=timestamp,
            transaction_id=transaction_id,
        )
        logger.info("Sent usage event | event_type=%s | tier=%s | tx=%s", EVENT_TYPE, tier, transaction_id)
        return jsonify({
            "success": True,
            "event_type": EVENT_TYPE,
            "tier": tier,
            "ingest_alias": ingest_alias,
            "transaction_id": transaction_id,
            "timestamp": timestamp
        })
    except Exception as e:
        logger.exception("Failed to send usage event")
        return jsonify({"error": f"Failed to send usage: {e}"}), 500


if __name__ == "__main__":
    logger.info("Starting Episode 3 API on http://localhost:5000")
    app.run(debug=True, port=5000)
