#!/bin/bash
# Reset database and start backend server
set -e  # Exit on any error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Ensure we're using development environment
export APP_ENV=development
echo "🔧 Setting APP_ENV=development"

echo "🗃️ Setting up database..."
python backend/reset_db.py

echo "🚀 Starting backend server only..."
python backend/run.py 