"""
Test connection to Metronome API
Episode 2: Authentication & API Basics

This script verifies that we can successfully connect to Metronome
using our API key and make a basic API call.
"""

import os
import sys
from dotenv import load_dotenv
from metronome import Metronome, AuthenticationError

# Load environment variables from .env file
load_dotenv()


# Get our API key from environment variables
bearer_token = os.environ.get('METRONOME_BEARER_TOKEN')
if not bearer_token:
    print("✗ Missing METRONOME_BEARER_TOKEN in your .env")
    print("  Create .env and set METRONOME_BEARER_TOKEN=<your_api_key>")
    sys.exit(1)

# Initialize the Metronome client
client = Metronome(bearer_token=bearer_token)

try:
    response = client.v1.customers.list()

    print("✓ Connected to Metronome!")
    if response.data:
        customer = response.data[0]
        print(f"  First customer: {customer.name}")
 
# Handle invalid or missing token
except AuthenticationError:
    print("✗ Authentication failed: invalid or missing token")
    print("  Check your METRONOME_BEARER_TOKEN and try again")

except Exception as e:
    print(f"✗ Metronome API request failed: {e}")
    print("  Check your token or network and try again")
