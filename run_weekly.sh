#!/bin/bash
#
# Weekly BioAI Newsletter Generation & Email Script
#
# This script runs the newsletter generation pipeline and emails the results.
# Designed for use with cron or other schedulers.
#
# Usage:
#   ./run_weekly.sh              # Uses .env in same directory
#   ./run_weekly.sh /path/to/.env # Uses specified env file
#
# Cron example (every Monday at 8 AM):
#   0 8 * * 1 /home/jlsteenwyk/Desktop/bioai_newsletter/run_weekly.sh >> /var/log/bioai_newsletter.log 2>&1
#

set -e  # Exit on any error

# Script directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=========================================="
log "Starting BioAI Weekly Newsletter generation"
log "=========================================="

# Determine which .env file to use
if [ -n "$1" ]; then
    ENV_FILE="$1"
else
    ENV_FILE="$SCRIPT_DIR/.env"
fi

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    log "Loading environment from: $ENV_FILE"
    set -a  # Automatically export all variables
    source "$ENV_FILE"
    set +a
else
    log "ERROR: Environment file not found: $ENV_FILE"
    log "Create a .env file with the following variables:"
    log "  ANTHROPIC_API_KEY=your-api-key"
    log "  SMTP_EMAIL=your-gmail@gmail.com"
    log "  SMTP_PASSWORD=your-app-password"
    log "  EMAIL_TO=recipient@example.com"
    exit 1
fi

# Validate required environment variables
REQUIRED_VARS=(
    "ANTHROPIC_API_KEY"
    "SMTP_EMAIL"
    "SMTP_PASSWORD"
    "EMAIL_TO"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        log "ERROR: Missing required environment variable: $var"
        exit 1
    fi
done

log "Environment variables loaded successfully"

# Change to project directory
cd "$SCRIPT_DIR"
log "Working directory: $(pwd)"

# Activate virtual environment
if [ -d "$SCRIPT_DIR/venv" ]; then
    log "Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    log "WARNING: No virtual environment found at $SCRIPT_DIR/venv"
    log "Using system Python"
fi

# Run newsletter generation
log "Starting newsletter generation (run_newsletter.py --send)..."
if python3 run_newsletter.py --send; then
    log "Newsletter generation and email completed successfully"
else
    log "ERROR: Newsletter generation failed"
    exit 1
fi

log "=========================================="
log "BioAI Weekly Newsletter complete!"
log "=========================================="
