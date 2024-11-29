"""
Window objects that provide dynamic views based on weather and time.
"""

from evennia.objects.objects import DefaultObject
from textwrap import fill
from django.conf import settings

class Window(DefaultObject):
    """Base window class with common functionality."""
    
    def get_display_name(self, looker, **kwargs):
        """Get the display name of the window."""
        if looker.locks.check_lockstring(looker, "perm(Admin) or perm(Builder)"):
            return f"|w|hthe {self.key}(#{self.id})|n"
        return f"|w|hthe {self.key}|n"
    
    def at_object_creation(self):
        """Called when window is first created."""
        super().at_object_creation()
        self.db.base_desc = self.db.desc
        self.locks.add("get:false()")  # Windows can't be picked up
        
    def return_appearance(self, looker):
        """
        This is called when someone looks at the window.
        """
        # Get the window's name/title
        name = self.get_display_name(looker)
        
        room = self.location
        if not hasattr(room, 'get_weather_data'):
            return f"|/|/{name}|/{self.db.desc}|/"
            
        weather_data = room.get_weather_data()
        if not weather_data:
            return f"|/|/{name}|/{self.db.desc}|/"
            
        time_period = weather_data.get('time_period', 'day')
        weather_code = weather_data.get('weathercode')
        temp = weather_data.get('apparent_temperature', 70)
        wind_speed = weather_data.get('wind_speed_10m', 0)
        
        view_desc = self._get_view_description(time_period, weather_code, temp, wind_speed)
        window_state = self._get_window_state(weather_code, temp, wind_speed)
        
        # Return unformatted text - let child classes handle wrapping
        return f"|/|/{name}|/{window_state} {view_desc}|/"
        
    def _get_window_state(self, weather_code, temp, wind_speed):
        """Get the description of the window's physical state."""
        if weather_code in [95, 96, 99]:  # Thunderstorm
            return "The window pane trembles slightly with each thunderclap, raindrops streaming down the glass in sheets."
        elif weather_code in [61, 63, 65]:  # Rain
            return "Raindrops pattern against the window glass, creating ever-changing trails as they run down the pane."
        elif wind_speed > 15:
            return "The window occasionally creaks against the force of the wind outside."
        elif temp < 50:
            return "A thin layer of condensation has formed at the edges of the window pane."
        else:
            return "The clean window pane offers a clear view outside."
            
    def _get_view_description(self, time_period, weather_code, temp, wind_speed):
        """
        Get the description of the view. Should be overridden by subclasses.
        """
        return "You see the outside world through the window."

class HarborWindow(Window):
    """A window with a view of the harbor."""
    
    def _get_view_description(self, time_period, weather_code, temp, wind_speed):
        """Get description of harbor view based on conditions."""
        if weather_code in [95, 96, 99]:  # Thunderstorm
            return (
                "Through the rain-streaked glass, lightning occasionally illuminates the harbor, "
                "revealing ships straining at their moorings and waves crashing against the seawall."
            )
        
        base_views = {
            "dawn": (
                "The harbor is beginning to stir as the sky lightens. Early-rising fishermen "
                "prepare their vessels while seabirds wheel overhead, greeting the new day."
            ),
            "morning": (
                "The harbor bustles with morning activity. Ships move in and out of port while "
                "dock workers and merchants go about their business below."
            ),
            "noon": (
                "The sun glints off the harbor waters, creating a dazzling display. The docks "
                "are alive with the peak of day's activities."
            ),
            "afternoon": (
                "The afternoon sun casts long shadows across the harbor. Ships rock gently at "
                "their moorings while crews work in the mellowing light."
            ),
            "early_evening": (
                "The harbor begins to quiet as the day winds down. A few late vessels make "
                "their way into port while the sun sinks towards the horizon."
            ),
            "evening": (
                "Lanterns twinkle along the harbor like earthbound stars. The occasional ship "
                "moves silently through the darkening waters."
            ),
            "late_night": (
                "The harbor sleeps under starlight, with only a few lights moving on the water "
                "marking the passage of night fishermen or late-arriving ships."
            ),
            "witching_hour": (
                "The harbor rests in pre-dawn stillness. Only the gentle lapping of waves and "
                "creaking of moored ships breaks the quiet."
            )
        }
        return base_views.get(time_period, "The harbor stretches out below.")

