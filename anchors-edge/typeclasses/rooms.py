"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia.objects.objects import DefaultRoom

from datetime import datetime
import time
from evennia import TICKER_HANDLER
import pytz
import requests
import json
from textwrap import fill


class Room(DefaultRoom):
    """
    Rooms are simple containers that has no location of their own.
    """
    pass


class WeatherAwareRoom(DefaultRoom):
    """
    A room that uses Claude Sonnet via OpenRouter API to generate weather-aware descriptions
    """
    
    def at_object_creation(self):
        """Called when room is first created"""
        super().at_object_creation()
        
        # Weather data storage
        self.db.weather_data = {}
        self.db.last_weather_update = 0
        
        # Cache for weather-modified descriptions
        self.db.cached_descriptions = {
            "dawn": None,
            "day": None,
            "dusk": None,
            "night": None
        }
        self.db.cache_timestamps = {
            "dawn": 0,
            "day": 0,
            "dusk": 0,
            "night": 0
        }
        
        # Location for weather (Turks and Caicos)
        self.db.latitude = 21.4655745
        self.db.longitude = -71.1390341
        
        # Start the weather update ticker (every 15 minutes)
        TICKER_HANDLER.add(60 * 15, self.update_weather)
        
    def get_openrouter_description(self, base_desc, weather_data):
        """Get AI-generated weather-influenced description using Claude Sonnet"""
        import os
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Weather code interpretation
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        
        # Get weather condition description
        weather_code = weather_data.get('weather_code', 0)
        weather_desc = weather_codes.get(weather_code, "Unknown weather")
        
        # Simplified weather conditions for the prompt
        conditions = (
            f"The weather outside is {weather_desc}. "
            f"The wind is blowing at {weather_data.get('wind_speed_10m', 0)} mph "
            f"with gusts up to {weather_data.get('wind_gusts_10m', 0)} mph. "
            f"The sky is {weather_data.get('cloud_cover', 0)}% covered in clouds. "
            f"The temperature feels like {weather_data.get('apparent_temperature', 0)}°F."
        )
        
        prompt = (
            "You are a descriptive writer for a text-based game. "
            f"Here is a base description of a ship's holding cell:\n\n{base_desc}\n\n"
            f"Current weather conditions: {conditions}\n\n"
            "Create a new description that incorporates these weather conditions. Focus on how "
            "the weather affects the atmosphere, lighting, sounds, and movement of the ship. "
            "Ensure the description is logically consistent with the current weather (for example, "
            "no direct moonlight if it's cloudy). Keep the same tone and approximate length as "
            "the original description. Do not generate more than one paragraph. Five sentences or less."
        )

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:4001", 
            "X-Title": "Anchors Edge MUD"
        }
        
        data = {
            "model": "anthropic/claude-3-sonnet",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5,
            "max_tokens": 256
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                x = response.json()['choices'][0]['message']['content'].strip()
                # replace the text "\n\n" with actual newlines
                return x.replace("\\n", "\n")
        except Exception as e:
            print(f"OpenRouter API error: {e}")
        return base_desc

    def get_weather_data(self):
        """Fetch current weather data from Open-Meteo API"""
        lat = 21.4655745
        lon = -71.1390341
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=apparent_temperature,precipitation,rain,showers,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timezone=America%2FChicago"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()['current']
            
        except Exception as e:
            print(f"Weather API error: {e}")
        return None
        
    def update_weather(self, *args, **kwargs):
        """Update the room's weather data and description"""
        weather_data = self.get_weather_data()
        if weather_data:
            self.db.weather_data = weather_data
            self.db.last_weather_update = datetime.now().timestamp()
            
            # Only update description if weather has changed significantly
            if self.should_update_description(weather_data):
                self.update_description()

    def should_update_description(self, new_weather):
        """Check if weather has changed enough to warrant a new description"""
        old_weather = self.db.weather_data
        
        # Check significant changes in wind speed or cloud cover
        if (abs(new_weather.get('wind_speed_10m', 0) - old_weather.get('wind_speed_10m', 0)) > 5 or
            abs(new_weather.get('cloud_cover', 0) - old_weather.get('cloud_cover', 0)) > 20):
            return True
        return False

    def update_description(self):
        """Update only the current time period's description and clear brief description"""
        current_period = self.get_time_period()
        base_desc = self.db.desc_base[current_period]
        
        # Always fetch fresh weather data if needed
        if not self.db.weather_data:
            self.db.weather_data = self.get_weather_data()
        
        # Always get a new description from OpenRouter
        weather_desc = self.get_openrouter_description(base_desc, self.db.weather_data)
        self.db.cached_descriptions[current_period] = weather_desc
        self.db.cache_timestamps[current_period] = time.time()
        print(f"Updated cached description for {current_period}")
        
        # Set the current description
        self.db.desc = weather_desc
        
        # Clear the brief description so it will be regenerated next time it's needed
        self.db.brief_desc = None
        
        return weather_desc

    def get_time_of_day(self):
        """Get the current hour in the configured timezone"""
        tz = pytz.timezone('America/Chicago')
        now = datetime.now(tz)
        return now.hour


class DynamicHoldingCell(WeatherAwareRoom):
    """
    A holding cell that changes based on time and weather conditions
    """
    
    def at_object_creation(self):
        """Called when room is first created"""
        super().at_object_creation()
        
        # Store base descriptions for different times
        self.db.desc_base = {
            "dawn": (
                "You find yourself in a cramped holding cell aboard what appears to be "
                "a ship. The first hints of dawn filter through the barred window, painting "
                "the cell in soft greys and blues. A heavy wooden door blocks the only exit. "
                "In the corner sits a simple wooden bucket filled with water, its surface "
                "occasionally rippling with the ship's movement."
            ),
            "day": (
                "You find yourself in a cramped holding cell aboard what appears to be "
                "a ship. Bright sunlight streams through the barred window, illuminating "
                "dust particles dancing in the air. A heavy wooden door blocks the only exit. "
                "In the corner sits a simple wooden bucket filled with water, its surface "
                "occasionally rippling with the ship's movement."
            ),
            "dusk": (
                "You find yourself in a cramped holding cell aboard what appears to be "
                "a ship. Golden evening light slants through the window, painting the cell "
                "walls in warm hues. A heavy wooden door blocks the only exit. In the corner "
                "sits a simple wooden bucket filled with water, its surface occasionally "
                "rippling with the ship's movement."
            ),
            "night": (
                "You find yourself in a cramped holding cell aboard what appears to be "
                "a ship. Moonlight seeps through the barred window, casting eerie shadows "
                "across the floor. A heavy wooden door blocks the only exit. In the corner "
                "sits a simple wooden bucket filled with water, its surface occasionally "
                "rippling with the ship's movement."
            )
        }
        
        # Start the time ticker (updates every 5 minutes)
        TICKER_HANDLER.add(60 * 5, self.at_time_update)
        
        # Force initial description update
        self.update_description()
    
    def get_time_period(self):
        """Determine current time period"""
        hour = self.get_time_of_day()
        if 5 <= hour < 7:
            return "dawn"
        elif 7 <= hour < 17:
            return "day"
        elif 17 <= hour < 20:
            return "dusk"
        else:
            return "night"
    
    def at_time_update(self, *args, **kwargs):
        """Update the room's description based on time and weather"""
        self.update_description()
    
    def return_appearance(self, looker, **kwargs):
        """Return the current time period's description with weather effects"""
        current_period = self.get_time_period()
        
        # Check if we need to update the description
        if not self.db.cached_descriptions[current_period]:
            self.update_description()
        elif time.time() - self.db.cache_timestamps[current_period] > 900:  # 15 minutes
            self.update_description()
        
        # Get weather data
        weather_data = self.db.weather_data or {}
        if not weather_data:
            weather_data = self.get_weather_data()
        
        wind_speed = weather_data.get('wind_speed_10m', 0)
        temp = weather_data.get('apparent_temperature', 0)
        cloud_cover = weather_data.get('cloud_cover', 0)
        
        # Color code the weather conditions with high contrast colors
        def get_wind_color(speed):
            if speed < 5:
                return "|c"  # Cyan for calm
            elif speed < 15:
                return "|G"  # Bright green for breezy
            elif speed < 25:
                return "|Y"  # Yellow for windy
            else:
                return "|R"  # Bright red for stormy
            
        def get_temp_color(temperature):
            if temperature < 40:
                return "|C"  # Bright cyan for cold
            elif temperature < 65:
                return "|G"  # Bright green for mild
            elif temperature < 85:
                return "|Y"  # Yellow for warm
            else:
                return "|R"  # Bright red for hot
            
        def get_cloud_color(cover):
            if cover < 25:
                return "|W"  # Bright white for clear
            elif cover < 50:
                return "|C"  # Bright cyan for partly cloudy
            elif cover < 75:
                return "|B"  # Blue for mostly cloudy
            else:
                return "|M"  # Magenta for overcast
        
        # Wrap the appearance text
        appearance = f"\n\n|Y{self.key}|n\n\n"
        
        # Add the main description with wrapping
        main_desc = self.db.cached_descriptions[current_period] or self.db.desc_base[current_period]
        appearance += fill(main_desc, width=CLIENT_DEFAULT_WIDTH)
        
        # Add weather status line
        weather_line = (
            f"{get_wind_color(wind_speed)}Wind: {wind_speed} mph|n | "
            f"{get_temp_color(temp)}Temp: {temp}°F|n | "
            f"{get_cloud_color(cloud_cover)}Cloud Cover: {cloud_cover}%|n"
        )
        
        appearance += f"\n\n{weather_line}"
        
        return appearance
    
    def get_brief_desc(self):
        """Returns an AI-generated one-sentence summary of the current room state"""
        if hasattr(self.db, "brief_desc") and self.db.brief_desc:
            return self.db.brief_desc
        
        current_period = self.get_time_period()
        current_desc = self.db.cached_descriptions[current_period] or self.db.desc_base[current_period]
        
        print(f"Generating brief description for {current_period}")
        print(f"Current description: {current_desc}")
        # Get brief summary from OpenRouter
        import os
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        prompt = (
            "You are a concise writer for a text-based game. Given this detailed room description:\n\n"
            f"{current_desc}\n\n"
            "Create a single, clear sentence that captures the essential elements and current "
            "weather/atmospheric conditions. Focus on the most notable features and current state "
            "of the cell. Keep the tone consistent but be brief."
        )

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:4001",
            "X-Title": "Anchors Edge MUD"
        }
        
        data = {
            "model": "anthropic/claude-3-sonnet",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100  # Reduced for brevity
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                brief_desc = response.json()['choices'][0]['message']['content'].strip()
                # Cache the brief description
                self.db.brief_desc = brief_desc
                # Wrap the brief description
                brief_desc = fill(brief_desc, width=CLIENT_DEFAULT_WIDTH)
                return f"\n\n|Y{self.key}|n\n\n{brief_desc}\nExits: {', '.join(e.key for e in self.exits)}"
        except Exception as e:
            print(f"OpenRouter API error in brief description: {e}")
        
        # Fallback to basic description if API fails
        return (
            f"\n\n|Y{self.key}|n\n\n"
            "A cramped ship's holding cell with a barred window and wooden door. "
            f"Exits: {', '.join(e.key for e in self.exits)}"
        )
    
    def return_appearance(self, looker, **kwargs):
        """Customize room appearance based on brief mode"""
        if looker.db.brief_mode:
            return self.get_brief_desc()
        
        # Normal detailed description
        return super().return_appearance(looker, **kwargs)

class TavernRoom(DefaultRoom):
    """
    A cozy tavern room that serves as the starting point for new characters.
    """
    def at_object_creation(self):
        """
        Called when the room is first created.
        """
        super().at_object_creation()
        
        # Set a detailed description of the tavern room
        self.db.desc = (
            "You find yourself in a warm, inviting tavern room. Wooden beams cross the ceiling, "
            "their aged surface telling tales of countless years gone by. Soft, golden light "
            "from iron wall sconces bathes the room in a comfortable glow, creating dancing "
            "shadows in the corners. The air carries the comforting scent of pine wood and "
            "hearth smoke.\n\n"
            "A polished wooden bar runs along one wall, its surface worn smooth by countless "
            "patrons. Several sturdy wooden tables and chairs are scattered about, each "
            "bearing the marks of years of use. A large fireplace dominates one wall, its "
            "crackling flames providing both warmth and light.\n\n"
            "On the far wall, a ornate mirror hangs, its gilded frame catching the firelight. "
            "The mirror seems to invite you to examine your reflection."
        )