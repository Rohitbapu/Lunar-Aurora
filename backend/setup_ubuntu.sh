#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Lunar Aurora - Automated Ubuntu 24.04 Setup"
echo "=========================================================="

echo "[1/4] Updating apt and installing PostgreSQL + PostGIS..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
    postgresql postgresql-contrib postgis postgresql-16-postgis-3 \
    ffmpeg libpq-dev git

echo "[2/4] Setting up PostGIS database 'lunar_aurora'..."
sudo -u postgres psql -c "CREATE USER luna WITH PASSWORD 'aurora123';" || true
sudo -u postgres psql -c "CREATE DATABASE lunar_aurora OWNER luna;" || true
sudo -u postgres psql -d lunar_aurora -c "CREATE EXTENSION IF NOT EXISTS postgis;"

echo "[3/4] Setting up Python virtual environment and dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/4] Initializing and seeding site database..."
export ENABLE_POSTGRES=1
export POSTGIS_URL="postgresql://luna:aurora123@localhost:5432/lunar_aurora"
python3 init_db.py

echo "=========================================================="
echo " Setup Complete! Launch backend with: ./run_backend.sh"
echo "=========================================================="

