#!/bin/bash
# Auto-start the data collection scheduler
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"

source .venv/bin/activate
export NO_PROXY='*'
export PYTHONUNBUFFERED=1

exec python scripts/run_scheduler.py
