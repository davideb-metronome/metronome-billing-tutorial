"""
Metronome SDK wrapper

Centralizes calls to the Metronome SDK so the Flask app
can stay thin and consistent. This file will grow in later episodes.
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from metronome import Metronome


class MetronomeClient:
    def __init__(self, bearer_token: str) -> None:
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

        Required:
        - customer_id: Metronome customer ID or attached ingest alias
        - event_type: stable event name
        - timestamp: datetime for the event occurrence
        - transaction_id: unique idempotency key

        Optional:
        - properties: dict of string values
        """

        def _to_rfc3339(dt: datetime) -> str:
            """Serialize to RFC3339 (UTC, seconds, trailing Z)."""
            return dt.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


        event = {
            "customer_id": customer_id,
            "event_type": event_type,
            "timestamp": _to_rfc3339(timestamp),
            "transaction_id": transaction_id    
        }
        if properties:
            event["properties"]=properties
        
        # Ingest a single Nova event
        self.client.v1.usage.ingest(usage=[event])











































       
