#!/bin/bash
# Setup script for Fore-Poster project
# Sets up environment and ensures .env linking is correct

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
  echo "⚠️  No .env file found!"
  if [ -f .env.example ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please update it with your settings."
  else
    echo "❌ .env.example not found. Please create a .env file manually."
    exit 1
  fi
fi

# Ensure frontend .env is a symbolic link to root .env
if [ -f frontend/.env ] && [ ! -L frontend/.env ]; then
  echo "⚠️  frontend/.env exists but is not a symbolic link."
  echo "Backing up to frontend/.env.bak and creating symbolic link..."
  mv frontend/.env frontend/.env.bak
  ln -s ../.env frontend/.env
  echo "✅ Created symbolic link frontend/.env -> ../.env"
elif [ ! -f frontend/.env ]; then
  echo "Creating symbolic link for frontend/.env..."
  ln -s ../.env frontend/.env
  echo "✅ Created symbolic link frontend/.env -> ../.env"
else
  echo "✅ frontend/.env is already set up correctly as a symbolic link."
fi

# Check for Python virtual environment
if [ ! -d "venv" ]; then
  echo "⚠️  No Python virtual environment found."
  echo "Creating virtual environment..."
  python3 -m venv venv
  echo "✅ Created virtual environment."
fi

# Check if we should install dependencies
echo -n "Install/update Python dependencies? (y/n) "
read install_deps
if [[ $install_deps == "y" || $install_deps == "Y" ]]; then
  echo "Installing Python dependencies..."
  source venv/bin/activate
  pip install -r requirements.txt
  echo "✅ Python dependencies installed."
fi

# Install frontend dependencies
echo -n "Install/update frontend dependencies? (y/n) "
read install_frontend
if [[ $install_frontend == "y" || $install_frontend == "Y" ]]; then
  echo "Installing frontend dependencies..."
  cd frontend
  npm install
  cd ..
  echo "✅ Frontend dependencies installed."
fi

# Ensure dev testing scripts are executable
echo "Setting up development testing scripts..."
chmod +x dev_backend.sh
chmod +x dev_frontend.sh
echo "✅ Development testing scripts are ready to use."

echo "🚀 Fore-Poster setup complete!"
echo ""
echo "To run the application using the dev scripts:"
echo "  1. Start the backend:  ./dev_backend.sh"
echo "  2. In another terminal: ./dev_frontend.sh"
echo ""
echo "Or run manually:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Start the backend: python backend/run.py"
echo "  3. In another terminal: cd frontend && npm run dev"
echo "" 