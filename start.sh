#!/bin/bash
echo "=========================================="
echo "BotStore Backend + Bot Runner"
echo "=========================================="

# Store the root directory
ROOT_DIR=$(pwd)
mkdir -p logs
export PATH=$PATH:/home/container/.local/bin
PORT=${SERVER_PORT:-2048}

echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "Dependencies installed"
else
    echo "Failed to install dependencies"
    exit 1
fi

echo ""
echo "Checking database schema..."
if [ -f "scripts/update_schema.py" ]; then
    python scripts/update_schema.py 2>/dev/null || echo "Schema update skipped"
fi

echo ""
echo "Starting Telegram Bot Runner in background..."
echo "=========================================="
# Run from root directory and log both stdout and stderr
cd "$ROOT_DIR"
python main.py >> logs/bot.log 2>&1 &
BOT_PID=$!
echo "Bot Runner started with PID: $BOT_PID"

# Wait a moment and check if bot is still running
sleep 3
if kill -0 $BOT_PID 2>/dev/null; then
    echo "Bot Runner is running successfully"
else
    echo "WARNING: Bot Runner may have crashed! Check logs/bot.log"
    cat logs/bot.log 2>/dev/null | tail -20
fi

echo ""
echo "Starting Backend API on port $PORT..."
echo "=========================================="
cd "$ROOT_DIR/api"

# Ensure PYTHONPATH includes current directory
export PYTHONPATH="$ROOT_DIR/api:$PYTHONPATH"

# Check if app.py exists
if [ -f "app.py" ]; then
    echo "Found app.py in $(pwd)"
    gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile -
else
    echo "ERROR: app.py not found in $(pwd)"
    ls -la
    exit 1
fi