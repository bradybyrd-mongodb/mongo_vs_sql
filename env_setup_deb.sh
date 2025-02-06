#!/usr/bin/env bash
echo "# --------------- Updating for Python Env -------------------------- #"
sudo apt -y update
sudo apt install -y git
#git clone git@github.com:bradybyrd-mongodb/mongo_vs_sql.git
git clone https://github.com/bradybyrd-mongodb/mongo_vs_sql.git
cd mongo_vs_sql
echo "# --- Python Version --- #"
# (must be > 3.10)
python3 --version 
sudo apt install -y python3.11-venv
sudo apt install python3-pip -y
#sudo apt install -y python3-psycopg2
#python3 -m venv .venv --system-site-packages
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
echo "# --- Install Python Packages --- #"
python3 -m pip install -r requirements.txt
echo "# -------------------- INFO --------------------------- #"
echo "  Remember to set an environment variable for your passwords"
echo "  export _PWD_=<my mongodb password>"
echo "  export _PGPWD_=<my postgres password>"
cd mongo_vs_sql