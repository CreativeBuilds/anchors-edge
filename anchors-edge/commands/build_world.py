"""
Command module for building the entire game world.
"""

from evennia import Command, create_object, create_script
from evennia.utils import search, logger
from typeclasses.rooms.tavern import MainTavernRoom, TavernHallway, SouthHarborRoom, NorthViewRoom, BoothRoom
from typeclasses.rooms.island import IslandRoom
from evennia.utils.evtable import EvTable
from server.conf.settings import START_LOCATION, DEFAULT_HOME
from evennia.objects.models import ObjectDB


class CmdBuildWorld(Command):
    """
    Build the entire game world from scratch.
    
    Usage:
        @buildworld [reset|check]
    
    Options:
        reset - If specified, will delete all existing rooms first
        check - Check the status of world systems
    """
    
    key = "@buildworld"
    locks = "cmd:perm(Admin)"
    help_category = "Building"
    
    def func(self):
        """Execute the build command."""
        if "check" in self.args:
            self._check_systems()
            return
            
        if "reset" in self.args:
            # If waiting for confirmation, check for y
            if self.caller.attributes.has("_buildworld_confirm"):
                if "y" in self.args.lower():
                    self.msg("Proceeding with reset...")
                    self._reset_world(confirmed=True)
                    self.caller.attributes.remove("_buildworld_confirm")
                else:
                    self.msg("Please confirm with '@buildworld reset y' or use a different command to cancel.")
                return
            else:
                # First time running reset, show what will be deleted
                self._reset_world(confirmed=False)
                return  # Don't proceed with build until confirmed
        
        try:
            # First ensure weather system exists
            self._setup_weather_system()
            
            # Build the world structure
            self._build_island()
            
            self.msg("World building completed successfully!")
            
            
        except Exception as e:
            self.msg(f"Error building world: {e}")
            logger.log_trace()

    def _check_systems(self):
        """Check the status of world systems."""
        # Check weather system
        weather_script = search.search_script("weather_controller")
        if weather_script:
            script = weather_script[0]
            self.msg("|gWeather System Status:|n")
            self.msg(f"- Script Active: {script.is_active}")
            self.msg(f"- Last Update: {script.db.last_updates}")
            self.msg(f"- Managed Islands: {list(script.db.coordinates.keys())}")
            
            # Test weather data fetch
            test_data = script.get_weather_data("main_island")
            if test_data:
                self.msg("- Weather Data: Available")
                self.msg(f"  Temperature: {test_data.get('apparent_temperature')}°F")
                self.msg(f"  Wind Speed: {test_data.get('wind_speed_10m')} mph")
            else:
                self.msg("|rWarning: Unable to fetch weather data|n")
        else:
            self.msg("|rWeather System not found!|n")

    def _reset_world(self, confirmed=False):
        """Delete all existing rooms except #2 (Limbo)."""
        try:
            # First list what will be deleted
            rooms = search.search_object("*", typeclass="typeclasses.rooms.WeatherAwareRoom")
            weather_scripts = search.search_script("weather_controller")
            
            if not confirmed:
                self.msg("|/The following will be deleted:")
                if rooms:
                    self.msg("|/Rooms:")
                    for room in rooms:
                        if room.dbref != "#2":
                            self.msg(f"- {room.name} ({room.dbref})")
                
                if weather_scripts:
                    self.msg("|/Scripts:")
                    for script in weather_scripts:
                        self.msg(f"- {script.key}")
                
                # Ask for confirmation
                self.caller.attributes.add("_buildworld_confirm", True)
                self.msg("|/Are you sure? Type '@buildworld reset y' to confirm.")
                return
            
            # Actually delete everything
            self.msg("|/Deleting objects...")
            if rooms:
                for room in rooms:
                    if room and room.dbref != "#2":
                        self.msg(f"Deleting room: {room.name}")
                        room.delete()
            
            # Only delete our custom scripts, not system scripts
            if weather_scripts:
                for script in weather_scripts:
                    self.msg(f"Deleting script: {script.key}")
                    script.delete()
            
            self.msg("|/Reset complete.")
            
        except Exception as e:
            self.msg(f"|rError during reset: {e}|n")
            logger.log_trace()

    def _setup_weather_system(self):
        """Ensure weather system is running."""
        try:
            # Check if weather script exists
            weather_script = search.search_script("weather_controller")
            
            if not weather_script:
                self.msg("Creating weather system...")
                # Create the weather script
                script = create_script(
                    "typeclasses.scripts.IslandWeatherScript",
                    key="weather_controller",
                    persistent=True,
                    interval=900,  # 15 minutes
                    autostart=True  # Make sure it starts automatically
                )
                if script:
                    script.start()  # Explicitly start the script
                    self.msg("|gWeather system created and started successfully.|n")
                    # Force first update
                    script.update_weather()
                else:
                    self.msg("|rFailed to create weather system.|n")
            else:
                script = weather_script[0]
                if not script.is_active:
                    script.start()
                    self.msg("|gRestarted existing weather system.|n")
                else:
                    self.msg("|gWeather system already running.|n")
                
                # Force an update
                script.update_weather()
            
            # Verify the script is running
            weather_script = search.search_script("weather_controller")
            if weather_script and weather_script[0].is_active:
                self.msg("Weather system verified as running.")
                test_data = weather_script[0].get_weather_data("main_island")
                if test_data:
                    self.msg(f"Weather data available: {test_data}")
                else:
                    self.msg("Warning: No weather data available yet.")
            else:
                self.msg("|rWarning: Weather system not running properly.|n")
            
        except Exception as e:
            self.msg(f"|rError setting up weather system: {e}|n")
            logger.log_err(f"Failed to setup weather system: {e}")

    def _build_island(self):
        """Build the main island structure."""
        self.msg("Building main island...")
        
        # Create the main tavern room using MainTavernRoom typeclass
        tavern = create_object(
            MainTavernRoom,  # Use specialized main tavern room
            key="The Salty Maiden",
            location=None,
            attributes=(
                ("weather_modifiers", {"sheltered": True, "indoor": True, "magical": False}),
                ("weather_enabled", True),
                ("is_tavern", True)
            )
        )
        
        # Create the second floor landing using TavernHallway
        second_floor = create_object(
            TavernHallway,  # Use specialized hallway room
            key="Second Floor Landing",
            location=None,
            attributes=(
                ("weather_modifiers", {"sheltered": True, "indoor": True, "magical": False}),
                ("weather_enabled", True),
                ("is_tavern", True)
            )
        )
        
        # Create stairs exit in both directions
        self._create_exit(tavern, second_floor, ["stairs", "up", "u"], ["down", "d"])
        
        # Create the guest rooms
        for i in range(1, 5):
            room_name = f"Guest Room {i}"
            # Different room types based on which side of the hallway
            if i <= 2:  # Rooms 1 and 2 face harbor
                guest_room = create_object(
                    SouthHarborRoom,  # Use specialized harbor-facing room
                    key=room_name,
                    location=None,
                    attributes=(
                        ("weather_modifiers", {"sheltered": True, "indoor": True, "magical": False}),
                        ("weather_enabled", True),
                        ("is_tavern", True)
                    )
                )
            else:  # Rooms 3 and 4 face city
                guest_room = create_object(
                    NorthViewRoom,  # Use specialized city-facing room
                    key=room_name,
                    location=None,
                    attributes=(
                        ("weather_modifiers", {"sheltered": True, "indoor": True, "magical": False}),
                        ("weather_enabled", True),
                        ("is_tavern", True)
                    )
                )
            # Create exit from landing to room
            self._create_exit(second_floor, guest_room, [f"door {i}", f"room {i}"], ["out"])

        # Create the booth rooms
        for i in range(1, 4):
            booth = create_object(
                BoothRoom,  # Use specialized booth room
                key=f"Private Booth {i}",
                location=None,
                attributes=(
                    ("weather_modifiers", {"sheltered": True, "indoor": True, "magical": False}),
                    ("weather_enabled", True),
                    ("is_tavern", True)
                )
            )
            # Create exit from tavern to booth
            self._create_exit(tavern, booth, [f"booth {i}"], ["out"])

        # Add furnishings to the tavern and second floor
        self._add_tavern_furnishings(tavern)
        self._add_second_floor_furnishings(second_floor)
        
        # Now that tavern exists, set it as spawn location
        self._set_spawn_location(tavern)
        
        # Create the outdoor areas
        harbor = create_object(
            IslandRoom,
            key="Harbor District",
            location=None,
            attributes=(
                ("desc", "A bustling harbor district with ships coming and going. "
                        "The salty breeze carries the scent of the sea. The Salty Maiden "
                        "Tavern provides shelter to the west, while the Market Square "
                        "lies to the north."),
                ("weather_modifiers", {"sheltered": False, "indoor": False, "magical": False}),
                ("weather_enabled", True)  # This room will show weather effects
            )
        )
        
        market = self._create_room(
            "Market Square",
            "A lively marketplace filled with vendors and traders. Colorful stalls and "
            "awnings dot the open plaza. The Harbor District lies to the south.",
            {"sheltered": False, "indoor": False, "magical": False}
        )
        
        # Set weather awareness for outdoor rooms
        harbor.db.weather_enabled = True
        market.db.weather_enabled = True
        
        # Create exits between rooms
        self._create_exit(harbor, market, ["north", "n"], ["south", "s"])
        self._create_exit(harbor, tavern, ["west", "w"], ["east", "e"])
        
        # Update room descriptions to reflect their connections
        tavern.db.desc = (
            "A cozy tavern frequented by sailors and locals alike. The warm glow of lanterns "
            "illuminates rough wooden tables and a well-worn bar counter. The air is thick "
            "with the smell of ale and sea salt. A heavy door leads east to the Harbor District."
        )
        
        market.db.desc = (
            "A lively marketplace filled with vendors and traders. Colorful stalls and "
            "awnings dot the open plaza. The Harbor District lies to the south, where "
            "you can see ships coming and going."
        )
        
        self.msg("Main island areas created.")
        
        # Move players from Limbo to the new tavern
        self._move_players_from_limbo(tavern)

    def _create_room(self, key, desc, modifiers):
        """Helper method to create a room."""
        return create_object(
            IslandRoom,
            key=key,
            location=None,
            attributes=(
                ("desc", desc),
                ("weather_modifiers", modifiers)
            )
        )

    def _create_exit(self, room1, room2, aliases1, aliases2):
        """Create exits between two rooms."""
        # Exit from room1 to room2
        create_object(
            "typeclasses.exits.Exit",
            key=aliases1[0],
            aliases=aliases1[1:],
            location=room1,
            destination=room2
        )
        # Exit from room2 to room1
        create_object(
            "typeclasses.exits.Exit",
            key=aliases2[0],
            aliases=aliases2[1:],
            location=room2,
            destination=room1
        ) 

    def _set_spawn_location(self, location):
        """
        Set the spawn location by updating settings.py
        """
        try:
            # Update settings file path
            settings_path = "server/conf/settings.py"
            
            with open(settings_path, 'r') as f:
                lines = f.readlines()
                
            # Update the settings
            with open(settings_path, 'w') as f:
                for line in lines:
                    if line.startswith('DEFAULT_HOME'):
                        f.write(f'DEFAULT_HOME = "#{location.id}"\n')
                    elif line.startswith('START_LOCATION'):
                        f.write(f'START_LOCATION = "#{location.id}"\n')
                    else:
                        f.write(line)
                        
            self.msg(f"|gSpawn location set to {location.name} (#{location.id}).|n")
            logger.log_info(f"Updated spawn location in settings.py to {location.name} (#{location.id})")
            
        except Exception as e:
            self.msg(f"|rError setting spawn location: {e}|n")
            logger.log_err(f"Failed to set spawn location: {e}")

    def _move_players_from_limbo(self, tavern):
        """Move all players from Limbo to the new tavern."""
        try:
            from evennia.objects.models import ObjectDB
            
            # Get Limbo
            limbo = ObjectDB.objects.get_id(2)
            if not limbo:
                return
            
            if not tavern:
                self.msg("|rError: Could not find tavern reference.|n")
                return
            
            # Find all characters in Limbo
            players_in_limbo = [obj for obj in limbo.contents 
                               if obj.has_account and obj.location == limbo]
            
            if players_in_limbo:
                self.msg(f"|/|yMoving {len(players_in_limbo)} player(s) from Limbo to {tavern.name}...|n")
                
                # Move each player
                for player in players_in_limbo:
                    player.location = tavern
                    player.msg(f"|yYou have been moved to {tavern.name}.|n")
                    
                # Announce in tavern
                if len(players_in_limbo) == 1:
                    tavern.msg_contents(f"{players_in_limbo[0].name} appears in the tavern.", exclude=players_in_limbo)
                else:
                    names = ", ".join(p.name for p in players_in_limbo)
                    tavern.msg_contents(f"Several people appear in the tavern: {names}", exclude=players_in_limbo)
                    
        except Exception as e:
            self.msg(f"|rError moving players from Limbo: {e}|n")

    def _add_tavern_furnishings(self, tavern):
        """Add furnishings to the tavern."""
        furnishings = [
            ("the bar", "A long, polished wooden bar runs along the left wall, its surface marked "
                    "by countless mugs and tales shared over the years. Various bottles and "
                    "kegs line the shelves behind it."),
            ("the hearth", "A large stone hearth dominates the western wall. The well-maintained "
                      "fireplace provides both warmth and a cozy atmosphere to the tavern."),
            ("the stairs", "Sturdy wooden stairs in the northwest corner lead up to the guest "
                      "rooms on the second floor."),
            ("booth one", "A cozy private booth with high-backed wooden benches and a solid table, "
                      "offering privacy for intimate conversations."),
            ("booth two", "A secluded booth with comfortable seating and a well-worn table, "
                      "perfect for private meetings."),
            ("booth three", "A quiet booth tucked away in the corner, its table bearing the marks "
                      "of countless meals and conversations."),
            ("the sconces", "Iron sconces line the walls, their flames providing warm illumination "
                       "throughout the tavern."),
            ("the windows", "Tall windows with wooden shutters look out onto the harbor, letting "
                       "in natural light during the day.")
        ]
        
        for key, desc in furnishings:
            obj = create_object(
                "evennia.objects.objects.DefaultObject",
                key=key,
                location=tavern,
                attributes=[
                    ("desc", desc)
                ]
            )
            # Make the objects un-gettable
            obj.locks.add("get:false()")

    def _add_second_floor_furnishings(self, second_floor):
        """Add furnishings to the second floor landing."""
        furnishings = [
            ("the table", "A polished wooden table stands beneath the window, its surface gleaming in "
                     "the light."),
            ("the window", "A tall window looks out over the harbor, letting in natural light during "
                     "the day."),
            ("some flowers", "Fresh wildflowers arranged in a clay pot, their vibrant colors brightening "
                       "the space. You can smell their sweet fragrance from here."),
            ("a clay pot", "A simple but elegant clay pot with delicate patterns etched around its rim."),
            ("the sconces", "Brass sconces are mounted at regular intervals along the walls, their "
                       "flames providing steady illumination throughout the night.")
        ]
        
        for key, desc in furnishings:
            obj = create_object(
                "evennia.objects.objects.DefaultObject",
                key=key,
                location=second_floor,
                attributes=[
                    ("desc", desc)
                ]
            )
            # Make the objects un-gettable
            obj.locks.add("get:false()")
            
            # Add special attributes for the flowers
            if key == "some flowers":
                obj.db.smell_desc = "The sweet fragrance of wildflowers fills your nose."
                obj.cmdset.add("commands.default_cmdsets.FlowerCmdSet", persistent=True)

