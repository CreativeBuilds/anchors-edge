#!/bin/bash

LOG_FILE="/home/creativebuilds/evennia_updates.log"
GAME_DIR="/home/creativebuilds/anchors-edge"
VENV_PATH="$GAME_DIR/.venv"
PYTHON_BIN="$VENV_PATH/bin/python"
PIP_BIN="$VENV_PATH/bin/pip"

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

# Verify Python exists in venv
if [ ! -f "$PYTHON_BIN" ]; then
    log "Python not found at $PYTHON_BIN"
    exit 1
fi

if [ ! -f "$PIP_BIN" ]; then
    log "Pip not found at $PIP_BIN"
    exit 1
fi

# Update requirements
log "Updating requirements"
"$PIP_BIN" install -r requirements.txt || {
    log "Failed to install requirements"
    exit 1
}

# Ensure evennia is installed
log "Installing/updating evennia"
"$PIP_BIN" install --upgrade evennia || {
    log "Failed to install/update evennia"
    exit 1
}

# Now get the evennia binary path after installation
EVENNIA_BIN="$VENV_PATH/bin/evennia"

if [ ! -f "$EVENNIA_BIN" ]; then
    log "Evennia not found at $EVENNIA_BIN even after installation"
    exit 1
fi

# Change to game directory
cd "$GAME_DIR/anchors-edge" || {
    log "Failed to change directory to $GAME_DIR/anchors-edge"
    exit 1
}

# Restart Evennia using full path
"$EVENNIA_BIN" restart || {
    log "Failed to restart Evennia"
    exit 1
}

log "Update complete" 