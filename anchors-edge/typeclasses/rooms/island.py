"""
Island-specific room types and templates.
"""

from typeclasses.rooms.base import WeatherAwareRoom
from typeclasses.rooms.weather_codes import WEATHER_CODES

class IslandRoom(WeatherAwareRoom):
    """Base class for outdoor island locations."""
    
    def at_object_creation(self):
        """Called when room is first created."""
        super().at_object_creation()
        self.db.weather_enabled = True
        self.db.weather_modifiers = {
            "sheltered": False,
            "indoor": False,
            "magical": False
        }
    
    def _get_weather_description(self, weather_data):
        """Get weather description based on current conditions."""
        if not weather_data:
            return ""
            
        weather_code = weather_data.get('weathercode')
        temp = weather_data.get('apparent_temperature', 70)
        wind_speed = weather_data.get('wind_speed_10m', 0)
        
        descriptions = []
        
        # Add temperature description
        if temp > 85:
            descriptions.append("The air is hot and humid")
        elif temp > 75:
            descriptions.append("The weather is pleasantly warm")
        elif temp > 60:
            descriptions.append("The temperature is mild")
        elif temp > 45:
            descriptions.append("There's a noticeable chill in the air")
        else:
            descriptions.append("The air is quite cold")
            
        # Add wind description
        if wind_speed > 20:
            descriptions.append("strong winds whip through the area")
        elif wind_speed > 10:
            descriptions.append("a steady breeze blows")
        elif wind_speed > 5:
            descriptions.append("a gentle breeze stirs the air")
            
        # Add weather condition description
        if weather_code in WEATHER_CODES["thunderstorm"]:
            descriptions.append("thunder rumbles overhead as lightning flashes across the sky")
        elif weather_code in WEATHER_CODES["rain"]:
            descriptions.append("rain falls steadily")
        elif weather_code in WEATHER_CODES["cloudy"]:
            descriptions.append("clouds fill the sky")
            
        # Combine descriptions
        if descriptions:
            weather_desc = ", ".join(descriptions)
            return f"\nThe weather: {weather_desc}."
        return ""