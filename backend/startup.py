#!/usr/bin/env python3
"""
Startup script to run before the FastAPI app starts.
This runs AFTER disk mounts, so ChromaDB persistence works.
"""
import subprocess
import sys
from pathlib import Path

def run_ingestion():
    """Run compliance guide ingestion if needed."""
    print("\n" + "="*70)
    print("STARTUP: Running ingestion check...")
    print("="*70)

    # Run the ingestion script (it will skip if data exists)
    result = subprocess.run(
        [sys.executable, "ingest_full_guide.py"],
        cwd=Path(__file__).parent,
        capture_output=False
    )

    if result.returncode != 0:
        print("⚠️  WARNING: Ingestion script failed, but continuing startup")

    print("="*70)
    print("STARTUP: Ingestion check complete")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_ingestion()
