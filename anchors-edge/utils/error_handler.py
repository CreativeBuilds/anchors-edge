"""
Common error handling utilities for command sets.
"""

from evennia import logger
from evennia.accounts.models import AccountDB
from evennia.utils import logger as evennia_logger
import requests
import traceback
from datetime import datetime
from threading import Thread

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1317957206561259521/PTufBfx3veJoAmCq22B0qCJ_3k6ZJlhbyhNRjGLQqzqTt9I7aGMx7978ddzQAEoeLVvt"

def send_to_discord(message, error=None):
    """
    Send a message to Discord via webhook.
    
    Args:
        message (str): The message to send
        error (Exception, optional): The error object if this is an error message
    """
    try:
        # Create an embed for better formatting
        embed = {
            "title": "Admin Alert" if not error else "Error Alert",
            "description": message,
            "color": 0xFF0000,  # Red color for alerts
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # If there's an error, add the traceback
        if error:
            embed["fields"] = [{
                "name": "Error Details",
                "value": f"```python\n{traceback.format_exc()[:1000]}```"  # Limit to 1000 chars
            }]
        
        # Prepare the payload
        payload = {
            "embeds": [embed]
        }
        
        # Send to Discord
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code != 204:
            evennia_logger.log_err(f"Failed to send Discord webhook: {response.text}")
                    
    except Exception as e:
        evennia_logger.log_err(f"Error sending Discord webhook: {e}")

def send_to_discord_thread(message, error=None):
    """Send Discord message in a separate thread to avoid blocking."""
    thread = Thread(target=send_to_discord, args=(message, error))
    thread.daemon = True  # Thread will exit when main program exits
    thread.start()

def notify_admins(message, error=None):
    """
    Send a message to all online admin accounts and Discord.
    
    Args:
        message (str): The message to send
        error (Exception, optional): The error object if this is an error message
    """
    # Get all admin accounts
    for account in AccountDB.objects.filter(is_superuser=True):
        if account.sessions.count() > 0:  # Only message online admins
            account.msg(f"|r[Admin Alert]|n {message}")
    
    # Send to Discord in a separate thread
    send_to_discord_thread(message, error)

def handle_error(obj, err, unlogged=False):
    """
    Common error handler for all command sets.
    
    Args:
        obj (Object): The object that caused the error
        err (Exception): The error that occurred
        unlogged (bool): Whether this is for unlogged users
    
    Returns:
        bool: True to prevent default error handler from running
    """
    # Log the actual error for staff/devs
    evennia_logger.log_err(f"Command error: {err}")
    
    # Send a friendly message to the user
    if hasattr(obj, 'msg'):
        if unlogged:
            obj.msg("|rAn error occurred. Please try again or contact staff if the problem persists.|n")
        else:
            obj.msg("|rAn error occurred. The staff has been notified.|n")
        
    # If this is a serious error, also notify staff/admins
    if not isinstance(err, (TypeError, ValueError, AttributeError)):
        notify_admins(f"Serious command error: {err}", error=err)
        
    return True  # Prevents the default error handler from running