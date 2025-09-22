# Metronome Usage-Based Billing Tutorial 

This repository accompanies the [YouTube usage-based billing tutorial](https://youtube.com/playlist?list=PLUG2zXfT80sy3LGcEE7Z0XMOAB9i_4pGH&si=9ETDVYJND3P4kNBl) that integrates with Metronome’s API. Each episode builds on the previous one by adding files and features. This code includes Episode 2 (auth check) and Episode 3 (HTTP ingest endpoint).

## Prerequisites

- Python 3.9+ recommended
- A Metronome API bearer token
- Git

## Setup

1) Clone and enter the project:

```bash
git clone <your-repo-url>
cd <cloned-folder>  # replace with the folder name created by GitHub
```

2) Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# Windows (CMD):        .\.venv\Scripts\activate.bat
```

3) Install dependencies:

```bash
pip install -r requirements.txt
```

4) Configure environment variables:

```bash
cp .env.example .env
# Edit .env and set:
#   METRONOME_BEARER_TOKEN=<your_api_key>
#   DEMO_CUSTOMER_ALIAS=<your_ingest_alias>
```

## Run the API check (Episode 2)

```bash
python test_connection.py
```

Expected outcomes:
- Success: prints a checkmark and (if present) the first customer’s name.
- Authentication error: instructs you to verify `METRONOME_BEARER_TOKEN`.
- Other error: prints the error and suggests next steps.

## Episode 3: Event Ingestion (HTTP endpoint)

This episode mirrors the reference demo by exposing a minimal HTTP endpoint
that sends a usage event to Metronome using a thin SDK wrapper.

What’s new:
- `app.py` — Flask app with `POST /api/generate`.
- `services/metronome_client.py` — Minimal wrapper around the Metronome SDK.
- `config.py` — Loads env vars (e.g., `METRONOME_BEARER_TOKEN`) and shared constants.

Before sending events (one-time, via Metronome dashboard):
- Create a demo customer and add an ingest alias (e.g., `jane@nova.com`).
- Or copy an existing `customer_id` if you prefer sending by ID.


Run the API:
```bash
python app.py
```

Send an event with curl:
```bash
# Uses DEMO_CUSTOMER_ALIAS from .env; include a deterministic transaction_id
curl -s -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"tier":"ultra","transaction_id":"ep3-demo-001"}'
```

Notes:
 - This app does not create customers. It always uses `DEMO_CUSTOMER_ALIAS` from `.env`. Create a customer in the
   dashboard and attach that alias before sending events.
 - Properties are strings per Metronome docs (e.g., `"num_images": "1"`).
 - The response includes a `transaction_id` you can search in Connections → Events.


## Viewer Guide

Follow specific episode snapshots using Git tags. Episode snapshots correspond to Git tags. Note: Episode 1 had no code snapshot; the first tag with code is `ep02`. Create a branch from a tag to experiment without altering the snapshot.

```bash
# Fetch and list available episode tags
git fetch --tags
git tag --list   # see available episode tags

# Check out the first code snapshot (Episode 2)
git checkout tags/ep02

# Optional: create a working branch from the tag to avoid detached HEAD
git checkout -b ep02-playground tags/ep02

# Check out the Episode 3 snapshot
git checkout tags/ep03

# Optional: create a working branch for Episode 3
git checkout -b ep03-playground tags/ep03
```

Why branch from a tag? Checking out a tag puts you in a detached HEAD state (not on a branch). Creating a branch (e.g., `ep02-playground`) lets you make changes and commits without altering the tag, which remains an immutable snapshot.

Questions or suggestions? Open an issue or discussion in the repo.

## Resources

- Metronome Docs: https://docs.metronome.com/
- Metronome SDKs: https://docs.metronome.com/developer-resources/sdks/
