"""
Tavern-specific room types and templates.
"""

from typeclasses.rooms.base import WeatherAwareRoom
from typeclasses.rooms.weather_codes import WEATHER_CODES
from textwrap import fill
from django.conf import settings

class TavernRoom(WeatherAwareRoom):
    """Base class for all tavern rooms with shared functionality."""
    
    def at_object_creation(self):
        """Called when room is first created."""
        super().at_object_creation()
        self.db.base_desc = self.db.desc
        self.db.is_tavern = True
        self.db.weather_enabled = True
        self.db.weather_modifiers = {
            "sheltered": True,
            "indoor": True,
            "magical": False
        }
    
    def get_display_desc(self, looker, **kwargs):
        """Get the description of the room."""
        # Update dynamic description before displaying
        if hasattr(self, '_update_dynamic_description'):
            self._update_dynamic_description()
        
        # Get the description from parent
        return super().get_display_desc(looker, **kwargs)
    
    def get_display_name(self, looker, **kwargs):
        """Return the light blue-colored name of the room."""
        return f"|c{super().get_display_name(looker, **kwargs)}|n"
    
    def wrap_text(self, text):
        """
        Wraps text to the configured width.
        
        Args:
            text (str): Text to wrap
            
        Returns:
            str: Wrapped text
        """
        width = getattr(settings, 'ROOM_DESCRIPTION_WIDTH', 78)
        return fill(text, width=width, expand_tabs=True, replace_whitespace=False)

class MainTavernRoom(TavernRoom):
    """The main tavern room with hearth and dynamic descriptions."""
    
    def _update_dynamic_description(self):
        """Update the room's description based on time of day and weather"""
        # Initialize base_desc
        base_desc = ""
        
        # Get current time and weather
        current_hour = self.get_current_hour()
        current_weather = self.get_current_weather()
        
        # Time-based lighting descriptions
        if 5 <= current_hour < 7:  # Dawn
            base_desc = "The early morning light filters softly through the tavern's windows, casting long shadows across the room."
        elif 7 <= current_hour < 12:  # Morning
            base_desc = "Morning light streams through the windows, bringing warmth to the tavern's well-worn surfaces."
        elif 12 <= current_hour < 17:  # Afternoon
            base_desc = "The sun at its peak bathes the tavern in bright, direct light."
        elif 17 <= current_hour < 19:  # Dusk
            base_desc = "The fading daylight casts a warm, golden glow throughout the tavern."
        elif 19 <= current_hour < 22:  # Evening
            base_desc = "Lantern light fills the tavern with a cozy, welcoming warmth as night settles outside."
        else:  # Night
            base_desc = "The tavern is lit by the warm glow of lanterns and the occasional flicker from the hearth."

        # Rest of the description
        base_desc += " The well-worn bar along the left wall gleams under the %s, while the three booths at the back offer welcome shade for those seeking respite from the day's heat. A large stone hearth stands dormant in the warm weather, its presence still dominating the south wall though no flames dance within." % (
            "midday sun" if 10 <= current_hour < 14 else
            "morning light" if 6 <= current_hour < 10 else
            "afternoon sun" if 14 <= current_hour < 18 else
            "evening light" if 18 <= current_hour < 21 else
            "lantern light"
        )

        # Weather effects
        if current_weather:
            weather_desc = {
                'clear': "A warm breeze drifts through the open windows, carrying with it the mingled scents of the sea and the promise of adventure.",
                'cloudy': "A cool breeze occasionally drifts through the windows, bringing with it the salt-tinged scent of the sea.",
                'rain': "The sound of rain pattering against the windows adds a cozy atmosphere to the tavern's interior.",
                'storm': "The occasional flash of lightning through the windows illuminates the tavern in brief, dramatic bursts."
            }.get(current_weather, "A gentle breeze drifts through the open windows.")
            
            base_desc += " " + weather_desc

        # Add static elements
        base_desc += " Sturdy wooden stairs in the northeast corner lead up to the second floor, their well-worn steps telling countless tales of travelers who've passed this way before. The tavern's entrance in the southwest corner welcomes visitors from the street, its heavy wooden door well-oiled and often in motion."

        # Update the room's description
        self.db.desc = base_desc

