"""
Common error handling utilities for command sets.
"""

from evennia import logger
from evennia.utils.utils import notify_admin

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
    logger.log_err(f"Command error: {err}")
    
    # Send a friendly message to the user
    if hasattr(obj, 'msg'):
        if unlogged:
            obj.msg("|rAn error occurred. Please try again or contact staff if the problem persists.|n")
        else:
            obj.msg("|rAn error occurred. The staff has been notified.|n")
        
    # If this is a serious error, also notify staff/admins
    if not isinstance(err, (TypeError, ValueError, AttributeError)):
        notify_admin(f"Serious command error: {err}")
        
    return True  # Prevents the default error handler from running 