#!/usr/bin/env bash
set -e
echo "========================================================"
echo " Starting Lunar Aurora Multimodal Backend & AI Service "
echo "========================================================"
cd "$(dirname "$0")"
python3 init_db.py
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

