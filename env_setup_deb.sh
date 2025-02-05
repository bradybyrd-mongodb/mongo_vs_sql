#!/usr/bin/env bash
echo "# --------------- Updating for Python Env -------------------------- #"
sudo apt -y update
sudo apt install -y git
git clone git@github.com:bradybyrd-mongodb/mongo_vs_sql.git
cd mongo_vs_sql
echo "# --- python version --- #"
# (must be > 3.10)
python3 --version 
sudo apt install -y python3.11-venv
python3 -m venv .venv
source .venv/bin/activate
sudo apt install -y python3-psycopg2
python3 -m pip install -r requirements.txt