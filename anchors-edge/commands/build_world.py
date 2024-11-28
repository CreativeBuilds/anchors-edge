"""
Command module for building the entire game world.
"""

from evennia import Command, create_object, create_script
from evennia.utils import search, logger
from typeclasses.rooms import IslandRoom, WeatherAwareRoom
from evennia.utils.evtable import EvTable
from server.conf.settings import START_LOCATION, DEFAULT_HOME  # Direct import
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
            
            # Move players from Limbo to the new tavern
            self._move_players_from_limbo()
            
            # Notify about restart
            self.msg("|yRestarting server to apply spawn location changes...|n")
            
            # Schedule a server restart
            from evennia.server.sessionhandler import SESSIONS
            SESSIONS.announce_all("|rGame restarting in 3 seconds.|n")
            from twisted.internet import reactor
            from evennia import SERVERNAME
            
            def do_restart():
                SESSIONS.announce_all("|rRestarting....|n")
                from evennia import gamedir
                from subprocess import call
                import sys
                call([sys.executable, "evennia.py", "reload"], cwd=gamedir)
            
            reactor.callLater(3, do_restart)
            
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
                self.msg("\nThe following will be deleted:")
                if rooms:
                    self.msg("\nRooms:")
                    for room in rooms:
                        if room.dbref != "#2":
                            self.msg(f"- {room.name} ({room.dbref})")
                
                if weather_scripts:
                    self.msg("\nScripts:")
                    for script in weather_scripts:
                        self.msg(f"- {script.key}")
                
                # Ask for confirmation
                self.caller.attributes.add("_buildworld_confirm", True)
                self.msg("\nAre you sure? Type '@buildworld reset y' to confirm.")
                return
            
            # Actually delete everything
            self.msg("\nDeleting objects...")
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
            
            self.msg("\nReset complete.")
            
        except Exception as e:
            self.msg(f"|rError during reset: {e}|n")
            logger.log_trace()

    def _setup_weather_system(self):
        """Ensure the weather system is set up."""
        weather_script = search.search_script("weather_controller")
        if not weather_script:
            self.msg("Creating weather system...")
            script = create_script(
                "typeclasses.scripts.IslandWeatherScript",
                key="weather_controller",
                persistent=True,
                autostart=True
            )
            if not script:
                raise Exception("Failed to create weather system!")
        else:
            self.msg("Weather system already exists.")

    def _build_island(self):
        """
        Build the main island structure.
        """
        self.msg("Building main island...")
        
        # Create the tavern first as it will be our default spawn
        tavern = self._create_room(
            "The Rusty Anchor Tavern",
            "A cozy tavern frequented by sailors and locals alike. The warm glow of lanterns "
            "illuminates rough wooden tables and a well-worn bar counter. The air is thick "
            "with the smell of ale and sea salt. A heavy door leads outside to the harbor.",
            {"sheltered": True, "indoor": True, "magical": False}
        )
        
        # Now that tavern exists, set it as spawn location
        self._set_spawn_location(tavern)
        
        # Create the outdoor areas
        harbor = create_object(
            IslandRoom,
            key="Harbor District",
            location=None,
            attributes=(
                ("desc", "A bustling harbor district with ships coming and going. "
                        "The salty breeze carries the scent of the sea. The Rusty Anchor "
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
        
        # Verify the build
        self._verify_build(tavern, harbor, market)

    def _verify_build(self, tavern, harbor, market):
        """Verify the build was successful."""
        try:
            # Check spawn location settings
            from server.conf.settings import START_LOCATION, DEFAULT_HOME
            
            # Convert dbref string to actual object
            spawn_dbref = START_LOCATION.strip('#')
            spawn_location = search.search_object(f"#{spawn_dbref}", exact=True)
            
            if spawn_location and spawn_location[0] == tavern:
                self.msg("|gSpawn location set successfully.|n")
            else:
                self.msg("|rWarning: Spawn location may not be set correctly.|n")
                
            # Check weather awareness
            if harbor.db.weather_enabled and market.db.weather_enabled:
                self.msg("|gWeather awareness configured for outdoor areas.|n")
            else:
                self.msg("|rWarning: Weather awareness may not be configured correctly.|n")
            
            # Check exits
            if len(harbor.exits) == 2 and len(tavern.exits) == 1 and len(market.exits) == 1:
                self.msg("|gAll exits created successfully.|n")
            else:
                self.msg("|rWarning: Some exits may be missing.|n")
                
        except Exception as e:
            self.msg(f"|rError during verification: {e}|n")

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
                self.msg(f"\n|yMoving {len(players_in_limbo)} player(s) from Limbo to {tavern.name}...|n")
                
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

class CmdListObjects(Command):
    """
    List all game objects with filtering options.
    
    Usage:
        @objects [/switch] [type]
        
    Switches:
        /rooms      - List only rooms
        /exits      - List only exits
        /chars      - List only characters
        /scripts    - List only scripts
        /weather    - Show weather info
        
    Examples:
        @objects
        @objects/rooms
        @objects/scripts
        @objects/weather
    """
    
    key = "@objects"
    locks = "cmd:perm(Admin)"
    help_category = "Building"
    
    def func(self):
        """List objects based on switches."""
        if "weather" in self.switches:
            self._show_weather()
            return
            
        # Determine what to list
        if "rooms" in self.switches:
            objects = search.search_object("*", typeclass="typeclasses.rooms.WeatherAwareRoom")
            title = "Rooms"
        elif "exits" in self.switches:
            objects = search.search_object("*", typeclass="typeclasses.exits.Exit")
            title = "Exits"
        elif "chars" in self.switches:
            objects = search.search_object("*", typeclass="typeclasses.characters.Character")
            title = "Characters"
        elif "scripts" in self.switches:
            objects = search.search_script("weather_controller")
            title = "Scripts"
        else:
            objects = search.search_object("*")  # Search all objects
            title = "All Objects"

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