class TavernHallway(TavernRoom):
    """The second floor hallway of the tavern."""
    
    def _update_dynamic_description(self):
        """Update the hallway's description based on conditions."""
        weather_data = self.get_weather_data()
        if not weather_data:
            return

        time_period = weather_data.get('time_period', 'day')
        weather_code = weather_data.get('weathercode')

        # Build a single flowing description
        if time_period == "dawn":
            self.db.desc = (
                "Early morning light filters into the well-maintained hallway. Guest rooms One "
                "and Two line the south side of the corridor, while rooms Three and Four occupy "
                "the north wall. A polished wooden table stands at the end of the hall, holding "
                "a clay pot of fresh wildflowers, their colors just beginning to emerge in the "
                "growing light. Brass sconces along the walls still provide supplementary "
                "illumination for the early hour."
            )
        elif time_period == "morning":
            self.db.desc = (
                "Morning light brightens the well-maintained hallway. Guest rooms One and Two "
                "line the south side of the corridor, while rooms Three and Four occupy the "
                "north wall. A polished wooden table at the hall's end holds fresh wildflowers, "
                "their colors vibrant in the natural light. Brass sconces mounted at regular "
                "intervals stand ready for evening."
            )
        elif time_period == "noon":
            self.db.desc = (
                "The well-maintained hallway stretches between four guest rooms, with rooms "
                "One and Two along the south wall and rooms Three and Four to the north. "
                "A polished wooden table at the end of the hall displays a clay pot of fresh "
                "wildflowers, their colors bright in the midday light filtering into the corridor."
            )
        elif time_period == "afternoon":
            self.db.desc = (
                "The well-maintained hallway runs between four guest rooms. Rooms One and Two "
                "line the south wall, while rooms Three and Four occupy the north side. At the "
                "hall's end, a polished wooden table holds a clay pot of fresh wildflowers, "
                "their colors rich in the afternoon light. Brass sconces wait patiently along "
                "the walls for evening."
            )
        elif time_period == "early_evening":
            self.db.desc = (
                "Freshly lit brass sconces cast a warm glow throughout the well-maintained "
                "hallway. Guest rooms One and Two line the south wall, while rooms Three and "
                "Four occupy the north side. A polished wooden table at the corridor's end "
                "holds a clay pot of wildflowers, their colors softening in the evening light."
            )
        elif time_period == "evening":
            self.db.desc = (
                "The evening hours find the corridor lit warmly by brass sconces. Guest rooms "
                "One and Two line the south wall, while rooms Three and Four occupy the north "
                "side. The polished wooden table at the hall's end reflects the sconces' light, "
                "its flower arrangement casting gentle shadows."
            )
        elif time_period == "late_night":
            self.db.desc = (
                "The hallway rests in comfortable quiet, lit by the steady glow of brass "
                "sconces. Guest rooms One and Two line the south wall, while rooms Three and "
                "Four occupy the north side. A wooden table at the corridor's end holds its "
                "flower arrangement, the blooms barely visible in the gentle light."
            )
        elif time_period == "witching_hour":
            self.db.desc = (
                "In these smallest hours, brass sconces provide just enough light to guide "
                "the way down the quiet hallway. Guest rooms One and Two line the south wall, "
                "while rooms Three and Four occupy the north side. Fresh flowers on the wooden "
                "table at the hall's end fill the air with a subtle fragrance."
            )

        # Add weather elements seamlessly into the description
        if weather_code in WEATHER_CODES["thunderstorm"]:
            self.db.desc += " " + (
                "Distant thunder occasionally rumbles through the building's walls."
            )
        elif weather_code in WEATHER_CODES["rain"]:
            self.db.desc += " " + (
                "The gentle sound of rain on the roof adds to the hallway's peaceful atmosphere."
            )

        # Wrap the description before setting it
        self.db.desc = self.wrap_text(self.db.desc)

