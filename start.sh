#!/bin/bash
echo "=========================================="
echo "BotStore Backend + Bot Runner"
echo "=========================================="

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
    cd scripts
    python update_schema.py 2>/dev/null || echo "Schema update skipped"
    cd ..
fi

echo ""
echo "Starting Telegram Bot Runner in background..."
echo "=========================================="
python main.py > logs/bot.log 2>&1 &
BOT_PID=$!
echo "Bot Runner started with PID: $BOT_PID"

echo ""
echo "Starting Backend API on port $PORT..."
echo "=========================================="
cd api
gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile -