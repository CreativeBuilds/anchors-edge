#!/bin/bash

LOG_FILE="/home/creativebuilds/evennia_updates.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "Starting update"

cd /home/creativebuilds/anchors-edge || {
    log "Failed to change directory"
    exit 1
}

git pull || {
    log "Failed to pull changes"
    exit 1
}

. .venv/bin/activate || {
    log "Failed to activate virtual environment"
    exit 1
}

cd anchors-edge || {
    log "Failed to change directory"
    exit 1
}

evennia restart || {
    log "Failed to restart Evennia"
    exit 1
}

log "Update complete"