class TownWindow(Window):
    """A window with a view of the town."""
    
    def _get_view_description(self, time_period, weather_code, temp, wind_speed):
        """Get description of town view based on conditions."""
        if weather_code in [95, 96, 99]:  # Thunderstorm
            return (
                "Lightning illuminates the town's rooftops in brief, dramatic flashes. Rain "
                "cascades down tiles and gutters, while wind-blown lanterns create swaying "
                "pools of light in the darkness. The storm transforms the familiar roofscape "
                "into a dramatic display of nature's power."
            )
        elif weather_code in [61, 63, 65]:  # Rain
            return (
                "Rain streams steadily across the rooftops below, creating silvery rivers "
                "along gutters and turning chimney smoke into ghostly wisps. The wet tiles "
                "gleam whenever light catches them, creating a strangely beautiful scene."
            )
            
        base_views = {
            "dawn": (
                "The town's rooftops emerge from darkness as dawn approaches. Chimney smoke "
                "rises straight and true in the still morning air, while early-rising workers "
                "move like shadows between buildings. The first hints of sunrise paint the "
                "eastern sky in delicate shades of pink and gold."
            ),
            "morning": (
                "Morning light plays across the town's rooftops, highlighting weathervanes and "
                "creating long shadows behind chimneys. Smoke rises from dozens of hearths as "
                "the city wakes. Workers traverse the maze of rooftops, carrying tools and "
                "materials for the day's labors."
            ),
            "noon": (
                "Sunlight bathes the town's rooftops in bright clarity. Chimney smoke drifts "
                "lazily in the midday warmth, while workers can be seen moving purposefully "
                "between buildings. Pigeons gather on sunny ledges, their feathers gleaming "
                "as they preen."
            ),
            "afternoon": (
                "Long shadows stretch across the rooftops as the afternoon progresses. The "
                "town's activities continue at a steady pace, with workers visible on their "
                "elevated paths and smoke rising from busy kitchens preparing evening meals. "
                "The western faces of chimneys glow warmly in the mellowing light."
            ),
            "early_evening": (
                "Windows begin to light up across the town as evening approaches. The last "
                "rays of sun paint the rooftops in warm copper tones, while chimney smoke "
                "takes on a golden hue. Workers begin making their way home across the "
                "elevated walkways."
            ),
            "evening": (
                "A tapestry of lit windows spreads across the town, creating a warm glow "
                "against the night sky. Lanterns mark the paths of night watchmen making "
                "their rounds, while smoke from evening fires drifts lazily overhead. The "
                "roofscape becomes a mysterious realm of shadows and light."
            ),
            "late_night": (
                "Most windows have gone dark now, though a few still glow with activity. "
                "The occasional lantern marks the passage of watchmen or late workers. "
                "Moonlight silvers the rooftops, creating a peaceful scene of shadows "
                "and subtle light."
            ),
            "witching_hour": (
                "The town sleeps under a blanket of darkness, broken only by the occasional "
                "lantern or still-lit window. Cats prowl silently across the rooftops, while "
                "the first hints of pre-dawn activity begin to stir in bakeries and stables "
                "below."
            )
        }
        return base_views.get(time_period, "The town's rooftops spread out below.")

class TavernWindow(Window):
    """A decorative window in the tavern."""
    
    def return_appearance(self, looker):
        """Override to wrap text properly."""
        unwrapped = super().return_appearance(looker)
        width = getattr(settings, 'ROOM_DESCRIPTION_WIDTH', 78)
        return fill(unwrapped, width=width, expand_tabs=True, replace_whitespace=False)
    
    def _get_view_description(self, time_period, weather_code, temp, wind_speed):
        """Get description based on conditions."""
        if weather_code in [95, 96, 99]:  # Thunderstorm
            return "The storm rages outside, making the tavern feel even more welcoming."
        elif weather_code in [61, 63, 65]:  # Rain
            return "Rain streams down the glass, distorting the view outside."
        else:
            return "The window provides a glimpse of the world outside the tavern."

class HallwayWindow(Window):
    """A west-facing window at the end of the hallway."""
    
    def _get_view_description(self, time_period, weather_code, temp, wind_speed):
        """Get description of the western view based on conditions."""
        if weather_code in [95, 96, 99]:  # Thunderstorm
            return (
                "Lightning flashes illuminate the western sky, briefly silhouetting the town's "
                "buildings against dramatic storm clouds. The polished table beneath the window "
                "gleams with each flash, making the flower arrangement cast dancing shadows."
            )
        elif weather_code in [61, 63, 65]:  # Rain
            return (
                "Rain streams down the window pane, blurring the view of the western sky. The "
                "flower arrangement on the table below catches subtle reflections from the wet "
                "glass, creating a peaceful scene."
            )
            
        base_views = {
            "dawn": (
                "The pre-dawn sky to the west still holds a few stubborn stars. The table beneath "
                "the window sits in shadow, its flower arrangement barely visible in the growing light."
            ),
            "morning": (
                "Morning light reflects off distant windows to the west, while the table beneath "
                "catches indirect sunlight that makes the polished wood gleam softly. The flower "
                "arrangement casts gentle shadows in the ambient light."
            ),
            "noon": (
                "The western view shows the town under the bright midday sun. The table beneath "
                "the window basks in ambient light, its flower arrangement vibrant in the natural "
                "illumination."
            ),
            "afternoon": (
                "The western sky grows golden as afternoon progresses. Warm light streams through "
                "the window, making the polished table glow and the flower arrangement cast long, "
                "dramatic shadows along its surface."
            ),
            "early_evening": (
                "The setting sun paints the western sky in brilliant hues of orange and gold. The "
                "table beneath the window is bathed in warm light, making both its polished surface "
                "and the flower arrangement glow with rich, sunset colors."
            ),
            "evening": (
                "The last traces of sunset fade from the western sky as lights begin to twinkle "
                "across the town. The table below catches the mixed illumination of dusk and "
                "interior lanterns, while the flower arrangement creates subtle shadows."
            ),
            "late_night": (
                "The western view shows a tapestry of distant lights under the night sky. The "
                "table beneath sits in the gentle glow of hallway sconces, its flower arrangement "
                "creating soft shadows in the muted light."
            ),
            "witching_hour": (
                "The western sky holds the promise of eventual dawn, though stars still glitter "
                "above the sleeping town. The table below rests in sconce-light, its flower "
                "arrangement a graceful silhouette in the pre-dawn quiet."
            )
        }
        return base_views.get(time_period, "The western view shows the town spread out below.")