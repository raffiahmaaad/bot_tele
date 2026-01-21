#!/bin/bash
# ==============================================
# BotStore Backend - YP Cloud VPS Startup Script
# For Pterodactyl Docker (Python 3.12)
# ==============================================

echo "=========================================="
echo "🚀 BotStore Backend API"
echo "=========================================="

# Create logs directory if not exists
mkdir -p logs

# Add local bin to PATH for installed scripts
export PATH=$PATH:/home/container/.local/bin

# Get port from Pterodactyl (default to 2048)
PORT=${SERVER_PORT:-2048}

# Step 1: Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt --quiet --no-warn-script-location
if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Step 2: Run database migrations (optional)
echo ""
echo "🗄️ Checking database schema..."
if [ -f "scripts/update_schema.py" ]; then
    cd scripts
    python update_schema.py 2>/dev/null || echo "⚠️ Schema update skipped"
    cd ..
fi

# Step 3: Start the API server with Gunicorn (Production)
echo ""
echo "🌐 Starting Backend API on port $PORT..."
echo "=========================================="
cd api
gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile -
