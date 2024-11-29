#!/bin/bash

echo "Stopping Evennia..."
evennia stop

echo "Waiting for processes to stop..."
sleep 2

echo "Removing database..."
rm -f server/evennia.db3

echo "Restoring from backup..."
cp server/backup.evennia.db3 server/evennia.db3

echo "Updating settings..."
# Use sed to update the settings file
sed -i '' 's/^DEFAULT_HOME.*$/DEFAULT_HOME = "#2"/' server/conf/settings.py
sed -i '' 's/^START_LOCATION.*$/START_LOCATION = "#2"/' server/conf/settings.py

echo "Starting Evennia..."
evennia start

echo "Reset complete! You can now connect to the game." 