class SouthHarborRoom(TavernRoom):
    """Guest rooms facing south towards the harbor."""
    
    def _update_dynamic_description(self):
        """Update the room's description based on conditions."""
        weather_data = self.get_weather_data()
        if not weather_data:
            return

        time_period = weather_data.get('time_period', 'day')
        weather_code = weather_data.get('weathercode')
        temp = weather_data.get('apparent_temperature', 70)

        # Build the description based on time of day
        if time_period == "dawn":
            base_desc = (
                "Early morning light floods this comfortable guest room through its large south-facing "
                "window, painting the wooden furniture in hues of gold and amber. A well-made bed with "
                "crisp linen sheets rests against one wall, while a sturdy desk and chair sit beneath "
                "the window, perfectly positioned to watch the harbor come alive with the day's first "
                "activities. The brass sconces still flicker softly, their services becoming less "
                "needed as dawn's light grows stronger."
            )
        elif time_period == "morning":
            base_desc = (
                "Bright morning sunlight streams through the large south-facing window, filling this "
                "comfortable guest room with cheerful illumination. A well-made bed with crisp linens "
                "stands ready against one wall, while the sturdy desk and chair beneath the window "
                "offer a perfect vantage point to watch the morning's harbor traffic. Brass sconces "
                "hang unlit along the walls, waiting for evening's return."
            )
        elif time_period == "noon":
            base_desc = (
                "The large south-facing window of this comfortable guest room offers a commanding view "
                "of the sun-dappled harbor waters. A well-made bed with crisp linens rests against "
                "one wall, while a sturdy desk and chair beneath the window provide an ideal spot "
                "for watching the afternoon's maritime activities. The room feels open and airy, with "
                "brass sconces waiting patiently for dusk."
            )
        elif time_period == "afternoon":
            base_desc = (
                "The afternoon light softens as it enters through the large south-facing window, "
                "the harbor view now peaceful after the day's peak activities. A well-made bed "
                "with crisp linens offers a perfect spot for an afternoon rest, while the sturdy "
                "desk and chair beneath the window invite quiet contemplation of the maritime scene."
            )
        elif time_period == "evening":
            base_desc = (
                "Evening transforms the room into a haven of warm light from the brass sconces, "
                "while the large south-facing window reflects the harbor's nighttime activities. "
                "A well-made bed with crisp linens beckons, and the sturdy desk and chair offer "
                "a perfect spot for evening reflection or letter-writing."
            )
        elif time_period == "late_night":
            base_desc = (
                "Night settles comfortably in this south-facing room. The harbor's lights "
                "twinkle beyond the window, while brass sconces provide warm illumination "
                "inside. A well-made bed with crisp linens waits against one wall, and a "
                "sturdy desk beneath the window offers a quiet spot to watch the harbor's "
                "nocturnal activities."
            )
        elif time_period == "witching_hour":
            base_desc = (
                "The room is peaceful at this early hour. Beyond the south-facing window, "
                "the harbor sleeps under a blanket of stars. Brass sconces cast a gentle "
                "glow across the well-made bed and sturdy desk, while the first hints of "
                "dawn remain hours away."
            )

        # Add weather elements seamlessly
        if weather_code in WEATHER_CODES["thunderstorm"]:
            base_desc += " " + (
                " The wooden shutters rattle against the storm's fury, though they hold firm, "
                "making the room feel even more like a cozy haven. Thunder occasionally rattles "
                "the windowpanes, while lightning briefly illuminates the harbor beyond."
            )
        elif weather_code in WEATHER_CODES["rain"]:
            base_desc += " " + (
                " Raindrops pattern against the window in mesmerizing streams, their gentle "
                "rhythm adding to the room's peaceful atmosphere while providing an ever-changing "
                "view of the harbor beyond."
            )
        elif temp > 80:
            base_desc += " " + (
                " A warm breeze drifts through the partially opened window, stirring the light "
                "curtains and carrying with it the mingled scents of salt water and adventure "
                "from the harbor below."
            )
        elif temp < 60:
            base_desc += " " + (
                " A small brazier in the corner keeps the room comfortably warm, its gentle heat "
                "warding off the chill that seeps in from the harbor, while the window provides "
                "a cozy vantage point to watch the maritime activities below."
            )

        # Always end with the bathing tub
        base_desc += " " + (
            " A copper bathing tub sits in one corner, ready for hot water to be brought up "
            "from the kitchens below, promising relaxation after a day of watching the endless "
            "dance of ships and sailors in the harbor beyond."
        )

        # Wrap the text before setting it
        self.db.desc = self.wrap_text(base_desc)

