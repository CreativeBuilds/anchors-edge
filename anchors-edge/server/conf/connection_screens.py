# -*- coding: utf-8 -*-
"""
Connection screen

This is the text shown to the player when they first connect to the game.
"""

from django.conf import settings
from datetime import datetime

def get_time_since_wipe():
    """Get time since last server wipe in human-readable format"""
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
        return "unknown time"

# Define the connection screen as a string
CONNECTION_SCREEN = """
|=============================================================|
|                                                             |
|                  Welcome to Anchors Edge                    |
|                                                             |
|=============================================================|

|yServer Status:|n
Last Reset: %s ago
Server Status: Early Alpha Testing

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
""" % get_time_since_wipe()
