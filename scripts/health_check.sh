#!/bin/bash
# ============================================
# Health Check Script
# ============================================
# Checks if the Streamlit app is running and
# restarts it if necessary.
#
# Designed to be run every 5 minutes via cron.
# ============================================

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$APP_DIR/app.pid"
PORT="${PORT:-8501}"
LOG_DIR="$APP_DIR/logs"

timestamp() {
    date "+%Y-%m-%d %H:%M:%S"
}

check_app() {
    # Method 1: Check PID file
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "[$(timestamp)] ✅ App is running (PID: $PID)"
            return 0
        fi
    fi
    
    # Method 2: Check if port is in use
    if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
        echo "[$(timestamp)] ✅ App is running (port $PORT is active)"
        return 0
    fi
    
    # Method 3: Check for streamlit process
    if pgrep -f "streamlit run app.py" > /dev/null; then
        echo "[$(timestamp)] ✅ App is running (process found)"
        return 0
    fi
    
    return 1
}

restart_app() {
    echo "[$(timestamp)] 🔄 Restarting app..."
    
    # Stop any existing instance
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        kill "$OLD_PID" 2>/dev/null
        rm "$PID_FILE"
    fi
    
    # Kill any orphaned streamlit processes
    pkill -f "streamlit run app.py" 2>/dev/null
    
    sleep 2
    
    # Start the app
    cd "$APP_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "$APP_DIR/venv" ]; then
        source "$APP_DIR/venv/bin/activate"
    fi
    
    nohup streamlit run app.py \
        --server.port="$PORT" \
        --server.address="0.0.0.0" \
        --server.headless=true \
        --browser.gatherUsageStats=false \
        > "$LOG_DIR/app.log" 2>&1 &
    
    echo $! > "$PID_FILE"
    
    echo "[$(timestamp)] ✅ App restarted with PID $(cat $PID_FILE)"
}

# Main logic
echo "[$(timestamp)] 🔍 Running health check..."

if check_app; then
    echo "[$(timestamp)] ✅ Health check passed"
else
    echo "[$(timestamp)] ❌ App is not running!"
    restart_app
fi