class BoothRoom(TavernRoom):
    """Private booth rooms off the main tavern."""
    
    def _update_dynamic_description(self):
        """Update the booth's description based on conditions."""
        weather_data = self.get_weather_data()
        if not weather_data:
            return

        time_period = weather_data.get('time_period', 'day')
        weather_code = weather_data.get('weathercode')

        # Build the base description based on time of day
        if time_period == "dawn":
            base_desc = (
                "Early morning light seeps into this intimate booth from the main room, mingling "
                "with the warm glow of a small lantern that still burns on the solid oak table. "
                "High-backed wooden benches create a private sanctuary, their rich wood gleaming "
                "softly in the gentle illumination as the tavern slowly awakens to a new day."
            )
        elif time_period == "morning":
            base_desc = (
                "Daylight spills past the high-backed wooden benches that define this private "
                "booth, complementing the gentle glow of the table's lantern. The solid oak "
                "table stands ready for morning meetings or quiet contemplation, while the "
                "booth's secluded position offers a peaceful retreat from the tavern's daily bustle."
            )
        elif time_period == "noon":
            base_desc = (
                "The afternoon sun streams through the west-facing window of this cozy guest room, "
                "bathing the space in rich golden light that makes the wooden furniture glow warmly. "
                "A well-made bed with crisp linens rests against one wall, while a sturdy desk "
                "and chair beneath the window provide a perfect spot for watching the day unfold."
            )
        elif time_period == "early_evening":
            base_desc = (
                "The setting sun paints this cozy guest room in warm hues through its west-facing "
                "window, while freshly lit brass sconces begin their evening duties. A well-made "
                "bed with crisp linens offers comfort against one wall, and a sturdy desk and "
                "chair sit beneath the window, perfectly positioned for watching the day's end."
            )
        elif time_period == "afternoon":
            base_desc = (
                "Afternoon light filters indirectly into the booth, creating a peaceful atmosphere "
                "perfect for extended conversations. The solid oak table gleams softly, while the "
                "high-backed wooden benches offer comfortable sanctuary from the day's heat."
            )
        elif time_period == "evening":
            base_desc = (
                "The booth's lantern casts a warm, inviting glow as evening settles in, making "
                "the solid oak table and high-backed wooden benches even more welcoming for "
                "those seeking intimate conversation or quiet reflection."
            )
        elif time_period == "late_night":
            base_desc = (
                "The booth offers a quiet retreat from the tavern's late-night atmosphere. "
                "A lantern on the solid oak table provides enough light for intimate "
                "conversation, while the high-backed wooden benches ensure privacy for "
                "those seeking solitude at this hour."
            )
        elif time_period == "witching_hour":
            base_desc = (
                "The booth sits quietly in these early hours, its lantern casting a soft "
                "glow across the solid oak table. The high-backed wooden benches create a "
                "peaceful sanctuary, perfect for those who prefer the quiet company of "
                "their own thoughts."
            )

        # Add ambient elements based on weather
        if weather_code in WEATHER_CODES["thunderstorm"]:
            base_desc += " " + (
                "The sound of the storm outside is muffled here, making the booth feel even "
                "more like a protected haven, while distant thunder adds a dramatic backdrop "
                "to any conversations."
            )
        elif weather_code in WEATHER_CODES["rain"]:
            base_desc += " " + (
                "The gentle patter of rain beyond the booth adds a soothing undertone to "
                "the intimate space, making it an even more inviting spot for quiet "
                "conversation or peaceful solitude."
            )

        # Add final atmospheric touch with single space
        base_desc += " " + (
            "The high-backed benches provide excellent privacy while still allowing the "
            "comforting sounds and enticing aromas of the tavern to drift in, creating "
            "a perfect balance of seclusion and ambiance."
        )

        # Wrap the text before setting it
        self.db.desc = self.wrap_text(base_desc)

