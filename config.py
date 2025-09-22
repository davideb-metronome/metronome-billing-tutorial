"""
Basic configuration for the Episode 3

Loads environment variables and defines shared constants used across
scripts and services. 
"""

import os
from dotenv import load_dotenv

# Load variables from .env if present
load_dotenv()

# Metronome API bearer token
METRONOME_BEARER_TOKEN = os.environ.get("METRONOME_BEARER_TOKEN")

# Ingest alias for episode 3
DEMO_CUSTOMER_ALIAS = os.environ.get("DEMO_CUSTOMER_ALIAS")

# Default event name for Nova
EVENT_TYPE = "image_generation"


