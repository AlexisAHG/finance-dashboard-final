#!/bin/bash
# ============================================
# Cron Job Setup Script
# ============================================
# This script sets up the cron job for:
# 1. Daily report generation at 8 PM
# 2. App health check every 5 minutes
# 3. Weekly cleanup
#
# Usage: ./setup_cron.sh
# ============================================

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$APP_DIR/venv/bin/python"
LOGS_DIR="$APP_DIR/logs"

# Create logs directory
mkdir -p "$LOGS_DIR"

echo "🕐 Setting up cron jobs for Finance Dashboard..."
echo "   App Directory: $APP_DIR"
echo ""

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "⚠️  Virtual environment not found at $VENV_PYTHON"
    echo "   Using system Python instead"
    VENV_PYTHON="python3"
fi

# Create temporary cron file
CRON_FILE=$(mktemp)

# Preserve existing cron jobs (excluding our app's jobs)
crontab -l 2>/dev/null | grep -v "finance-dashboard" > "$CRON_FILE" || true

# Add our cron jobs
cat >> "$CRON_FILE" << EOF

# ============================================
# Finance Dashboard Cron Jobs
# ============================================

# Daily report generation at 8 PM (20:00)
0 20 * * * cd $APP_DIR && $VENV_PYTHON scripts/generate_report.py >> $LOGS_DIR/cron_report.log 2>&1 # finance-dashboard

# Health check every 5 minutes - restart app if not running
*/5 * * * * cd $APP_DIR && bash scripts/health_check.sh >> $LOGS_DIR/health_check.log 2>&1 # finance-dashboard

# Weekly cleanup of old logs (Sunday at 3 AM)
0 3 * * 0 find $LOGS_DIR -name "*.log" -mtime +7 -delete # finance-dashboard

# ============================================
EOF

# Install the cron jobs
crontab "$CRON_FILE"
rm "$CRON_FILE"

echo "✅ Cron jobs installed successfully!"
echo ""
echo "📋 Current cron jobs:"
crontab -l | grep -A 20 "Finance Dashboard"
echo ""
echo "📝 To view cron jobs: crontab -l"
echo "📝 To edit cron jobs: crontab -e"
echo "📝 Logs will be saved to: $LOGS_DIR"
