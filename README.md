# Usage-Based Billing Tutorial | Episode 2: Authentication and API basics

This repository accompanies the [YouTube usage-based billing tutorial](https://youtube.com/playlist?list=PLUG2zXfT80sy3LGcEE7Z0XMOAB9i_4pGH&si=9ETDVYJND3P4kNBl) that integrates with Metronome’s API. Each episode builds on the previous one by adding files and features. The current snapshot includes a basic authentication check to Metronome.

## What’s Here

- `test_connection.py` — Verifies authentication and performs a simple API call (`customers.list`).
- `requirements.txt` — Python dependencies for the scripts.
- `.env.example` — Template for required environment variables.
- `.gitignore` — Git ignore rules (updated to avoid committing secrets and Python artifacts).

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
# Edit .env and set METRONOME_BEARER_TOKEN=<your_api_key>
```

## Run the API check

```bash
python test_connection.py
```

Expected outcomes:
- Success: prints a checkmark and (if present) the first customer’s name.
- Authentication error: instructs you to verify `METRONOME_BEARER_TOKEN`.
- Other error: prints the error and suggests next steps.

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
```

Why branch from a tag? Checking out a tag puts you in a detached HEAD state (not on a branch). Creating a branch (e.g., `ep02-playground`) lets you make changes and commits without altering the tag, which remains an immutable snapshot.

Questions or suggestions? Open an issue or discussion in the repo.

## Resources

- Metronome Docs: https://docs.metronome.com/
- Metronome SDKs: https://docs.metronome.com/developer-resources/sdks/
