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
        
    def get_display_desc(self, looker, **kwargs):
        """Get the description of the room."""
        if self.key == "Market Square":
            return self._get_market_description(looker)
        return super().get_display_desc(looker, **kwargs)
        
    def _get_market_description(self, looker):
        """Get time-appropriate market description."""
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
                "The market square is beginning to stir as vendors arrive early to set up their "
                "stalls. The first hints of dawn paint the sky as carts are wheeled into position "
                "and awnings unfurled. Early risers, mostly fishermen and bakers, move purposefully "
                "through the growing activity."
            )
        elif time_period == "morning":
            base_desc = (
                "The market square bustles with morning activity. Colorful stalls and awnings dot "
                "the open plaza, while vendors call out their wares. The air is filled with the "
                "scents of fresh bread, spices, and the day's catch from the harbor."
            )
        elif time_period == "noon":
            base_desc = (
                "The market square pulses with the peak of day's trading. Vendors hawk their wares "
                "beneath colorful awnings while shoppers weave between the stalls. The air is rich "
                "with the mingled aromas of food, spices, and sea air from the harbor."
            )
        elif time_period == "afternoon":
            base_desc = (
                "The afternoon market maintains a steady bustle. Vendors adjust their awnings to "
                "track the sun while continuing their trade. The crowd has thinned from the noon "
                "rush, but a constant flow of shoppers still moves between the stalls."
            )
        elif time_period == "early_evening":
            base_desc = (
                "As evening approaches, the market's energy begins to shift. Some vendors start "
                "packing away their more delicate goods, while others light lanterns to continue "
                "trading into the dusk. The crowd thins as workers head home for the day."
            )
        elif time_period == "evening":
            base_desc = (
                "The market square grows quieter as night falls. Most vendors have packed up for "
                "the day, though a few determined traders keep their lantern-lit stalls open. The "
                "open plaza that was so busy during daylight now holds only scattered activity."
            )
        elif time_period == "late_night":
            base_desc = (
                "The market square stands empty and quiet. Bare cobblestones mark where busy stalls "
                "stood during the day, now cleaned and ready for tomorrow's trade. Only the "
                "occasional night watchman passes through on their rounds."
            )
        elif time_period == "witching_hour":
            base_desc = (
                "In these smallest hours, the market square rests in darkness. The empty plaza "
                "holds memories of the day's bustle, while the first hints of pre-dawn activity "
                "begin as early vendors prepare for another day of trade."
            )
            
        # Add temperature effects
        if time_period not in ["late_night", "witching_hour"]:  # Only add for active market times
            if temp > 85:
                if time_period in ["noon", "afternoon"]:
                    base_desc += " " + (
                        "The hot, humid air has driven many to seek shelter in the shade of the "
                        "awnings, while vendors offer cool drinks to thirsty customers."
                    )
                else:
                    base_desc += " " + (
                        "The air is thick with humidity, though people still move about their "
                        "business in the heat."
                    )
            elif temp > 75:
                base_desc += " " + (
                    "The pleasant warmth has brought out plenty of shoppers, adding to the "
                    "square's lively atmosphere."
                )
            elif temp > 60:
                base_desc += " " + (
                    "The mild temperature makes for comfortable trading conditions as people "
                    "browse the stalls."
                )
            elif temp > 45:
                base_desc += " " + (
                    "The noticeable chill has people hurrying between stalls, some stopping "
                    "to warm their hands on cups of hot tea."
                )
            else:
                base_desc += " " + (
                    "The cold air has people bundled up as they move quickly about their "
                    "business, while vendors stamp their feet to stay warm."
                )
        
        # Add wind effects
        if wind_speed > 20:
            if time_period in ["late_night", "witching_hour"]:
                base_desc += " " + (
                    "Strong winds whip through the empty square, stirring up loose papers "
                    "and rattling the occasional shutter."
                )
            else:
                base_desc += " " + (
                    "Strong winds challenge the vendors' control of their awnings and goods, "
                    "forcing many to secure their wares more carefully."
                )
        elif wind_speed > 10:
            if time_period in ["late_night", "witching_hour"]:
                base_desc += " " + (
                    "A steady breeze sweeps through the empty square, carrying the day's "
                    "remnants along the cobblestones."
                )
            else:
                base_desc += " " + (
                    "A steady breeze ripples the awnings and carries the mingled scents "
                    "of the market across the square."
                )
        elif wind_speed > 5:
            base_desc += " " + (
                "A gentle breeze carries the various scents of the market through the air."
            )
            
        # Add weather effects
        if weather_code in WEATHER_CODES["thunderstorm"]:
            if time_period in ["late_night", "witching_hour"]:
                base_desc += " " + (
                    "Lightning illuminates the empty square in brief, dramatic flashes, while "
                    "thunder echoes between the surrounding buildings."
                )
            else:
                base_desc += " " + (
                    "Lightning flashes overhead as vendors scramble to secure their goods, "
                    "some already packing up early to avoid the worst of the storm."
                )
        elif weather_code in WEATHER_CODES["rain"]:
            if time_period in ["late_night", "witching_hour"]:
                base_desc += " " + (
                    "Rain falls steadily on the empty cobblestones, creating a peaceful rhythm "
                    "in the quiet square."
                )
            else:
                base_desc += " " + (
                    "Vendors huddle under their awnings as rain falls steadily, while determined "
                    "shoppers hurry between the sheltered stalls."
                )
                
        # Always end with the connection to the harbor
        base_desc += " The Harbor District lies to the south."
        
        return base_desc
        
    def get_weather_transition(self, old_weather, new_weather):
        """Get island-specific weather transition messages."""
        transitions = {
            ("clear", "rain"): "|w[Weather: Rain]|n A tropical shower moves in, bringing warm rain that patters against palm fronds.",
            ("clear", "storm"): "|w[Weather: Storm]|n The sky darkens rapidly as a tropical storm approaches, wind beginning to whip through the palms.",
            ("rain", "clear"): "|w[Weather: Clear]|n The rain shower passes, leaving everything fresh and glistening in renewed sunshine.",
            ("rain", "storm"): "|w[Weather: Storm]|n The gentle rain transforms into a proper tropical storm, palm trees swaying in strengthening winds.",
            ("storm", "clear"): "|w[Weather: Clear]|n The storm moves off across the sea, leaving behind clear skies and dripping foliage.",
            ("storm", "rain"): "|w[Weather: Rain]|n The storm's intensity eases to a gentle tropical shower.",
            ("clear", "cloudy"): "|w[Weather: Cloudy]|n Clouds drift in from the sea, providing occasional shade from the tropical sun.",
            ("cloudy", "clear"): "|w[Weather: Clear]|n The clouds dissipate, allowing the bright island sun to shine through.",
            ("clear", "windy"): "|w[Weather: Windy]|n A strong sea breeze picks up, setting the palm fronds to dancing.",
            ("windy", "clear"): "|w[Weather: Clear]|n The wind settles down, leaving the palms gently swaying in the tropical air.",
            ("cloudy", "rain"): "|w[Weather: Rain]|n The clouds darken and thicken until rain begins falling from the tropical sky.",
            ("cloudy", "storm"): "|w[Weather: Storm]|n The clouds grow ominously dark as a tropical storm system moves in from the sea.",
            ("cloudy", "windy"): "|w[Weather: Windy]|n A strong wind picks up, pushing the cloud cover across the sky.",
            ("windy", "rain"): "|w[Weather: Rain]|n The strong winds bring rain clouds, and soon warm tropical rain begins to fall.",
            ("windy", "storm"): "|w[Weather: Storm]|n The winds intensify as a tropical storm system moves in, palm trees thrashing in the strengthening gusts.",
            ("windy", "cloudy"): "|w[Weather: Cloudy]|n The wind pushes clouds in from the sea, providing intermittent shade.",
            ("rain", "cloudy"): "|w[Weather: Cloudy]|n The rain tapers off, leaving behind a blanket of clouds overhead.",
            ("rain", "windy"): "|w[Weather: Windy]|n The rain subsides as strong winds sweep in from the ocean.",
            ("storm", "cloudy"): "|w[Weather: Cloudy]|n The storm passes, though clouds still linger in its wake.",
            ("storm", "windy"): "|w[Weather: Windy]|n The storm moves on but leaves behind strong gusts that whip through the palm trees.",
            ("clear", "fog"): "|w[Weather: Fog]|n A thick tropical fog rolls in from the sea, wreathing the palm trees in mist.",
            ("fog", "clear"): "|w[Weather: Clear]|n The fog burns away under the tropical sun, revealing clear skies.",
            ("cloudy", "fog"): "|w[Weather: Fog]|n The clouds descend as fog rolls in from the ocean.",
            ("fog", "cloudy"): "|w[Weather: Cloudy]|n The fog lifts into low clouds that hang over the island.",
            ("rain", "fog"): "|w[Weather: Fog]|n The rain tapers off as thick fog moves in from the sea.",
            ("fog", "rain"): "|w[Weather: Rain]|n The fog thickens until it releases its moisture as tropical rain.",
            ("storm", "fog"): "|w[Weather: Fog]|n The storm passes, leaving behind a thick blanket of fog.",
            ("fog", "storm"): "|w[Weather: Storm]|n The fog is driven away as a tropical storm moves in.",
            ("windy", "fog"): "|w[Weather: Fog]|n The wind dies down as fog creeps in from the ocean.",
            ("fog", "windy"): "|w[Weather: Windy]|n A strong wind picks up, beginning to disperse the fog."            
        }
        return transitions.get((old_weather, new_weather), super().get_weather_transition(old_weather, new_weather))
        
    def get_time_transition(self, old_period, new_period):
        """Get island-specific time transition messages."""
        transitions = {
            ("dawn", "morning"): "|w[Time: Morning]|n The island awakens to birdsong as the sun rises over the eastern horizon.",
            ("morning", "noon"): "|w[Time: Noon]|n The sun climbs to its zenith, bringing the full heat of the tropical day.",
            ("noon", "afternoon"): "|w[Time: Afternoon]|n The intense midday sun begins its westward journey, though the heat lingers.",
            ("afternoon", "early_evening"): "|w[Time: Evening]|n The heat of the day begins to soften as the sun moves toward the horizon.",
            ("early_evening", "evening"): "|w[Time: Evening]|n The sun sets in a spectacular display of colors over the western sea.",
            ("evening", "late_night"): "|w[Time: Night]|n Night settles over the island as stars begin to twinkle in the tropical sky.",
            ("late_night", "witching_hour"): "|w[Time: Night]|n A peaceful quiet descends on the island, broken only by the sound of waves.",
            ("witching_hour", "dawn"): "|w[Time: Dawn]|n The first hint of dawn brightens the eastern horizon as early birds begin to stir."
        }
        return transitions.get((old_period, new_period), super().get_time_transition(old_period, new_period))