class NorthViewRoom(TavernRoom):
    """Guest rooms facing north over the town's rooftops."""
    
    def _update_dynamic_description(self):
        """Update the room's description based on conditions."""
        weather_data = self.get_weather_data()
        if not weather_data:
            return

        time_period = weather_data.get('time_period', 'day')
        weather_code = weather_data.get('weathercode')
        temp = weather_data.get('apparent_temperature', 70)

        # Build the base description based on time of day
        if time_period == "dawn":
            base_desc = (
                "The first hints of dawn are just beginning to brighten this cozy guest room, "
                "where a well-made bed with crisp linens rests against one wall. A sturdy desk "
                "and chair sit beneath the west-facing window, while brass sconces still flicker "
                "softly on the walls, their warm light gradually yielding to the growing day."
            )
        elif time_period == "morning":
            base_desc = (
                "Gentle morning light filters into this cozy guest room through its west-facing "
                "window, creating peaceful shadows from the neighboring buildings. A well-made "
                "bed with crisp linens rests against one wall, while a sturdy desk and chair "
                "beneath the window offer a quiet spot for morning contemplation."
            )
        elif time_period == "noon":
            base_desc = (
                "The afternoon sun streams through the west-facing window of this cozy guest room, "
                "bathing the space in rich golden light that makes the wooden furniture glow warmly. "
                "A well-made bed with crisp linens rests against one wall, while a sturdy desk "
                "and chair beneath the window provide a perfect spot for watching the day unfold."
            )
        elif time_period == "afternoon":
            base_desc = (
                "The afternoon sun casts long shadows through the west-facing window, creating "
                "interesting patterns across the cozy guest room. The well-made bed with crisp "
                "linens offers a perfect spot for an afternoon rest, while the sturdy desk and "
                "chair await the golden hour to come."
            )
        elif time_period == "evening":
            base_desc = (
                "Evening fills the room with warm light from both the brass sconces and the "
                "city's illumination beyond the west-facing window. The well-made bed with "
                "crisp linens promises comfort, while the desk and chair offer a perfect "
                "vantage point for watching the city's nightlife unfold."
            )
        elif time_period == "late_night":
            base_desc = (
                "Night brings a gentle quiet to this west-facing room. The city's lights "
                "shine softly through the window, while brass sconces provide warm illumination "
                "inside. A well-made bed with crisp linens offers rest, and a sturdy desk "
                "beneath the window provides a peaceful spot for late-night contemplation."
            )
        elif time_period == "witching_hour":
            base_desc = (
                "The room rests quietly in these early hours. The west-facing window shows "
                "the city's remaining lights, while brass sconces provide just enough "
                "illumination to move about comfortably. The well-made bed and simple "
                "furnishings wait patiently for the coming dawn."
            )

        # Add weather elements seamlessly
        if weather_code in WEATHER_CODES["thunderstorm"]:
            base_desc += " " + (
                " The wooden shutters are secured against the storm's fury, though thunder still "
                "rattles the windows and lightning occasionally illuminates their edges, making "
                "the room feel even more like a safe haven."
            )
        elif weather_code in WEATHER_CODES["rain"]:
            base_desc += " " + (
                " Rain streams down the windowpane in ever-changing patterns, transforming the "
                "view of the neighboring buildings into a shimmering impressionist painting and "
                "adding a soothing rhythm to the room's peaceful atmosphere."
            )
        elif temp > 80:
            base_desc += " " + (
                " A warm breeze finds its way through the partially opened window, stirring the "
                "light curtains and carrying with it the mingled scents of the city beyond."
            )
        elif temp < 60:
            base_desc += " " + (
                " A small brazier in the corner keeps the room comfortably warm, its gentle heat "
                "warding off the chill that seeps in from the city beyond the window."
            )

        # Always end with the bathing tub
        base_desc += " " + (
            " A copper bathing tub sits in one corner, ready for hot water to be brought up "
            "from the kitchens below, promising relaxation after a day of city watching."
        )

        # Wrap the text before setting it
        self.db.desc = self.wrap_text(base_desc)

