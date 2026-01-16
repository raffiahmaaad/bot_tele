@echo off
REM ============================================
REM  Digital Store Bot - Windows Service Script
REM ============================================

echo Starting Digital Store Bot...

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the bot
python main.py

pause
