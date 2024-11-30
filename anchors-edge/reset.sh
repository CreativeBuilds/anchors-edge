#!/bin/bash

echo "Stopping Evennia..."
evennia stop

echo "Waiting for processes to stop..."
sleep 2

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

echo "Starting Evennia..."
evennia start

echo "Reset complete! You can now connect to the game." 