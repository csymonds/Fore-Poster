#!/bin/bash
# Start frontend development server
set -e  # Exit on any error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Start frontend server
echo "🚀 Starting frontend dev server..."
cd frontend
npm run dev 