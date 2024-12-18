"""
Room type definitions.
"""

from typeclasses.rooms.base import WeatherAwareRoom
from typeclasses.rooms.tavern import TavernRoom
from typeclasses.rooms.island import IslandRoom
from typeclasses.rooms.harbor import HarborRoom
from typeclasses.rooms.weather_codes import WEATHER_CODES

__all__ = [
    'WeatherAwareRoom',
    'TavernRoom',
    'IslandRoom',
    'HarborRoom',
    'WEATHER_CODES'
] 