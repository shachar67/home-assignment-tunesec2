#!/bin/bash
# Setup script for Risk Assessment Workflow

echo "================================"
echo "Risk Assessment Workflow Setup"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Found: Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - GOOGLE_API_KEY (get from https://aistudio.google.com/app/apikey)"
    echo "   - TAVILY_API_KEY (get from https://tavily.com/)"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Run an assessment:"
echo "   python run.py --software \"Tiles\" --company \"Shopify\""
echo ""

