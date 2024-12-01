"""
Last server wipe timestamp
"""
from datetime import datetime
import os

TIMESTAMP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_wipe_timestamp')

def get_or_create_timestamp():
    """Get existing timestamp or create a new one"""
    try:
        # Try to read existing timestamp
        if os.path.exists(TIMESTAMP_FILE):
            with open(TIMESTAMP_FILE, 'r') as f:
                timestamp = int(f.read().strip())
                if timestamp > 0:
                    return timestamp
        
        # Create new timestamp if file doesn't exist or is invalid
        timestamp = int(datetime.now().timestamp() * 1000)
        with open(TIMESTAMP_FILE, 'w') as f:
            f.write(str(timestamp))
        return timestamp
    except Exception as e:
        print(f"Error with timestamp file: {e}")
        # Return current time if anything goes wrong
        return int(datetime.now().timestamp() * 1000)

# Set the timestamp
LAST_WIPE = get_or_create_timestamp()