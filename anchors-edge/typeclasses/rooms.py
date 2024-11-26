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
import random

from evennia.settings_default import CLIENT_DEFAULT_WIDTH

class Room(DefaultRoom):
    """
    Rooms are simple containers that has no location of their own.
    """
    
    def return_appearance(self, looker, **kwargs):
        """
        This is called when looking at the room.
        """
        if not looker:
            return ""
            
        # Get the description
        appearance = super().return_appearance(looker, **kwargs)
        if not appearance:
            return ""

        # Let the command/client handle text wrapping
        return appearance


class WeatherAwareRoom(DefaultRoom):
    """
    A room that uses Claude Sonnet via OpenRouter API to generate weather-aware descriptions
    """
    
    def at_object_creation(self):
        """Called when room is first created"""
        super().at_object_creation()
        
        # Initialize cached_descriptions as an empty dictionary
        if not hasattr(self.db, 'cached_descriptions') or self.db.cached_descriptions is None:
            self.db.cached_descriptions = {}
        
        # Initialize cache_timestamps similarly
        if not hasattr(self.db, 'cache_timestamps') or self.db.cache_timestamps is None:
            self.db.cache_timestamps = {}
        
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
        
        # Default weather effect descriptions
        self.db.weather_effects = {
            "rain": "\nThe sound of rain can be heard.",
            "wind": "\nThe wind howls outside.",
            "thunder": "\nThunder rumbles in the distance.",
            "cloudy_light": "dim",  # replaces "bright"
            "cloudy_sun": "daylight"  # replaces "sunlight"
        }
        
        # Location for weather (Turks and Caicos)
        self.db.latitude = 21.4655745
        self.db.longitude = -71.1390341
        
        # Start the weather update ticker (every 15 minutes)
        TICKER_HANDLER.add(60 * 15, self.update_weather)
        
        # Add moon phase effects
        self.db.moon_effects = {
            "new_moon": "darkness shrouds",
            "waxing_crescent": "a thin crescent moon casts faint light",
            "first_quarter": "a half moon provides modest illumination",
            "waxing_gibbous": "the nearly full moon bathes the area in silver light",
            "full_moon": "bright moonlight illuminates",
            "waning_gibbous": "the waning moon casts strong silver light",
            "last_quarter": "the half moon provides modest illumination",
            "waning_crescent": "a thin crescent moon offers faint light"
        }
        
        # Extend weather effects with moonlight variations
        self.db.weather_effects.update({
            "cloudy_moon": "filtered moonlight dimly illuminates",  # replaces normal moon descriptions when cloudy
            "clear_night": "stars twinkle in the clear night sky",
            "cloudy_night": "clouds obscure the night sky"
        })
        
        # Track moon phase (0-7: new=0, full=4)
        self.db.current_moon_phase = 0
        
    def get_openrouter_description(self, base_desc, weather_data):
        """Get weather-influenced description using base description and current weather"""
        weather_code = weather_data.get('weather_code', 0)
        wind_speed = weather_data.get('wind_speed_10m', 0)
        cloud_cover = weather_data.get('cloud_cover', 0)
        
        # Add weather effects to the description
        desc = base_desc
        
        # Default weather effects - can be overridden by child classes
        if hasattr(self, 'apply_weather_effects'):
            desc = self.apply_weather_effects(desc, weather_code, wind_speed, cloud_cover)
        else:
            # Basic default weather modifications
            if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                desc = desc + "\nThe sound of rain can be heard outside."
            
            if wind_speed > 15:
                desc = desc + "\nThe wind can be heard howling outside."
            
            if weather_code in [95, 96, 99]:
                desc = desc + "\nThunder rumbles in the distance."
            
            if cloud_cover > 80 and self.get_time_period() == "day":
                desc = desc.replace("bright", "dim").replace("sunlight", "daylight")
            
        return desc

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
        """Updates the room's description based on time of day and weather"""
        # Get current time period
        current_period = self.get_time_period()
        
        # Initialize base descriptions if they don't exist
        if not hasattr(self.db, 'desc_base') or self.db.desc_base is None:
            self.db.desc_base = {
                "dawn": self.db.desc or "The room is lit by the early morning light.",
                "morning": self.db.desc or "The room is well-lit by the morning sun.",
                "noon": self.db.desc or "The room is brightly lit by the midday sun.",
                "afternoon": self.db.desc or "The room is lit by the afternoon sun.",
                "dusk": self.db.desc or "The room is dimly lit by the setting sun.",
                "night": self.db.desc or "The room is dark, lit only by artificial light."
            }
        
        # Get base description for current time period
        base_desc = self.db.desc_base.get(current_period, self.db.desc or "You see nothing special.")
        
        # Always fetch fresh weather data if needed
        if not self.db.weather_data:
            self.db.weather_data = self.get_weather_data()
        
        # Apply weather effects directly to the base description
        weather_desc = self.apply_weather_effects(
            base_desc, 
            self.db.weather_data.get('weather_code', 0),
            self.db.weather_data.get('wind_speed_10m', 0),
            self.db.weather_data.get('cloud_cover', 0)
        )
        
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

    def get_moon_phase(self):
        """Calculate current moon phase (simplified 8-phase system)"""
        # This is a simplified calculation - you may want to use a proper astronomical formula
        
        # Moon cycle is approximately 29.53 days
        cycle_length = 29.53
        
        # Reference new moon date (you can update this periodically)
        reference_new_moon = datetime(2024, 3, 10)  # March 10, 2024 new moon
        
        days_since_new = (datetime.now() - reference_new_moon).days
        current_cycle_position = (days_since_new % cycle_length) / cycle_length
        
        # Convert to 8 phases (0-7)
        phase = int(current_cycle_position * 8)
        
        # Map phase number to name
        phase_names = [
            "new_moon", "waxing_crescent", "first_quarter", "waxing_gibbous",
            "full_moon", "waning_gibbous", "last_quarter", "waning_crescent"
        ]
        
        return phase_names[phase]

    def apply_weather_effects(self, desc, weather_code, wind_speed, cloud_cover):
        """Apply generic weather effects to the description"""
        current_period = self.get_time_period()
        
        # Handle night-specific lighting based on moon and clouds
        if current_period == "night":
            moon_phase = self.get_moon_phase()
            moon_desc = self.db.moon_effects[moon_phase]
            
            if cloud_cover > 80:
                # Very cloudy - minimal moonlight
                desc = desc.replace(moon_desc, self.db.weather_effects["cloudy_moon"])
                desc = desc.replace(self.db.weather_effects["clear_night"], 
                                  self.db.weather_effects["cloudy_night"])
            elif cloud_cover > 40:
                # Partially cloudy - filtered moonlight
                desc = desc.replace(moon_desc, 
                                  f"filtered {moon_desc.replace('bright ', '').replace('strong ', '')}")
        
        # Existing weather effects...
        if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            desc = desc + self.db.weather_effects["rain"]
        
        if wind_speed > 15:
            desc = desc + self.db.weather_effects["wind"]
        
        if weather_code in [95, 96, 99]:
            desc = desc + self.db.weather_effects["thunder"]
        
        # Modify lighting for very cloudy conditions during day
        if cloud_cover > 80 and current_period == "day":
            desc = desc.replace("bright", self.db.weather_effects["cloudy_light"])
            desc = desc.replace("sunlight", self.db.weather_effects["cloudy_sun"])
            
        return desc

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
        
        # Build the appearance text without wrapping
        appearance = f"\n‎ \n‎|Y{self.key}|n\n‎ \n‎"
        
        # Add the main description without wrapping
        main_desc = self.db.cached_descriptions[current_period] or self.db.desc_base[current_period]
        appearance += main_desc
        
        # Add weather status line
        weather_line = (
            f"{get_wind_color(wind_speed)}Wind: {wind_speed} mph|n | "
            f"{get_temp_color(temp)}Temp: {temp}°F|n | "
            f"{get_cloud_color(cloud_cover)}Cloud Cover: {cloud_cover}%|n"
        )
        
        appearance += f"\n‎ \n‎{weather_line}"
        
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
            "You are a concise writer for a text-based game. Given this detailed room description:\n‎ \n"
            f"{current_desc}\n‎ \n"
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
                brief_desc = brief_desc
                return f"\n‎ \n‎|Y{self.key}|n\n‎ \n‎{brief_desc}\nExits: {', '.join(e.key for e in self.exits)}"
        except Exception as e:
            print(f"OpenRouter API error in brief description: {e}")
        
        # Fallback to basic description if API fails
        return (
            f"\n‎ \n‎Y{self.key}|n\n‎ \n"
            "A cramped ship's holding cell with a barred window and wooden door. "
            f"Exits: {', '.join(e.key for e in self.exits)}"
        )
    
    def return_appearance(self, looker, **kwargs):
        """Customize room appearance based on brief mode"""
        if looker.db.brief_mode:
            return self.get_brief_desc()
        
        # Normal detailed description
        return super().return_appearance(looker, **kwargs)

