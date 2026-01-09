#!/bin/bash
# ============================================
# Finance Dashboard - Startup Script
# ============================================
# This script starts the Streamlit application
# and ensures it runs continuously (24/7).
#
# Usage: ./start_app.sh
# ============================================

# Configuration
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="finance-dashboard"
LOG_DIR="$APP_DIR/logs"
PID_FILE="$APP_DIR/app.pid"
PORT="${PORT:-8501}"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to start the app
start_app() {
    echo "🚀 Starting Finance Dashboard..."
    echo "   App Directory: $APP_DIR"
    echo "   Port: $PORT"
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "⚠️  App is already running with PID $OLD_PID"
            exit 1
        else
            rm "$PID_FILE"
        fi
    fi
    
    # Activate virtual environment if it exists
    if [ -d "$APP_DIR/venv" ]; then
        source "$APP_DIR/venv/bin/activate"
        echo "✅ Virtual environment activated"
    fi
    
    # Start Streamlit in background
    cd "$APP_DIR"
    nohup streamlit run app.py \
        --server.port="$PORT" \
        --server.address="0.0.0.0" \
        --server.headless=true \
        --browser.gatherUsageStats=false \
        > "$LOG_DIR/app.log" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    echo "✅ App started with PID $(cat $PID_FILE)"
    echo "📊 Dashboard available at: http://localhost:$PORT"
    echo "📝 Logs: $LOG_DIR/app.log"
}

# Function to stop the app
stop_app() {
    echo "🛑 Stopping Finance Dashboard..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            rm "$PID_FILE"
            echo "✅ App stopped"
        else
            echo "⚠️  App was not running"
            rm "$PID_FILE"
        fi
    else
        echo "⚠️  PID file not found"
    fi
}

# Function to check status
status_app() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ App is running with PID $PID"
            echo "📊 Dashboard: http://localhost:$PORT"
        else
            echo "❌ App is not running (stale PID file)"
        fi
    else
        echo "❌ App is not running"
    fi
}

# Function to restart the app
restart_app() {
    echo "🔄 Restarting Finance Dashboard..."
    stop_app
    sleep 2
    start_app
}

# Function to view logs
view_logs() {
    if [ -f "$LOG_DIR/app.log" ]; then
        tail -f "$LOG_DIR/app.log"
    else
        echo "❌ Log file not found"
    fi
}

# Main script
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        status_app
        ;;
    logs)
        view_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the dashboard"
        echo "  stop    - Stop the dashboard"
        echo "  restart - Restart the dashboard"
        echo "  status  - Check if dashboard is running"
        echo "  logs    - View live logs"
        exit 1
        ;;
esac
