#!/usr/bin/env bash
set -e

echo "============================="
echo " GRAMGPT — Server Setup"
echo "============================="

# --- Check prerequisites ---
command -v python3 >/dev/null 2>&1 || { echo "Need Python 3.12+"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "Need git"; exit 1; }

# --- Clone / update ---
if [ ! -d "GRAMGPT" ]; then
    git clone https://github.com/your-org/GRAMGPT.git
    cd GRAMGPT
else
    cd GRAMGPT
    git pull
fi

# --- Python venv ---
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# --- Dependencies ---
pip install --upgrade pip
pip install -r requirements.txt

# --- Environment ---
if [ ! -f ".env.local" ]; then
    cp .env.example .env.local
    echo ""
    echo "============================================="
    echo " EDIT .env.local with your credentials:"
    echo "   nano .env.local"
    echo ""
    echo " Required: TELEGRAM_API_ID, TELEGRAM_API_HASH,"
    echo "           TELEGRAM_PHONE, OPENAI_API_KEY"
    echo "============================================="
fi

# --- Optional: Redis ---
if command -v redis-server >/dev/null 2>&1; then
    echo "Redis found — distributed task queue available"
else
    echo "Redis not found — tasks will run inline (no Redis needed)"
fi

# --- Data dirs ---
mkdir -p data/sessions

echo ""
echo "============================="
echo " Setup complete!"
echo ""
echo " Start:    python run.py"
echo " Docs:     http://localhost:8000/docs"
echo " Health:   http://localhost:8000/api/v1/health"
echo "============================="
