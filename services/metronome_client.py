"""
Metronome SDK wrapper

Centralizes calls to the Metronome SDK so the Flask app
can stay thin and consistent. This file will grow in later episodes.


Notes
- Per Metronome guidance, event property keys and values should be strings
  (even numeric-looking values like "1"). Metronome parses numeric strings
  with arbitrary-precision decimals for aggregation.
- Timestamps must be RFC3339 strings in UTC with a trailing "Z".
"""

from datetime import datetime, timezone
from typing import Dict, Optional, List

from metronome import Metronome
from config import BILLABLE_GROUP_KEYS


class MetronomeClient:
    def __init__(self, bearer_token: str) -> None:
        """Initialize the official Metronome SDK client."""
        self.client = Metronome(bearer_token=bearer_token)

    # ---- Usage ingestion (single-event convenience) ----
    def send_usage_event(
        self,
        *,
        customer_id: str,
        event_type: str,
        properties: Optional[Dict] = None,
        timestamp: datetime,
        transaction_id: str,
    ) -> None:
        """Send a single usage event.

        Required
        - customer_id: Metronome customer ID or attached ingest alias
        - event_type: stable event name
        - timestamp: timezone-aware datetime for the event occurrence
        - transaction_id: unique idempotency key (enables safe retries)

        Optional
        - properties: dict of string values (per Metronome guidelines)
        """

        def _to_rfc3339(dt: datetime) -> str:
            """Serialize to RFC3339 (UTC, seconds, trailing Z).

            Expects an aware datetime. If a naive datetime is supplied,
            Python will raise when converting timezones. Callers should pass
            `datetime.now(timezone.utc)` or otherwise ensure tz-aware values.
            """
            return dt.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


        event = {
            # Identify the customer (ID or ingest alias)
            "customer_id": customer_id,
            # Stable event name; metrics target this via event_type_filter
            "event_type": event_type,
            # RFC3339 UTC timestamp with trailing Z
            "timestamp": _to_rfc3339(timestamp),
            # Idempotency key to deduplicate retries
            "transaction_id": transaction_id
        }
        if properties:
            # Forward properties as provided. Per docs, keys/values should be strings.
            event["properties"] = properties
        
        # Ingest a single Nova event
        self.client.v1.usage.ingest(usage=[event])

    # ---- Billable metrics ----
    def create_billable_metric(
        self,
        *,
        name: str,
        event_type: str,
        aggregation_type: str = "SUM",
        aggregation_key: Optional[str] = "num_images",
        group_keys: Optional[List[List[str]]] = None,
        property_filters: Optional[List[Dict]] = None,
    ) -> Dict:
        """Create a billable metric for the given event type.

        Defaults target the demo's dimensional pricing setup:
        - aggregation_type: "SUM"
        - aggregation_key: "num_images" (sent as a numeric string in events)
        - group_keys: defaults to config.BILLABLE_GROUP_KEYS (segment by image type)

        Parameters
        - name: display name for the metric
        - event_type: the event this metric aggregates ("image_generation" for our demo)
        - aggregation_type: SUM for our demo
        - aggregation_key: required for numeric aggregations ("num_images" for our demo)
        - group_keys: list of lists of property names for dimensional breakdowns
                      (shape must be e.g., [["image_type"], ["region"]])
        - property_filters: optional filters; e.g., require fields to exist
          [{"name": "image_type", "exists": True}, {"name": "num_images", "exists": True}]
        """

        params: Dict = {
            "name": name,
            "aggregation_type": aggregation_type,
            "event_type_filter": {"in_values": [event_type]},
        }
        if aggregation_key:
            params["aggregation_key"] = aggregation_key
        # Use provided group_keys or fall back to immutable config default
        keys = group_keys if group_keys is not None else BILLABLE_GROUP_KEYS
        params["group_keys"] = [list(x) for x in keys]
        if property_filters:
            params["property_filters"] = property_filters

        resp = self.client.v1.billable_metrics.create(**params)
        return resp.data.model_dump() if hasattr(resp, "data") else {}











































       
