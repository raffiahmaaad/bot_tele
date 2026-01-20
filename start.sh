#!/bin/bash
# ==============================================
# Start Backend & Frontend (Production)
# ==============================================

# Kill existing processes
pkill -f "gunicorn" 2>/dev/null
pkill -f "next-server" 2>/dev/null

# Start Backend API
echo "🚀 Starting Backend API on port 5001..."
cd api
nohup python app.py > ../logs/backend.log 2>&1 &
cd ..

# Wait for backend to start
sleep 3

# Start Frontend
echo "🌐 Starting Frontend on port 3000..."
cd web
nohup npm start > ../logs/frontend.log 2>&1 &
cd ..

echo ""
echo "✅ Application started!"
echo "   Backend:  http://localhost:5001"
echo "   Frontend: http://localhost:3000"
echo ""
echo "📋 Logs: ./logs/backend.log & ./logs/frontend.log"
