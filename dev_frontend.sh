#!/bin/bash
# Start frontend development server
set -e  # Exit on any error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if symbolic link for .env exists
if [ ! -L "frontend/.env" ]; then
  echo "⚠️ frontend/.env symlink not found, creating it..."
  [ -f "frontend/.env" ] && mv frontend/.env frontend/.env.bak
  ln -s ../.env frontend/.env
  echo "✅ Created symlink frontend/.env -> ../.env"
fi

# Start frontend server
echo "🚀 Starting frontend dev server..."
cd frontend
npm run dev 