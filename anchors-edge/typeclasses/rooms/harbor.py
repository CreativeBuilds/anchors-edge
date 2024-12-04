"""
Harbor-specific room types and templates.
"""

from typeclasses.rooms.base import WeatherAwareRoom
from typeclasses.rooms.weather_codes import WEATHER_CODES

class HarborRoom(WeatherAwareRoom):
    """Base class for harbor locations."""
    
    def at_object_creation(self):
        """Called when room is first created."""
        super().at_object_creation()
        self.db.weather_enabled = True
        self.db.weather_modifiers = {
            "sheltered": False,
            "indoor": False,
            "magical": False
        }

    def _get_harbor_description(self, looker):
        """Get time-appropriate harbor description."""
        weather_data = self.get_weather_data()
        if not weather_data:
            return self.db.desc
            
        time_period = weather_data.get('time_period', 'day')
        weather_code = weather_data.get('weathercode')
        temp = weather_data.get('apparent_temperature', 70)
        wind_speed = weather_data.get('wind_speed_10m', 0)
        
        # Get base time-of-day description
        if time_period == "dawn":
            base_desc = (
                "The harbor stirs to life as the first light touches the water. Early fishing vessels "
                "slip their moorings, their crews moving with practiced efficiency in the growing light. "
                "The wooden docks creak softly under the feet of sailors preparing for the day's work, "
                "while seabirds wheel overhead, their calls heralding the morning."
            )
        elif time_period == "morning":
            base_desc = (
                "The harbor bustles with morning activity. Fishing boats return with their early catches, "
                "while merchant vessels prepare to set sail. The docks are alive with the sounds of commerce "
                "as porters move cargo and sailors call out to one another across the busy waterfront."
            )
        elif time_period == "noon":
            base_desc = (
                "The harbor reaches its daily peak of activity under the midday sun. Ships of all sizes "
                "crowd the docks, from small fishing boats to larger merchant vessels. The air rings with "
                "the sounds of commerce and maritime labor, while dock workers and sailors move purposefully "
                "about their tasks."
            )
        elif time_period == "afternoon":
            base_desc = (
                "Afternoon finds the harbor in steady motion. More fishing boats return with their day's catch, "
                "while merchant ships continue loading and unloading their cargo. The docks remain busy with "
                "a mix of maritime traffic, though the frantic energy of noon has settled into a more measured pace."
            )
        elif time_period == "early_evening":
            base_desc = (
                "The harbor's rhythm shifts as evening approaches. Most fishing boats have returned, their "
                "catches being sorted and sold at the dockside markets. Merchant vessels secure their moorings "
                "for the night, while tavern lights begin to beckon tired sailors."
            )
        elif time_period == "evening":
            base_desc = (
                "Evening transforms the harbor into a different world. Lanterns sway gently on moored vessels, "
                "their light reflecting off the dark water. The daytime bustle has given way to quieter activities "
                "as night watch crews take their positions and most sailors seek entertainment ashore."
            )
        elif time_period == "late_night":
            base_desc = (
                "The harbor rests in nighttime stillness, broken only by the gentle lapping of waves against "
                "the hulls of moored vessels. A few lanterns mark the watch positions along the docks, while "
                "most ships sleep quietly at their berths, their shapes dark against the starlit water."
            )
        elif time_period == "witching_hour":
            base_desc = (
                "In these smallest hours, the harbor dreams. Only the occasional footstep of a watchman or "
                "the creak of a ship's timber breaks the pre-dawn quiet. A few early fishing boats begin "
                "their preparations, their crews moving like shadows in the darkness."
            )
            
        # Add temperature effects
        if time_period not in ["late_night", "witching_hour"]:
            if temp > 85:
                base_desc += " " + (
                    "The hot, humid air hangs heavy over the docks, causing workers to move more slowly "
                    "and seek whatever shade they can find between tasks."
                )
            elif temp < 45:
                base_desc += " " + (
                    "The cold air has workers stamping their feet and rubbing their hands between tasks, "
                    "their breath visible in the chill as they go about their duties."
                )
        
        # Add wind effects
        if wind_speed > 20:
            base_desc += " " + (
                "Strong winds whip across the harbor, causing moored vessels to strain at their lines "
                "while loose canvas snaps sharply in the gusts."
            )
        elif wind_speed > 10:
            base_desc += " " + (
                "A steady breeze fills the harbor, carrying the mingled scents of salt water and tar "
                "while setting the moored vessels gently rocking at their berths."
            )
            
        # Add weather effects
        if weather_code in WEATHER_CODES["thunderstorm"]:
            base_desc += " " + (
                "Lightning illuminates the harbor in stark flashes, followed by rolling thunder that "
                "echoes across the water. Ships' crews scramble to secure any loose gear as the storm rages."
            )
        elif weather_code in WEATHER_CODES["rain"]:
            base_desc += " " + (
                "Rain falls steadily across the harbor, drumming on deck planking and causing the "
                "water's surface to dance with countless tiny impacts."
            )
        elif weather_code in WEATHER_CODES["cloudy"]:
            base_desc += " " + (
                "Clouds hang low over the harbor, their gray masses promising weather to come while "
                "diffusing the light across the water."
            )
                
        # Always end with the connections
        base_desc += " The Market Square lies to the north, while various ships and boats line the docks."
        
        return base_desc
        
    def get_display_desc(self, looker, **kwargs):
        """Get the description of the room."""
        if self.key == "Harbor District":
            return self._get_harbor_description(looker)
        return super().get_display_desc(looker, **kwargs) 

    def get_weather_transition(self, old_weather, new_weather):
        """Get harbor-specific weather transition messages."""
        transitions = {
            ("clear", "rain"): "Raindrops begin to ripple across the harbor waters, creating concentric circles that spread outward.",
            ("clear", "storm"): "Dark clouds roll in from the sea as waves grow choppier, heralding an approaching storm.",
            ("rain", "clear"): "The rain tapers off, leaving the harbor waters calm and glistening.",
            ("rain", "storm"): "The steady rain intensifies as thunder echoes across the water, waves growing more aggressive.",
            ("storm", "clear"): "The storm passes out to sea, leaving the harbor waters to gradually settle.",
            ("storm", "rain"): "The storm's fury subsides to a steady rain, though the waters remain somewhat choppy.",
            ("clear", "cloudy"): "Clouds gather over the harbor, their shadows dancing across the water's surface.",
            ("cloudy", "clear"): "The clouds break apart, allowing sunlight to sparkle across the harbor waters.",
            ("clear", "windy"): "The wind picks up, creating white-capped waves across the harbor.",
            ("windy", "clear"): "The wind dies down, allowing the harbor waters to settle into gentle ripples."
        }
        return transitions.get((old_weather, new_weather), super().get_weather_transition(old_weather, new_weather))
        
    def get_time_transition(self, old_period, new_period):
        """Get harbor-specific time transition messages."""
        transitions = {
            ("dawn", "morning"): "The harbor comes alive as the sun rises, early fishing boats heading out to sea.",
            ("morning", "noon"): "The sun climbs high overhead, casting shorter shadows across the busy docks.",
            ("noon", "afternoon"): "The afternoon sun bathes the harbor in golden light as activity continues steadily.",
            ("afternoon", "early_evening"): "The light grows amber as the sun descends, fishing boats beginning to return.",
            ("early_evening", "evening"): "Harbor lanterns spring to life one by one as daylight fades.",
            ("evening", "late_night"): "Night settles over the harbor as activity winds down to the quiet watch hours.",
            ("late_night", "witching_hour"): "A deep quiet falls over the harbor, broken only by gentle waves and creaking ropes.",
            ("witching_hour", "dawn"): "Pre-dawn light slowly illuminates the harbor as early crews begin to stir."
        }
        return transitions.get((old_period, new_period), super().get_time_transition(old_period, new_period))