class CmdListObjects(Command):
    """
    List game objects and their details
    
    Usage:
        @objects[/switch]
    
    Switches:
        rooms    - List all rooms
        exits    - List all exits
        chars    - List all characters
        scripts  - List all scripts
        weather  - Show weather info
        
    Examples:
        @objects
        @objects/rooms
        @objects/scripts
        @objects/weather
    """
    
    key = "@objects"
    locks = "cmd:perm(Admin)"
    help_category = "Building"
    switch_options = ["rooms", "exits", "chars", "scripts", "weather"]
    def func(self):
        """List objects based on switches."""
        # Get the first switch if any and convert to lowercase
        switch = None
        if hasattr(self, 'switches') and self.switches:
            switch = self.switches[0].lower()

        if not switch:  # If no switches, show all objects
            objects = search.search_object("*")
            title = "All Objects"
        elif switch == "weather":
            self._show_weather()
            return
        elif switch == "rooms":
            objects = search.search_object("*", typeclass="typeclasses.rooms.WeatherAwareRoom")
            title = "Rooms"
        elif switch == "exits":
            objects = search.search_object("*", typeclass="typeclasses.exits.Exit")
            title = "Exits"
        elif switch == "chars":
            objects = search.search_object("*", typeclass="typeclasses.characters.Character")
            title = "Characters"
        elif switch == "scripts":
            objects = search.search_script("*")  # Changed to search all scripts
            title = "Scripts"
        else:
            self.msg("Invalid switch. Use one of: rooms, exits, chars, scripts, weather")
            return

        # Create table
        table = EvTable(
            "|wID|n",
            "|wName|n",
            "|wTypeclass|n",
            "|wLocation|n",
            border="cells"
        )
        
        # Add objects to table
        if objects:  # Check if objects is not None
            for obj in objects:
                table.add_row(
                    f"#{obj.id}",
                    obj.name,
                    obj.typename,
                    obj.location.name if obj.location else "None"
                )
        
        self.msg(f"|w{title}:|n")
        self.msg(str(table))
        self.msg(f"Total: {len(objects) if objects else 0} objects")

    def _show_weather(self):
        """Show detailed weather information."""
        weather_script = search.search_script("weather_controller")
        if not weather_script:
            self.msg("|rWeather system not found!|n")
            return
            
        script = weather_script[0]
        
        # Create weather table
        table = EvTable(
            "|wIsland|n",
            "|wTemp|n",
            "|wWind|n",
            "|wClouds|n",
            "|wLast Update|n",
            border="cells"
        )
        
        for island in script.db.coordinates.keys():
            weather = script.get_weather_data(island)
            if weather:
                last_update = script.db.last_updates.get(island, "Never")
                if isinstance(last_update, float):
                    from datetime import datetime
                    last_update = datetime.fromtimestamp(last_update).strftime('%H:%M:%S')
                    
                table.add_row(
                    island,
                    f"{weather.get('apparent_temperature', 'N/A')}°F",
                    f"{weather.get('wind_speed_10m', 'N/A')} mph",
                    f"{weather.get('cloud_cover', 'N/A')}%",
                    last_update
                )
            else:
                table.add_row(island, "No Data", "No Data", "No Data", "Never")
        
        self.msg("|wWeather Systems:|n")
        self.msg(str(table)) 