@echo off
REM Setup script for Risk Assessment Workflow (Windows)

echo ================================
echo Risk Assessment Workflow Setup
echo ================================
echo.

REM Check Python
echo Checking Python version...
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
echo Virtual environment created
echo.

REM Activate and install
echo Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Dependencies installed
echo.

REM Create .env file
if not exist .env (
    echo Creating .env file...
    copy env.example .env
    echo .env file created
    echo.
    echo WARNING: Edit .env and add your API keys:
    echo    - GOOGLE_API_KEY (get from https://aistudio.google.com/app/apikey^)
    echo    - TAVILY_API_KEY (get from https://tavily.com/^)
) else (
    echo .env file already exists
)

echo.
echo ================================
echo Setup Complete!
echo ================================
echo.
echo Next steps:
echo 1. Edit .env and add your API keys
echo 2. Run an assessment:
echo    python run.py --software "Tiles" --company "Shopify"
echo.
pause

