"""
 This runs a thin Flask HTTP boundary. The POST
 route `/api/generate` accepts JSON from external clients (curl today,
 a frontend later), validates it, then forwards a well-formed event to
 the Metronome client (SDK wrapper). The browser never calls Metronome
 directly; only the server does.

 Episode 4 adds a local setup route `POST /api/metrics` that creates the
 "Nova Image Generation" billable metric (SUM over "num_images", grouped by
 `image_type`).

 Episode 5 adds pricing setup via `POST /api/pricing`:
  - Creates a product tied to the Ep4 metric
  - Creates a rate card
  - Adds three FLAT rates, each scoped to a pricing group value
    (`image_type=standard|high-res|ultra`) using config prices
"""

import logging
from datetime import datetime, timezone

from flask import Flask, jsonify, request
import json
import os

from config import (
    METRONOME_BEARER_TOKEN,
    EVENT_TYPE,
    DEMO_CUSTOMER_ALIAS,
    BILLABLE_METRIC_NAME,
    BILLABLE_GROUP_KEYS,
    BILLABLE_PRICES,
    PRODUCT_NAME,
    RATE_CARD_NAME,
    RATE_EFFECTIVE_AT,
)
from services.metronome_client import MetronomeClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

if not METRONOME_BEARER_TOKEN:
    raise RuntimeError("METRONOME_BEARER_TOKEN is not set. Configure it in .env")

if not DEMO_CUSTOMER_ALIAS:
    raise RuntimeError("DEMO_CUSTOMER_ALIAS is not set. Configure it in .env")

client = MetronomeClient(METRONOME_BEARER_TOKEN)


# ---- Local state helpers (ids only; never committed) ----
STATE_PATH = ".metronome_config.json"

def _load_state() -> dict:
    """Load local IDs/state persisted between runs (if present)."""
    try:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_state(state: dict) -> None:
    """Persist local IDs/state to disk for idempotent setup."""
    try:
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        logger.warning("Failed to save state file %s", STATE_PATH)


def _ensure_metric() -> dict:
    """Create or reuse the Episode 4 metric and persist its ID.

    Simple idempotent behavior:
    - If a stored metric_id exists and is retrievable → reuse.
    - Else look up by name and reuse the first match → persist id.
    - Else create anew → persist id.
    """
    state = _load_state()

    # 1) Try stored id first
    metric_id = state.get("metric_id")
    if metric_id:
        existing = client.retrieve_billable_metric(metric_id)
        if existing:
            logger.info("Using existing metric from state: %s", metric_id)
            return existing

    # 2) Try to find by name (non-archived)
    metrics = client.list_billable_metrics()
    matches = [m for m in metrics if m.get("name") == BILLABLE_METRIC_NAME]
    if matches:
        m = matches[0]
        state["metric_id"] = m.get("id")
        _save_state(state)
        logger.info("Linked existing metric by name: %s -> %s", BILLABLE_METRIC_NAME, m.get("id"))
        return m

    # 3) Create a new metric
    created = client.create_billable_metric(
        name=BILLABLE_METRIC_NAME,
        event_type=EVENT_TYPE,
        aggregation_type="SUM",
        aggregation_key="num_images",
        group_keys=[list(x) for x in BILLABLE_GROUP_KEYS],
        property_filters=[
            {"name": "image_type", "exists": True},
            {"name": "num_images", "exists": True},
        ],
    )
    state["metric_id"] = created.get("id")
    _save_state(state)
    logger.info("Created metric: %s", created.get("id"))
    return created


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


@app.post("/api/metrics")
def setup_metric():
    """Create the Episode 4 billable metric.

    Hardcoded to our demo defaults:
    - name: BILLABLE_METRIC_NAME
    - event_type: EVENT_TYPE
    - aggregation: SUM over "num_images"
    - group_keys: BILLABLE_GROUP_KEYS (from config)
    - property_filters: require image_type and num_images to exist

    Quick curl:
      curl -sS -X POST http://localhost:5000/api/metrics | jq
    """
    try:
        # Ensure or create the billable metric; idempotent and persisted
        metric = _ensure_metric()
        logger.info(
            "Created billable metric id=%s name=%s",
            metric.get("id"),
            metric.get("name"),
        )
        return jsonify({
            "success": True,
            "metric_name": BILLABLE_METRIC_NAME,
            "metric": metric,
        }), 201
    except Exception as e:
        logger.exception("Failed to create billable metric")
        return jsonify({"error": f"Failed to create metric: {e}"}), 500


@app.post("/api/pricing")
def setup_pricing():
    """Create product + rate card + flat rates per image_type.

    Quick curl:
      curl -sS -X POST http://localhost:5000/api/pricing | jq
    """
    try:
        # Ensure we have a metric and its ID
        metric = _ensure_metric()
        billable_metric_id = metric.get("id")

        # Create product tied to this metric; enable dimensional pricing
        # Flatten config BILLABLE_GROUP_KEYS to pricing group key list
        pricing_group_key = [g[0] for g in BILLABLE_GROUP_KEYS]
        product = client.create_product(
            name=PRODUCT_NAME,
            billable_metric_id=billable_metric_id,
            pricing_group_key=pricing_group_key,
            presentation_group_key=pricing_group_key,
        )
        product_id = product.get("id")
        if not product_id:
            return jsonify({"error": "Failed to create product"}), 500

        # Create rate card
        rate_card = client.create_rate_card(name=RATE_CARD_NAME)
        rate_card_id = rate_card.get("id") or rate_card.get("rate_card_id")
        if not rate_card_id:
            return jsonify({"error": "Failed to create rate card"}), 500

        # Add one flat rate per image_type using pricing group values
        rates = {}
        for image_type, cents in BILLABLE_PRICES.items():
            r = client.add_flat_rate(
                rate_card_id=rate_card_id,
                product_id=product_id,
                price_cents=int(cents),
                starting_at=RATE_EFFECTIVE_AT,
                pricing_group_values={"image_type": image_type},
            )
            rid = r.get("id") or r.get("rate_id")
            rates[image_type] = {"id": rid, "price_cents": cents}

        # Persist IDs so future runs can reuse
        state = _load_state()
        state.update({
            "metric_id": billable_metric_id,
            "product_id": product_id,
            "rate_card_id": rate_card_id,
        })
        _save_state(state)

        return jsonify({
            "success": True,
            "product": {"id": product_id, "name": PRODUCT_NAME},
            "rate_card": {"id": rate_card_id, "name": RATE_CARD_NAME},
            "rates": rates,
        }), 201
    except Exception as e:
        logger.exception("Failed to create pricing")
        return jsonify({"error": f"Failed to create pricing: {e}"}), 500


if __name__ == "__main__":
    logger.info("Starting Episode 3 API on http://localhost:5000")
    app.run(debug=True, port=5000)
