# Stock Transaction Management System - Windows Setup

This guide will help you set up and run the Stock Transaction Management System on Windows.

## Prerequisites

1. **Python Installation**
   - Download Python from: https://www.python.org/downloads/
   - During installation, make sure to check "Add Python to PATH"
   - Recommended version: Python 3.8 or higher

## Quick Setup (Recommended)

### Step 1: Download the Project
- Download and extract the project files to a folder on your computer
- Example: `C:\Users\YourName\Desktop\stock-ui`

### Step 2: Run Installation
1. Double-click on `install.bat`
2. The script will automatically:
   - Check if Python is installed
   - Install the uv package manager
   - Create a virtual environment
   - Install all required dependencies
3. Wait for the installation to complete
4. Press any key to close the installation window

### Step 3: Start the Application
1. Double-click on `start_app.bat`
2. The application will start and open in your default web browser
3. If it doesn't open automatically, go to: http://localhost:8501

## Manual Setup (Alternative)

If the automatic setup doesn't work, follow these manual steps:

### Step 1: Install Python
1. Go to https://www.python.org/downloads/
2. Download the latest Python version
3. Run the installer
4. **Important**: Check "Add Python to PATH" during installation
5. Click "Install Now"

### Step 2: Install uv Package Manager
1. Open Command Prompt as Administrator
2. Run this command:
   ```
   powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
   ```

### Step 3: Set Up the Project
1. Open Command Prompt
2. Navigate to the project folder:
   ```
   cd C:\path\to\your\stock-ui\folder
   ```
3. Create virtual environment:
   ```
   uv venv .venv
   ```
4. Activate virtual environment:
   ```
   .venv\Scripts\activate
   ```
5. Install dependencies:
   ```
   uv pip install -r pyproject.toml
   ```

### Step 4: Run the Application
1. In the same Command Prompt window:
   ```
   streamlit run main.py
   ```
2. The application will open in your browser at http://localhost:8501

## Troubleshooting

### Common Issues:

1. **"Python is not recognized"**
   - Reinstall Python and make sure to check "Add Python to PATH"
   - Restart your computer after installation

2. **"uv is not recognized"**
   - Run the uv installation command again
   - Restart Command Prompt after installation

3. **"Virtual environment not found"**
   - Run `install.bat` first to create the virtual environment

4. **Application won't start**
   - Make sure no other application is using port 8501
   - Try closing and reopening Command Prompt
   - Check if your antivirus is blocking the application

5. **Browser doesn't open automatically**
   - Manually go to http://localhost:8501 in your browser

### Getting Help:
- Check the main README.md for detailed feature information
- Make sure all files are in the same folder
- Try running the commands manually in Command Prompt

## Features Available

Once the application is running, you can:
- View and manage transaction history
- Configure transaction charges
- Add new transactions
- View portfolio overview
- Generate profit & loss statements
- Manage multiple demat accounts

## Stopping the Application

- Press `Ctrl+C` in the Command Prompt window
- Or close the Command Prompt window

## Updating the Application

To update the application:
1. Download the latest version
2. Replace the old files with new ones
3. Run `install.bat` again to update dependencies
4. Start the application with `start_app.bat` 