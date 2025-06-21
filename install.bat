@echo off
echo ========================================
echo Stock Transaction Management System
echo ========================================
echo.
echo This script will set up the Stock Transaction Management System
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python is installed. Checking version...
python --version

REM Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo Installing uv package manager...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo ERROR: Failed to install uv
        echo Please install uv manually from https://github.com/astral-sh/uv
        pause
        exit /b 1
    )
)

echo uv is installed. Creating virtual environment...
uv venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing dependencies...
uv pip install -r pyproject.toml

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To start the application, run: start_app.bat
echo.
pause 