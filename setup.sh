#!/bin/bash

# Exit on error
set -e

echo "🚀 Setting up the Stock Agent environment..."

# Check if python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ python3 could not be found. Please install it first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📁 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists."
fi

# Activate environment and install dependencies
echo "📦 Installing dependencies from requirements.txt..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from .env.example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
else
    echo "✅ .env file already exists."
fi

echo "🔐 Gemini CLI Setup:"
if ! command -v gemini &> /dev/null
then
    echo "🔍 'gemini' CLI not found. Attempting to install via npm..."
    if ! command -v npm &> /dev/null
    then
        echo "❌ 'npm' not found. Please install Node.js/npm first to enable 'gemini-cli'."
    else
        echo "📦 Installing gemini-cli globally..."
        npm install -g gemini-cli
        echo "✅ 'gemini-cli' installed successfully."
    fi
else
    echo "✅ 'gemini' CLI tool found."
fi

echo "------------------------------------------------"
echo "🎉 Setup complete!"
echo "To start working, run:"
echo "    source venv/bin/activate"
echo "    python -m app.main"
echo "------------------------------------------------"
