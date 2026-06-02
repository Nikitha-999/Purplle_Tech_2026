import json
from datetime import datetime

with open('output/events.jsonl', 'r') as f:
    line = f.readline()
    event = json.loads(line)
    ts = event.get('timestamp')
    print(f"First event timestamp: {ts}")
    if ts:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        print(f"Date: {dt.date()}")
