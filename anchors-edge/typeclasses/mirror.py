from textwrap import fill
from evennia import DefaultObject
from server.conf.settings import CLIENT_DEFAULT_WIDTH

class Mirror(DefaultObject):
    """
    A simple mirror object that doesn't echo.
    """
    def at_object_creation(self):
        """Called when object is first created"""
        self.locks.add("get:false()")
        desc = "This ornate mirror hangs on the wall in an elaborately carved gilded frame. The glass is crystal clear, perfect for examining your appearance."
        self.db.desc = fill(desc, width=CLIENT_DEFAULT_WIDTH) 