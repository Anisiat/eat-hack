import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

token = os.getenv("PREDICTHQ_TOKEN", "").strip()
if not token:
    raise SystemExit("Set PREDICTHQ_TOKEN in the project .env file or your environment.")

try:
    response = requests.get(
        "https://api.predicthq.com/v1/events/",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        params={
            "country": "GB",
            "limit": 5,
        },
        timeout=30,
    )
except requests.RequestException:
    raise SystemExit("Could not reach PredictHQ. Check your connection and try again.")

print("Status code:", response.status_code)

if response.status_code == 401:
    raise SystemExit(
        "PredictHQ rejected PREDICTHQ_TOKEN (401). Replace it with a valid API token "
        "from PredictHQ's API Tokens page. Check for an old exported PREDICTHQ_TOKEN "
        "overriding your .env file."
    )
if response.status_code == 403:
    raise SystemExit("PredictHQ denied access (403). Check your token's events permissions.")
if not response.ok:
    raise SystemExit(f"PredictHQ request failed (HTTP {response.status_code}).")

try:
    data = response.json()
except ValueError:
    raise SystemExit("PredictHQ returned an invalid JSON response.")

results = data.get("results") if isinstance(data, dict) else None
if not isinstance(results, list):
    raise SystemExit("PredictHQ returned an unexpected response: missing results list.")
if results:
    print(results[0])
else:
    print("No events matched your query.")
