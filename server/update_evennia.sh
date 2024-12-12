#!/bin/bash

LOG_FILE="/home/creativebuilds/evennia_updates.log"
GAME_DIR="/home/creativebuilds/anchors-edge"
VENV_PATH="$GAME_DIR/.venv"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "Starting update"

# Change to game directory
cd "$GAME_DIR" || {
    log "Failed to change directory to $GAME_DIR"
    exit 1
}

# Pull latest changes
git pull || {
    log "Failed to pull changes"
    exit 1
}

# Activate the virtual environment activation script
if [ -f "$VENV_PATH/bin/activate" ]; then
    log "Activating virtual environment"
    . "$VENV_PATH/bin/activate" || {
        log "Failed to activate virtual environment at $VENV_PATH"
        exit 1
    }
else
    log "Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Verify evennia is available
if ! command -v evennia &> /dev/null; then
    log "Evennia command not found even after activating virtual environment"
    exit 1
fi

# Change to game directory
cd "$GAME_DIR/anchors-edge" || {
    log "Failed to change directory to $GAME_DIR/anchors-edge"
    exit 1
}

# Restart Evennia
evennia restart || {
    log "Failed to restart Evennia"
    exit 1
}

log "Update complete"

# Deactivate virtual environment
deactivate