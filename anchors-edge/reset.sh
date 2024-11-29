#!/bin/bash

echo "Stopping Evennia..."
evennia stop

echo "Waiting for processes to stop..."
sleep 2

echo "Running world cleanup..."
# Create a temporary Python script to run the cleanup
cat << EOF > cleanup_temp.py
from evennia.utils import create_script
create_script('typeclasses.scripts.cleanup.WorldCleanupScript').clean_world()
EOF

# Run the cleanup script
evennia shell < cleanup_temp.py
rm cleanup_temp.py

echo "Updating settings..."
# Use sed to update the settings file
sed -i '' 's/^DEFAULT_HOME.*$/DEFAULT_HOME = "#2"/' server/conf/settings.py
sed -i '' 's/^START_LOCATION.*$/START_LOCATION = "#2"/' server/conf/settings.py

echo "Starting Evennia..."
evennia start

echo "Reset complete! You can now connect to the game." 