#!/bin/bash

function show_help {
    echo "Usage: ./reset.sh [--ignore-copy]"
    echo "  --ignore-copy  Don't copy from backup DB, just delete the old one"
    exit 1
}

# Parse command line arguments
IGNORE_COPY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --ignore-copy)
            IGNORE_COPY=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

echo "Stopping Evennia..."
evennia stop

echo "Waiting for processes to stop..."
sleep 2

# Remove old timestamp file if it exists
echo "Removing old timestamp file..."
rm -f server/conf/last_wipe_timestamp

# Update the last wipe timestamp
python3 - << EOF
import os
from datetime import datetime

timestamp = int(datetime.now().timestamp() * 1000)
# Use a simpler, direct path to the timestamp file
timestamp_file = 'server/conf/last_wipe_timestamp'

try:
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(timestamp_file), exist_ok=True)
    
    with open(timestamp_file, 'w') as f:
        f.write(str(timestamp))
    print(f"Created new timestamp file: {timestamp_file}")
except Exception as e:
    print(f"Error writing timestamp: {e}")
EOF

echo "Updating settings..."
# Use sed to update the settings file
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS version
    sed -i '' 's/^DEFAULT_HOME.*$/DEFAULT_HOME = "#2"/' server/conf/settings.py
    sed -i '' 's/^START_LOCATION.*$/START_LOCATION = "#2"/' server/conf/settings.py
else
    # Linux version
    sed -i 's/^DEFAULT_HOME.*$/DEFAULT_HOME = "#2"/' server/conf/settings.py
    sed -i 's/^START_LOCATION.*$/START_LOCATION = "#2"/' server/conf/settings.py
fi

# Handle database reset based on --ignore-copy flag
if [ "$IGNORE_COPY" = true ]; then
    echo "Deleting database without backup copy..."
    rm -f server/*.db3
else
    echo "Making backup copy of database..."
    if [ -f server/evennia.db3 ]; then
        cp server/evennia.db3 server/evennia.db3.bak
    fi
fi

echo "Starting Evennia..."
evennia start

# Show time since last wipe
python3 - << EOF
from datetime import datetime
import os

def time_since_wipe():
    try:
        from server.conf.last_wipe import LAST_WIPE
        now = int(datetime.now().timestamp() * 1000)
        diff = now - LAST_WIPE
        
        # Convert to seconds
        seconds = int(diff / 1000)
        
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''}"
        elif seconds < 604800:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''}"
        else:
            weeks = seconds // 604800
            return f"{weeks} week{'s' if weeks != 1 else ''}"
    except:
        return "0 seconds"

print(f"\nTime since last wipe: {time_since_wipe()}")
EOF

echo "Reset complete! You can now connect to the game." 