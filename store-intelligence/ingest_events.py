import json
import requests

events = []

with open("output/events.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            events.append(json.loads(line))

print(f"Loaded {len(events)} events")

response = requests.post(
    "http://127.0.0.1:8000/events/ingest",
    json={"events": events}
)

print(response.status_code)
print(response.json())