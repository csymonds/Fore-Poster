#!/bin/bash
# Reset database and start backend server
set -e  # Exit on any error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🔄 Activating virtual environment..."
source venv/bin/activate || {
  echo "❌ Failed to activate virtual environment. Is it created?"
  echo "   Run ./setup.sh to create it"
  exit 1
}

echo "🗃️ Setting up database..."
python backend/reset_db.py

echo "⏰ Do you want to start the scheduler too? (y/n)"
read start_scheduler

# Start the backend and optionally the scheduler
if [[ "$start_scheduler" == "y" || "$start_scheduler" == "Y" ]]; then
  echo "🚀 Starting backend server and scheduler..."
  echo "📝 Backend logs will appear below. Scheduler logs go to scheduler.log"
  echo "👉 Press Ctrl+C to stop both services"
  
  # Start scheduler in background
  python backend/fore_scheduler.py > scheduler.log 2>&1 &
  SCHEDULER_PID=$!
  
  # Trap to kill scheduler when this script exits
  trap "echo '🛑 Stopping services...'; kill $SCHEDULER_PID 2>/dev/null; echo '✅ Services stopped'" EXIT
  
  # Start backend in foreground
  python backend/run.py
else
  echo "🚀 Starting backend server only..."
  python backend/run.py
fi 