class TavernKitchen(TavernRoom):
    """The busy kitchen of the Salty Maiden."""
    
    def at_object_creation(self):
        """Called when room is first created."""
        super().at_object_creation()
        # Set kitchen-specific attributes
        self.locks.add("view: tag(kitchen_staff)")  # Only staff can see details
        
    def _update_dynamic_description(self):
        """Update the kitchen's description based on conditions."""
        weather_data = self.get_weather_data()
        if not weather_data:
            return

        time_period = weather_data.get('time_period', 'day')
        
        # Build the description based on time of day
        if time_period == "dawn":
            base_desc = (
                "The kitchen is already alive with activity as the morning's preparations begin. "
                "Fresh bread dough rises in wooden bowls while the hearth fire is being stoked "
                "for the day's first batch of baking. The scent of herbs and fresh coffee fills "
                "the air as the kitchen staff moves with practiced efficiency."
            )
        elif time_period == "morning":
            base_desc = (
                "Morning finds the kitchen in full swing. Fresh-baked bread cools on racks while "
                "pots of porridge simmer on the hearth. Staff members weave around each other with "
                "practiced ease, preparing for the day's meals while handling breakfast orders."
            )
        elif time_period == "noon":
            base_desc = (
                "The kitchen bustles with midday activity. Multiple pots bubble on the massive hearth "
                "while fresh ingredients are chopped and prepared. The air is rich with the aromas of "
                "cooking food as kitchen staff expertly handle the lunch rush."
            )
        elif time_period == "afternoon":
            base_desc = (
                "A relative calm settles over the kitchen between meal rushes. Staff members prep "
                "ingredients for dinner while tending to occasional orders. The hearth still radiates "
                "warmth as pots of stew simmer slowly for the evening meal."
            )
        elif time_period == "early_evening":
            base_desc = (
                "The kitchen pulses with renewed energy as dinner preparations reach their peak. "
                "Savory aromas fill the air while the staff orchestrates the complex dance of "
                "evening service. The hearth blazes as multiple dishes cook simultaneously."
            )
        elif time_period == "evening":
            base_desc = (
                "Evening finds the kitchen operating at full capacity. Multiple dishes are prepared "
                "simultaneously as orders flow in from the tavern. The staff moves with swift "
                "precision, their practiced routines keeping pace with the dinner rush."
            )
        elif time_period == "late_night":
            base_desc = (
                "The kitchen's pace has slowed, though it remains warm and active. Late-night "
                "meals are prepared for remaining patrons while cleanup from dinner service "
                "continues. The hearth's glow provides comfortable warmth as the staff handles "
                "final orders."
            )
        elif time_period == "witching_hour":
            base_desc = (
                "Even at this hour, the kitchen maintains a quiet industry. Fresh dough is "
                "being prepared for morning bread while the night cook tends to occasional "
                "orders. The hearth burns low but steady, ready for the coming dawn."
            )

        # Add standard kitchen features
        base_desc += " " + (
            "A massive hearth dominates one wall, while well-organized preparation areas and "
            "storage shelves line the others. The ceiling supports hooks and racks for cookware "
            "and drying herbs, and a door leads back to the main tavern room."
        )

        # Wrap the text before setting it
        self.db.desc = self.wrap_text(base_desc)