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

# Manually activate virtual environment
if [ -d "$VENV_PATH" ]; then
    log "Manually activating virtual environment"
    
    # Set VIRTUAL_ENV variable
    export VIRTUAL_ENV="$VENV_PATH"
    
    # Modify PATH to prioritize venv binaries
    export PATH="$VIRTUAL_ENV/bin:$PATH"
    
    # Unset PYTHONHOME to avoid conflicts
    unset PYTHONHOME
    
    # Set PS1 prompt (optional but matches activate behavior)
    PS1="(.venv) ${PS1:-}"
    
    # Verify Python is from venv
    PYTHON_PATH=$(which python)
    if [[ $PYTHON_PATH != "$VENV_PATH/bin/python" ]]; then
        log "Failed to properly set Python path from virtual environment"
        exit 1
    fi
else
    log "Virtual environment directory not found at $VENV_PATH"
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