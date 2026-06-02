#!/usr/bin/env python3
"""
Quick start script for Purplle Store Intelligence Platform
Initializes the database and starts the backend
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_command(cmd, description):
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        sys.exit(1)
    print(f"✅ {description} complete")

def main():
    root = Path(__file__).parent
    os.chdir(root)
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║   🏪 Purplle Store Intelligence Platform                  ║
    ║   Production Setup & Initialization                       ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check if events exist
    events_file = root / "output" / "events.jsonl"
    if not events_file.exists():
        print("⚠️  No events.jsonl found. Events will be generated from pipeline.")
    else:
        event_count = sum(1 for _ in open(events_file))
        print(f"✅ Found {event_count} events in output/events.jsonl")
    
    # Step 1: Ensure dependencies
    print("\n📦 Checking Python environment...")
    run_command(f"{sys.executable} -m pip install -q -r requirements.txt", 
                "Install Python dependencies")
    
    # Step 2: Ingest events
    print("\n📥 Ingesting events into database...")
    run_command(f"{sys.executable} scripts/ingest_jsonl.py", 
                "Event ingestion")
    
    # Step 3: Verify database
    print("\n🔍 Verifying database setup...")
    run_command(f"{sys.executable} -c \"from app.database import init_db, SessionLocal; init_db(); db = SessionLocal(); print('✅ Database ready')\"",
                "Database verification")
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║   ✅ Setup Complete!                                      ║
    ║                                                           ║
    ║   Next steps:                                             ║
    ║                                                           ║
    ║   1. Start Backend:                                       ║
    ║      uvicorn app.main:app --reload --port 8000           ║
    ║                                                           ║
    ║   2. In another terminal, start Frontend:                ║
    ║      cd frontend && npm run dev                          ║
    ║                                                           ║
    ║   3. Visit http://localhost:5173                         ║
    ║                                                           ║
    ║   🎯 Dashboard endpoints:                                 ║
    ║      GET /health                                          ║
    ║      GET /stores/ST1008/metrics                           ║
    ║      GET /stores/ST1008/funnel                            ║
    ║      GET /stores/ST1008/heatmap                           ║
    ║      GET /stores/ST1008/anomalies                         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    main()
