"""
Object parent class and common object types.
"""

from evennia.objects.objects import DefaultObject
from .window import Window, HarborWindow, TownWindow, TavernWindow, HallwayWindow
from .furniture import Bed, Desk, Chair, Furniture

class ObjectParent(DefaultObject):
    """
    This is the base class for all objects in the game.
    """
    pass

__all__ = [
    'ObjectParent',
    'Window',
    'HarborWindow', 
    'TownWindow',
    'TavernWindow',
    'HallwayWindow',
    'Bed',
    'Desk',
    'Chair',
    'Furniture'
]
