# -*- coding: utf-8 -*-
"""
Connection screen

This is the text shown to the player when they first connect to the game.
Implements a dynamic connection screen that updates periodically.
"""

from django.conf import settings
from datetime import datetime
from evennia.utils import logger
from evennia.utils.utils import time_format
from functools import wraps
import os

def get_last_reset():
    """Get the time since last server reset"""
    try:
        # Try to get the last reset time from settings
        reset_file = os.path.join(settings.GAME_DIR, "server", "last_wipe_timestamp")
        current_time = datetime.now()
        
        if os.path.exists(reset_file):
            with open(reset_file, 'r') as f:
                timestamp = float(f.read().strip())
                reset_time = datetime.fromtimestamp(timestamp)
                # Calculate time difference
                time_diff = current_time - reset_time
                # Convert to seconds for time_format
                return time_format(time_diff.total_seconds(), 2)
        else:
            # Create file if it doesn't exist
            with open(reset_file, 'w') as f:
                f.write(str(current_time.timestamp()))
            return "Just now"
    except Exception as e:
        logger.log_err(f"Error reading last reset time: {e}")
        return "Unknown"

def get_server_stats():
    """Get current server statistics"""
    try:
        last_reset = get_last_reset()
        return {
            'last_reset': last_reset
        }
    except Exception as e:
        logger.log_err(f"Error getting server stats: {e}")
        return {
            'last_reset': "Unknown"
        }

def get_connection_screen():
    """
    Generate the connection screen with dynamic content.
    """
    stats = get_server_stats()
    
    # Build the screen with dynamic content
    screen = f"""
|=============================================================|
|                                                             |
|                  Welcome to Anchors Edge                    |
|                                                             |
|=============================================================|

|yServer Status:|n
Last Reset: {stats.get('last_reset', 'unknown')} ago
Status: Early Alpha Testing

|r== EARLY ALPHA WARNING ==|n
This game is in early alpha development. Server resets occur frequently
and without warning. All characters and progress may be wiped at any time.

|wTo create a new account:|n
    create <username> <password>

|wTo connect to an existing account:|n
    connect <username> <password>

|wTo get help once connected:|n
    help

|=============================================================|
"""
    return screen

# The callable connection screen
CONNECTION_SCREEN = get_connection_screen
