#!/bin/bash
# ==============================================
# BotStore VPS Deployment Script
# ==============================================

echo "=========================================="
echo "🚀 BotStore Deployment"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found!"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Step 1: Install Python dependencies
echo ""
echo "📦 Step 1: Installing Python dependencies..."
pip install -r requirements.txt --quiet
if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Step 2: Setup database tables
echo ""
echo "🗄️ Step 2: Setting up database..."
cd scripts
python update_schema.py
if [ $? -eq 0 ]; then
    echo "✅ Database tables ready"
else
    echo "⚠️ Database setup warning (tables may already exist)"
fi
cd ..

# Step 3: Build frontend
echo ""
echo "🌐 Step 3: Building frontend..."
cd web
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install --silent
fi
npm run build
if [ $? -eq 0 ]; then
    echo "✅ Frontend built successfully"
else
    echo "❌ Failed to build frontend"
    exit 1
fi
cd ..

echo ""
echo "=========================================="
echo "✅ Deployment preparation complete!"
echo "=========================================="
echo ""
echo "To start the application, run:"
echo "  Backend:  cd api && python app.py"
echo "  Frontend: cd web && npm start"
echo ""
