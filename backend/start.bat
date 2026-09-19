@echo off
REM ResourceLoop AI — Windows Startup Script

echo 🔄 ResourceLoop AI — Starting...
echo.

REM Check for virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt -q

REM Seed database
echo 🌱 Seeding database with demo data...
python seed_data.py

echo.
echo ✅ Ready to start!
echo.
echo 🚀 Starting FastAPI server on http://localhost:8000
echo 📖 API docs at http://localhost:8000/docs
echo 🌐 Frontend at http://localhost:8000
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