class TavernRoom(WeatherAwareRoom):
    """
    A cozy tavern room that serves as the starting point for new characters.
    Inherits weather awareness to add atmospheric effects.
    """
    def at_object_creation(self):
        """Called when the room is first created"""
        # Initialize base descriptions first
        self.db.desc_base = {
            "dawn": ("You find yourself in a warm, inviting tavern room as dawn's first light peeks through the windows. "
                    "Wooden beams cross the ceiling, their aged surface telling tales of countless years gone by. "
                    "The iron wall sconces are being extinguished one by one as morning light gradually fills the room. "
                    "The air carries the comforting scent of pine wood and lingering hearth smoke.\n‎\n"
                    "A polished wooden bar runs along one wall, its surface worn smooth by countless patrons. "
                    "Several sturdy wooden tables and chairs are scattered about, each bearing the marks of years of use. "
                    "A large fireplace dominates one wall, its embers still glowing from the night before.\n‎\n‎"
                    "On the far wall, a ornate mirror hangs, its gilded frame catching the early morning light. "
                    "The mirror seems to invite you to examine your reflection."),

            "day": ("You find yourself in a warm, inviting tavern room. Wooden beams cross the ceiling, their aged "
                   "surface telling tales of countless years gone by. Bright sunlight streams through the windows, "
                   "mixing with the warm glow from iron wall sconces. The air carries the comforting scent of pine "
                   "wood and fresh bread from the kitchen.\n‎\n‎"
                   "A polished wooden bar runs along one wall, its surface worn smooth by countless patrons. "
                   "Several sturdy wooden tables and chairs are scattered about, each bearing the marks of years of use. "
                   "A large fireplace dominates one wall, maintained with a modest flame that provides a cozy atmosphere.\n‎\n‎"
                   "On the far wall, a ornate mirror hangs, its gilded frame gleaming in the daylight. "
                   "The mirror seems to invite you to examine your reflection."),

            "dusk": ("You find yourself in a warm, inviting tavern room as evening settles in. Wooden beams cross "
                    "the ceiling, their aged surface telling tales of countless years gone by. The golden light of "
                    "sunset mingles with the growing warmth of freshly lit iron wall sconces. The air carries the "
                    "comforting scent of pine wood and hearth smoke.\n‎\n‎"
                    "A polished wooden bar runs along one wall, its surface worn smooth by countless patrons. "
                    "Several sturdy wooden tables and chairs are scattered about, each bearing the marks of years of use. "
                    "A large fireplace dominates one wall, its flames building up to ward off the coming night.\n‎\n‎"
                    "On the far wall, a ornate mirror hangs, its gilded frame catching the last rays of sunlight. "
                    "The mirror seems to invite you to examine your reflection."),

            "night": ("You find yourself in a warm, inviting tavern room. Wooden beams cross the ceiling, their aged "
                     "surface telling tales of countless years gone by. Soft, golden light from iron wall sconces "
                     "bathes the room in a comfortable glow, creating dancing shadows in the corners. The air carries "
                     "the comforting scent of pine wood and hearth smoke.\n‎\n‎"
                     "A polished wooden bar runs along one wall, its surface worn smooth by countless patrons. "
                     "Several sturdy wooden tables and chairs are scattered about, each bearing the marks of years of use. "
                     "A large fireplace dominates one wall, its crackling flames providing both warmth and light.\n‎\n‎"
                     "On the far wall, a ornate mirror hangs, its gilded frame catching the firelight. "
                     "The mirror seems to invite you to examine your reflection.")
        }
        
        # Then call parent's at_object_creation which will use these descriptions
        super().at_object_creation()
        
        # Delete all characters in the room that aren't players
        for char in self.contents:
            if not char.has_account:
                char.delete()
        
        # Create Willow using the new NPC class
        from evennia import create_object
        willow = create_object(
            "typeclasses.characters.Willow",
            key="Willow",
            location=self,
            locks="edit:perm(Builders);call:false()"
        )
        
        # Store reference to Willow
        self.db.barmaid = willow
        
        # Override default weather effects with tavern-specific ones
        self.db.weather_effects.update({
            "rain": "The gentle patter of rain against the windows mingles with the sounds within. The air carries",
            "wind": "The sound of the wind whistles softly through the window frames. The air carries",
            "thunder": "The gentle patter of rain against the windows mingles with the sounds within. Occasional rumbles of thunder can be heard in the distance. The air carries",
            "cloudy_light": "Muted",  # replaces "Bright"
            "cloudy_sun": "daylight filters",  # replaces "sunlight streams"
            "cloudy_moon": "dim moonlight filters through the clouded windows",
            "clear_night": "the night sky is visible through the windows",
            "cloudy_night": "the clouded night sky is barely visible through the windows"
        })
        
        # Override moon effects for tavern-specific descriptions
        self.db.moon_effects = {
            "new_moon": "the darkness of the new moon leaves only starlight filtering",
            "waxing_crescent": "faint crescent moonlight slips",
            "first_quarter": "half-moon light streams",
            "waxing_gibbous": "strong moonlight pours",
            "full_moon": "brilliant full moonlight floods",
            "waning_gibbous": "strong moonlight streams",
            "last_quarter": "half-moon light filters",
            "waning_crescent": "faint crescent moonlight barely reaches"
        }
        
        # Base descriptions for different times of day
        self.db.desc_base = {
            "dawn": ("You find yourself in a warm, inviting tavern room as dawn's first light peeks through the windows. "
                    "Wooden beams cross the ceiling, their aged surface telling tales of countless years gone by. "
                    "The iron wall sconces are being extinguished one by one as morning light gradually fills the room. "
                    "The air carries the comforting scent of pine wood and lingering hearth smoke.\n‎\n"
                    "A polished wooden bar runs along one wall, its surface worn smooth by countless patrons. "
                    "Several sturdy wooden tables and chairs are scattered about, each bearing the marks of years of use. "
                    "A large fireplace dominates one wall, its embers still glowing from the night before.\n‎\n‎"
                    "On the far wall, a ornate mirror hangs, its gilded frame catching the early morning light. "
                    "The mirror seems to invite you to examine your reflection."),

            "day": ("You find yourself in a warm, inviting tavern room. Wooden beams cross the ceiling, their aged "
                   "surface telling tales of countless years gone by. Bright sunlight streams through the windows, "
                   "mixing with the warm glow from iron wall sconces. The air carries the comforting scent of pine "
                   "wood and fresh bread from the kitchen.\n‎\n‎"
                   "A polished wooden bar runs along one wall, its surface worn smooth by countless patrons. "
                   "Several sturdy wooden tables and chairs are scattered about, each bearing the marks of years of use. "
                   "A large fireplace dominates one wall, maintained with a modest flame that provides a cozy atmosphere.\n‎\n‎"
                   "On the far wall, a ornate mirror hangs, its gilded frame gleaming in the daylight. "
                   "The mirror seems to invite you to examine your reflection."),

            "dusk": ("You find yourself in a warm, inviting tavern room as evening settles in. Wooden beams cross "
                    "the ceiling, their aged surface telling tales of countless years gone by. The golden light of "
                    "sunset mingles with the growing warmth of freshly lit iron wall sconces. The air carries the "
                    "comforting scent of pine wood and hearth smoke.\n‎\n‎"
                    "A polished wooden bar runs along one wall, its surface worn smooth by countless patrons. "
                    "Several sturdy wooden tables and chairs are scattered about, each bearing the marks of years of use. "
                    "A large fireplace dominates one wall, its flames building up to ward off the coming night.\n‎\n‎"
                    "On the far wall, a ornate mirror hangs, its gilded frame catching the last rays of sunlight. "
                    "The mirror seems to invite you to examine your reflection."),

            "night": ("You find yourself in a warm, inviting tavern room. Wooden beams cross the ceiling, their aged "
                     "surface telling tales of countless years gone by. Soft, golden light from iron wall sconces "
                     "bathes the room in a comfortable glow, creating dancing shadows in the corners. The air carries "
                     "the comforting scent of pine wood and hearth smoke.\n‎\n‎"
                     "A polished wooden bar runs along one wall, its surface worn smooth by countless patrons. "
                     "Several sturdy wooden tables and chairs are scattered about, each bearing the marks of years of use. "
                     "A large fireplace dominates one wall, its crackling flames providing both warmth and light.\n‎\n‎"
                     "On the far wall, a ornate mirror hangs, its gilded frame catching the firelight. "
                     "The mirror seems to invite you to examine your reflection.")
        }

    def return_appearance(self, looker, **kwargs):
        """
        Customize the appearance of the tavern room.
        """
        if not looker:
            return ""
            
        # Update description based on time and weather
        current_period = self.get_time_period()
        
        # Check if we need to update the description
        if not self.db.cached_descriptions[current_period]:
            self.update_description()
        elif time.time() - self.db.cache_timestamps[current_period] > 900:  # 15 minutes
            self.update_description()
            
        return super().return_appearance(looker, **kwargs)

    def apply_weather_effects(self, desc, weather_code, wind_speed, cloud_cover):
        """Apply tavern-specific weather effects to the description"""
        current_period = self.get_time_period()
        
        # Start with the base description
        modified_desc = desc
        
        # Build weather effects
        weather_effects = []
        
        # Add rain sounds if it's raining
        if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            weather_effects.append("The gentle patter of rain against the windows mingles with the sounds within")
        
        # Add wind sounds for strong winds
        if wind_speed > 15:
            weather_effects.append("The wind whistles softly through the window frames")
        
        # Add thunder effects
        if weather_code in [95, 96, 99]:
            weather_effects.append("Occasional rumbles of thunder can be heard in the distance")
        
        # Combine weather effects with appropriate conjunctions
        if weather_effects:
            weather_text = ""
            if len(weather_effects) == 1:
                weather_text = f"{weather_effects[0]}. "
            elif len(weather_effects) == 2:
                weather_text = f"{weather_effects[0]} and {weather_effects[1]}. "
            else:
                weather_text = f"{', '.join(weather_effects[:-1])}, and {weather_effects[-1]}. "
            
            # Find the sentence about the air's scent
            air_scent_index = modified_desc.find("The air carries")
            if air_scent_index != -1:
                # Insert weather effects before the air scent
                modified_desc = (
                    f"{modified_desc[:air_scent_index]}"
                    f"{weather_text}"
                    f"{modified_desc[air_scent_index:]}"
                )
        
        # Modify lighting for very cloudy conditions during day
        if cloud_cover > 80 and current_period == "day":
            modified_desc = modified_desc.replace("Bright sunlight streams", 
                                               "Muted daylight filters")
            
        return modified_desc

    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """Called when an object enters the room"""
        # Check if it's a drink being dropped
        if hasattr(moved_obj, 'db') and moved_obj.db.is_drink:
            # Get the barmaid
            if hasattr(self.db, 'barmaid') and self.db.barmaid:
                # Determine if it's placed on a table or bar
                if random.random() < 0.6:  # 60% chance for table
                    self.msg_contents(f"{moved_obj.name} is placed on a nearby table.")
                else:
                    self.msg_contents(f"{moved_obj.name} is placed on the bar.")
                    
                # Only schedule cleanup if drink is nearly empty
                if moved_obj.db.health <= 3:
                    from evennia import utils
                    utils.delay(10, self.cleanup_drink, moved_obj)
    
    def cleanup_drink(self, drink_obj):
        """Have Willow clean up the drink"""
        if not drink_obj or not drink_obj.location == self:
            return
            
        # Double check the drink is still nearly empty when cleanup occurs
        if drink_obj.db.health > 3:
            return
            
        if hasattr(self.db, 'barmaid') and self.db.barmaid:
            willow = self.db.barmaid
            # Generate cleanup message
            messages = [
                f"{willow.name} swings by and collects the nearly empty {drink_obj.name}.",
                f"{willow.name} efficiently clears away the mostly finished {drink_obj.name}.",
                f"{willow.name} gathers up the almost empty {drink_obj.name} while tidying the tavern.",
                f"{willow.name} picks up the nearly finished {drink_obj.name} and takes it behind the bar."
            ]
            self.msg_contents(random.choice(messages))
            drink_obj.delete()