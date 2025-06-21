@echo off
echo ========================================
echo Starting Stock Transaction Management System
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first to set up the application
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Start the application
echo Starting the application...
echo.
echo The application will open in your default web browser
echo If it doesn't open automatically, go to: http://localhost:8501
echo.
echo To stop the application, press Ctrl+C in this window
echo.
streamlit run main.py

pause 