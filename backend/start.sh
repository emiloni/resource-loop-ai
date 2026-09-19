#!/bin/bash
# ResourceLoop AI — Startup Script
# Usage: bash start.sh

echo "🔄 ResourceLoop AI — Starting..."
echo ""

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

# Check for PostgreSQL
echo "🗄  Checking database..."
if command -v psql &> /dev/null; then
    echo "   PostgreSQL found."
else
    echo "   ⚠️  PostgreSQL not found in PATH. Make sure it's running."
fi

# Seed database
echo "🌱 Seeding database with demo data..."
python seed_data.py

echo ""
echo "✅ Ready to start!"
echo ""
echo "🚀 Starting FastAPI server on http://localhost:8000"
echo "📖 API docs at http://localhost:8000/docs"
echo "🌐 Frontend at http://localhost:8000"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
