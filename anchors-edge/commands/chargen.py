"""
Character generation commands
"""
from evennia import Command
from evennia.utils.evmenu import EvMenu
from evennia.utils import create
from evennia.utils import search
from django.conf import settings
from evennia.utils.search import search_object
from textwrap import TextWrapper
import json
import random
from pathlib import Path
from typeclasses.characters import Character
from utils.text import format_description

def _check_name(caller, name):
    """Check if name is valid and unique."""
    if len(name.split()) > 1:
        caller.msg("Character names must be a single word.")
        return False
        
    # Check for existing character with same name
    existing = search_object(name)
    if existing:
        caller.msg("That name is already taken.")
        return False
        
    return True

def wrap_text(text, width=78):
    """Helper function to wrap text consistently."""
    wrapper = TextWrapper(width=width, expand_tabs=True, 
                         replace_whitespace=False,
                         break_long_words=False,
                         break_on_hyphens=False)
    
    # Split into lines, wrap each line separately to preserve formatting
    lines = text.split('\n')
    wrapped_lines = []
    
    for line in lines:
        if line.strip():  # Only wrap non-empty lines
            wrapped_lines.append(wrapper.fill(line))
        else:
            wrapped_lines.append(line)
            
    # Rejoin the lines
    return '\n'.join(wrapped_lines)

def node_race_select(caller):
    """Select character race."""
    text = """
|c== Character Creation - Race Selection ==|n

Choose your race carefully, as it will shape your character's natural abilities and how they interact with the world.

|wAvailable Races:|n"""
    
    # Define race descriptions
    race_info = {
        "Human": {
            "desc": "Born with |y|wadaptable|n nature, humans excel at learning new skills and adjusting to any situation. Their |y|wnatural charisma|n and |y|wquick reflexes|n make them natural leaders and adventurers."
        },
        "Elf": {
            "desc": "Possessing graceful movements and long life, elves maintain an innate connection to the world around them. Their centuries of life grant them |y|wdeep wisdom|n and |y|wkeen intellect|n."
        },
        "Dwarf": {
            "desc": "Renowned for their |y|wphysical might|n and |y|wresilience|n, dwarves possess legendary |y|wstrength|n and |y|wtoughness|n. Their connection to stone and metal is unmatched."
        },
        "Gnome": {
            "desc": "Though physically small, gnomes possess |y|wgreat intellect|n and approach life with curiosity. Their |y|wmental acuity|n and |y|wquick movements|n make them excellent inventors, despite their |y|wphysical limitations|n."
        },
        "Kobold": {
            "desc": "|y|wNimble|n and |y|wclever|n, kobolds move with |y|wsurprising agility|n. While |y|wphysically weak|n, they excel through |y|wmental sharpness|n, making them exceptional scouts and problem-solvers."
        },
        "Feline": {
            "desc": "Born with |y|wnatural agility|n and grace, feline folk move with |y|wfluid precision|n. Their |y|wquick reflexes|n and |y|wcharismatic nature|n make them excellent adventurers, though their |y|wacademic disinterest|n can be a hindrance."
        },
        "Ashenkin": {
            "desc": "Mysterious and compelling, the ashenkin possess |y|wnatural charisma|n. Their |y|wmental prowess|n and |y|wcunning|n comes at the cost of their |y|wdiminished wisdom|n."
        }
    }
    
    # Display races and their descriptions
    for race, info in race_info.items():
        text += f"\n\n|520|w{race}|n"
        text += f"\n{info['desc']}"
        if race in settings.AVAILABLE_RACES and settings.AVAILABLE_RACES[race].get("subraces"):
            text += f"\n|wVariants:|n {', '.join(settings.AVAILABLE_RACES[race]['subraces'])}"
    
    text += "\n\n|wEnter your choice:|n"

    def _set_race(caller, raw_string):
        """Handle race selection."""
        args = raw_string.strip().lower().split()
        if not args:
            caller.msg("Please enter a race choice.")
            return None
            
        race = args[0].capitalize()
        if race not in settings.AVAILABLE_RACES:
            caller.msg(f"Invalid race: {race}")
            return None
            
        # Store race on the menu
        caller.ndb._menutree.race = race
            
        # Handle races with subraces
        if settings.AVAILABLE_RACES[race].get("subraces"):
            if len(args) < 2:
                # If they only entered the race name, go to subrace selection
                return "node_subrace_select"
            subrace = args[1]
            if subrace not in settings.AVAILABLE_RACES[race]["subraces"]:
                caller.msg(f"Invalid subrace for {race}. Available subraces: {', '.join(settings.AVAILABLE_RACES[race]['subraces'])}")
                return None
            # Store subrace on the menu
            caller.ndb._menutree.subrace = subrace
            
        return "node_gender_select"
    
    options = {"key": "_default", "goto": _set_race}
    return wrap_text(text), options

def node_subrace_select(caller):
    """Select a subrace for the chosen race."""
    race = caller.ndb._menutree.race
    
    text = f"""
|c== Character Creation - Subrace Selection ==|n

You have chosen to play as a |y{race}|n.
Please select a subrace from the following options:

|wAvailable Subraces:|n"""
    
    # Display available subraces with their lore descriptions
    race_info = {
        "Human": {
            "normal": "The most common variety of humans, known for their adaptability and determination. They represent the majority of human settlers in Anchors Edge.",
            "halfling": "A diminutive variety of humans who compensate for their small stature with remarkable agility and an uncanny stroke of fortune that seems to follow them."
        },
        "Elf": {
            "wood": "Standing as tall as humans but with more elongated limbs, wood elves move with a fluid grace that speaks to their deep connection with the natural world. Their features are softer than their high elf kin, and their skin often bears the weathered marks of a life lived among the elements.",
            "high": "Distinguished by their angular features and almost ethereal appearance, high elves possess an innate connection to magical energies. Their complexions tend to be pale and drawn, with sharp, aristocratic features that hint at their arcane affinity.",
            "half": "Born of human and elven parents, half-elves combine the adaptability of humans with elven grace. Their features are a unique blend of both ancestries, neither fully elven nor fully human, but beautiful in their own distinct way."
        },
        "Dwarf": {
            "mountain": "Powerfully built with broad shoulders and thick limbs, mountain dwarves are the embodiment of dwarven might. Their skin tends to be more weathered, bearing the marks of their forge work and mountain homes.",
            "hill": "More rounded in feature than their mountain kin, hill dwarves possess an earthy wisdom and hardy constitution. Their builds are stockier, and they often sport more elaborate beards adorned with clan braids."
        }
    }
    
    for subrace, desc in race_info[race].items():
        text += f"\n\n|w{subrace}|n\n{desc}"
    
    text += "\n\n|wEnter your choice:|n"
    
    def _set_subrace(caller, raw_string):
        """Handle subrace selection."""
        subrace = raw_string.strip().lower()
        if subrace not in settings.AVAILABLE_RACES[race]["subraces"]:
            caller.msg(f"Invalid subrace. Please choose from: {', '.join(settings.AVAILABLE_RACES[race]['subraces'])}")
            return None
            
        # Store subrace on the menu
        caller.ndb._menutree.subrace = subrace
        return "node_gender_select"
    
    options = {"key": "_default", "goto": _set_subrace}
    return wrap_text(text), options

def node_background_select(caller):
    """Select character background."""
    text = """
|c== Character Creation - Background Selection ==|n

Your background represents your history and reason for coming to the island.
This choice will affect your starting location and initial relationships.

|wAvailable Backgrounds:|n"""
    
    # Display backgrounds and their descriptions
    for bg, info in settings.CHARACTER_BACKGROUNDS.items():
        text += f"\n\n|y{bg}|n"
        text += f"\n    {info['desc']}"
    
    text += "\n\n|wEnter the name of your chosen background:|n"
    
    def _set_background(caller, raw_string):
        """Handle background selection."""
        background = raw_string.strip().title()
        if background not in settings.CHARACTER_BACKGROUNDS:
            caller.msg(f"Invalid background. Please choose from: {', '.join(settings.CHARACTER_BACKGROUNDS.keys())}")
            return None
            
        # Store background on the menu
        caller.ndb._menutree.background = background
        return "node_description_select"
    
    options = {"key": "_default", "goto": _set_background}
    return wrap_text(text), options

def format_full_description(descriptions):
    """Format all descriptions into a cohesive character appearance using natural sentences."""
    parts = []
    gender = descriptions.get('gender', 'their')  # Default to gender-neutral if not specified
    pronoun = 'Their' if gender == 'their' else gender == 'male' and 'His' or 'Her'
    
    # Face area (eyes, hair, face)
    face_features = []
    if 'eyes' in descriptions:
        face_features.append(f"{pronoun} eyes {descriptions['eyes']}")
    if 'hair' in descriptions:
        face_features.append(f"{pronoun} hair {descriptions['hair']}")
    if 'face' in descriptions:
        face_features.append(f"{pronoun} face {descriptions['face']}")
    if face_features:
        parts.append(" ".join(face_features))
    
    # Upper body (arms, chest, back)
    upper_body = []
    if 'arms' in descriptions:
        upper_body.append(f"{pronoun} arms {descriptions['arms']}")
    if 'chest' in descriptions:
        upper_body.append(f"{pronoun} chest {descriptions['chest']}")
    if 'back' in descriptions:
        upper_body.append(f"{pronoun} back {descriptions['back']}")
    if upper_body:
        parts.append(" ".join(upper_body))
    
    # Lower body (stomach, legs, feet)
    lower_body = []
    if 'stomach' in descriptions:
        lower_body.append(f"{pronoun} stomach {descriptions['stomach']}")
    if 'legs' in descriptions:
        lower_body.append(f"{pronoun} legs {descriptions['legs']}")
    if 'feet' in descriptions:
        lower_body.append(f"{pronoun} feet {descriptions['feet']}")
    if lower_body:
        parts.append(" ".join(lower_body))
    
    # Special features last (horns, tail)
    special = []
    if 'horns' in descriptions:
        special.append(f"{pronoun} horns {descriptions['horns']}")
    if 'tail' in descriptions:
        special.append(f"{pronoun} tail {descriptions['tail']}")
    if special:
        parts.append(" ".join(special))
    
    # Join all parts with proper spacing and capitalization
    description = " ".join(parts)
    
    # Ensure the first letter is capitalized
    if description:
        description = description[0].upper() + description[1:]
    
    return description

def node_description_select(caller):
    """Select character descriptions."""
    text = """
|c== Character Creation - Character Description ==|n

Your character has been given default descriptions based on their race and gender. You can:
- Type |wshow|n to see your character's full appearance
- Type |wshow <part>|n to see a specific description
- Type |w<part> <description>|n to change a description
- Type |whelp|n to see example descriptions for your race
- Type |wdone|n when finished

Remember to write descriptions that will flow naturally in a sentence.
For example, if your character is female, write descriptions like:
|wEyes:|n "are a deep emerald green with flecks of gold"
|wHair:|n "falls in soft auburn waves past her shoulders"
|wFace:|n "bears a gentle expression, with high cheekbones"

These will be formatted into sentences like:
"Her eyes are a deep emerald green with flecks of gold. Her hair falls in soft auburn waves past her shoulders."

Available parts: eyes, hair, face, hands, arms, chest, stomach, back, legs, feet, groin, bottom"""

    # Add race-specific parts to the help text
    race = caller.ndb._menutree.race
    if race in ["Kobold", "Ashenkin"]:
        text += ", horns, tail"
    elif race == "Feline":
        text += ", tail"

    # Initialize descriptions dict if not exists
    if not hasattr(caller.ndb._menutree, 'descriptions'):
        # Generate default descriptions based on race and gender
        gender = caller.ndb._menutree.gender.lower()  # Convert to lowercase to match JSON structure
        
        # Load descriptions from JSON
        with open(Path("data/descriptions/body_parts.json"), 'r') as f:
            race_descriptions = json.load(f)
            
        if race in race_descriptions and gender in race_descriptions[race]:
            default_descs = race_descriptions[race][gender]
            descriptions = {}
            for part, descs in default_descs.items():
                if isinstance(descs, list) and descs:
                    descriptions[part] = random.choice(descs)
                else:
                    descriptions[part] = descs
            caller.ndb._menutree.descriptions = descriptions
        else:
            # Fallback to empty descriptions if race/gender combo not found
            caller.ndb._menutree.descriptions = {}

    def _handle_description(caller, raw_string):
        """Handle description input."""
        args = raw_string.strip().lower().split(None, 1)
        if not args:
            return None

        command = args[0]

        if command == 'done':
            return "node_text_descriptor"
            
        if command == 'help':
            race = caller.ndb._menutree.race
            gender = caller.ndb._menutree.gender.lower()
            pronoun = 'Their' if gender == 'their' else gender == 'male' and 'His' or 'Her'
            
            if race in settings.RACE_DESCRIPTIONS:
                examples = settings.RACE_DESCRIPTIONS[race]
                caller.msg(f"\n|cExample descriptions for your {race}:|n")
                for part, descs in examples.items():
                    if isinstance(descs, list) and descs:
                        caller.msg(f"|w{part}:|n {pronoun} {part} {descs[0]}")
            return None
            
        if command == 'show':
            # Set a flag to suppress menu redisplay
            caller.ndb._menutree.suppress_menu = True
            
            if len(args) > 1:
                # Show specific part
                part = args[1]
                if part in caller.ndb._menutree.descriptions:
                    gender = caller.ndb._menutree.gender.lower()
                    pronoun = 'Their' if gender == 'their' else gender == 'male' and 'His' or 'Her'
                    caller.msg(f"|w{part.title()}:|n {pronoun} {part} {caller.ndb._menutree.descriptions[part]}")
                else:
                    caller.msg(f"No description set for {part}.")
            else:
                # Show all descriptions in natural format
                if hasattr(caller.ndb._menutree, 'descriptions'):
                    caller.msg("|c== Your Character's Appearance ==|n\n")
                    caller.msg(format_full_description(caller.ndb._menutree.descriptions))
                else:
                    caller.msg("No descriptions set yet.")
            return None

        # Handle setting a description
        valid_parts = [
            "eyes", "hair", "face", "hands", "arms", "chest", 
            "stomach", "back", "legs", "feet", "groin", "bottom"
        ]
        
        # Add race-specific parts
        if race in ["Kobold", "Ashenkin"]:
            valid_parts.extend(["horns", "tail"])
        elif race == "Feline":
            valid_parts.append("tail")

        if command not in valid_parts:
            caller.msg(f"Valid body parts are: {', '.join(valid_parts)}")
            return None

        if len(args) < 2:
            caller.msg(f"Please provide a description for {command}.")
            return None

        # Store the description
        caller.ndb._menutree.descriptions[command] = args[1]
        
        # Show how it looks in a sentence
        gender = caller.ndb._menutree.gender.lower()
        pronoun = 'Their' if gender == 'their' else gender == 'male' and 'His' or 'Her'
        caller.msg(f"\nSet description: {pronoun} {command} {args[1]}")
        return None
            
    options = {"key": "_default", "goto": _handle_description}
    
    # Check if we should suppress menu display
    if hasattr(caller.ndb._menutree, 'suppress_menu') and caller.ndb._menutree.suppress_menu:
        # Clear the flag and return empty text
        del caller.ndb._menutree.suppress_menu
        return "", options
    
    return text, options

def node_name_select(caller):
    """Select character name."""
    text = """
|c== Character Creation - Name Selection ==|n

Choose a name for your character. This name will identify you in the game world.

|wRequirements:|n
- Must be a single word
- Must be unique
- Should fit the game's setting

|wEnter your character's name:|n"""
    
    def _set_name(caller, raw_string):
        """Handle name input"""
        name = raw_string.strip()
        if _check_name(caller, name):
            caller.ndb._menutree.charname = name
            return "node_name_confirm"
        return None
    
    options = {"key": "_default", "goto": _set_name}
    return wrap_text(text), options

def node_name_confirm(caller):
    """Confirm name selection."""
    name = caller.ndb._menutree.charname
    race = caller.ndb._menutree.race
    subrace = caller.ndb._menutree.subrace if hasattr(caller.ndb._menutree, 'subrace') else None
    
    text = f"""
|c== Character Creation - Name Confirmation ==|n

You have chosen the name: |y{name}|n
For your {f"{race} ({subrace})" if subrace else race} character.

Are you sure you want to use this name?

|wEnter |gyes|w to confirm or |rno|w to choose again:|n
"""
    
    def _confirm_name(caller, raw_string):
        """Handle name confirmation."""
        choice = raw_string.strip().lower()
        if choice == "yes":
            return "node_final_confirm"
        elif choice == "no":
            if hasattr(caller.ndb._menutree, 'charname'):
                del caller.ndb._menutree.charname
            return "node_name_select"
        else:
            caller.msg("Please enter 'yes' or 'no'.")
            return None
    
    options = {"key": "_default", "goto": _confirm_name}
    return wrap_text(text), options

def node_create_char(caller):
    """Create the character."""
    try:
        charname = caller.ndb._menutree.charname
        race = caller.ndb._menutree.race
        subrace = caller.ndb._menutree.subrace if hasattr(caller.ndb._menutree, 'subrace') else None
        gender = caller.ndb._menutree.gender if hasattr(caller.ndb._menutree, 'gender') else None
        background = caller.ndb._menutree.background if hasattr(caller.ndb._menutree, 'background') else None
        text_description = caller.ndb._menutree.text_description if hasattr(caller.ndb._menutree, 'text_description') else None

        # Create character using the imported create.create_object
        char = create.create_object(
            Character,
            key=charname,
            home=settings.START_LOCATION,
            location=settings.START_LOCATION,
            permissions=["Player"],  # Only basic player permissions
            locks=f"puppet:id({caller.id}) or pid({caller.id});examine:id({caller.id}) or perm(Admin);edit:perm(Admin);delete:perm(Admin);get:false()"  # More restrictive locks
        )

        # Set character attributes
        char.db.race = race
        if subrace:
            char.db.subrace = subrace
        if gender:
            char.db.gender = gender
        if background:
            char.db.background = background
        if text_description:
            char.db.text_description = text_description

        # Store descriptions
        if hasattr(caller.ndb._menutree, 'descriptions'):
            char.db.descriptions = caller.ndb._menutree.descriptions

        # Add character to account's playable characters
        if not caller.db._playable_characters:
            caller.db._playable_characters = []
        caller.db._playable_characters.append(char)
        
        # Set account reference on character
        char.db.account = caller
        
        if hasattr(caller.ndb._menutree, 'age'):
            char.db.age = caller.ndb._menutree.age

        text = f"""
|c== Character Creation Complete! ==|n

|wCharacter Details:|n
Name: |y{charname}|n
Race: |y{race}{f" ({subrace})" if subrace else ""}|n
Gender: |y{gender if gender else "Not specified"}|n
Background: |y{background if background else "Not specified"}|n

|wAppearance:|n
{char.format_description()}

Your character has been created and is ready to enter the world.
Use |wcharselect {charname}|n to begin your adventure!

You have {settings.MAX_CHARACTERS_PER_ACCOUNT - len(caller.db._playable_characters)} character slots remaining.
"""
        return wrap_text(text), None
        
    except Exception as e:
        caller.msg(f"Error creating character: {e}")
        if 'char' in locals() and char:
            char.delete()
        return None

def node_final_confirm(caller):
    """Final confirmation before character creation."""
    race = caller.ndb._menutree.race
    subrace = caller.ndb._menutree.subrace if hasattr(caller.ndb._menutree, 'subrace') else None
    gender = caller.ndb._menutree.gender if hasattr(caller.ndb._menutree, 'gender') else None
    background = caller.ndb._menutree.background if hasattr(caller.ndb._menutree, 'background') else None
    charname = caller.ndb._menutree.charname if hasattr(caller.ndb._menutree, 'charname') else None
    text_description = caller.ndb._menutree.text_description if hasattr(caller.ndb._menutree, 'text_description') else None
    
    text = f"""
|c== Character Creation - Final Confirmation ==|n

Please review your character details:

|wName:|n {charname}
|wRace:|n {race}{f" ({subrace})" if subrace else ""}
|wGender:|n {gender if gender else "Not specified"}
|wAge:|n {caller.ndb._menutree.age if hasattr(caller.ndb._menutree, 'age') else "Not specified"}
|wBackground:|n {background if background else "Not specified"}

|wOverall Description:|n
{text_description if text_description else "No overall description provided."}

|wDetailed Appearance:|n
"""
    
    # Add description details
    if hasattr(caller.ndb._menutree, 'descriptions'):
        # Define the order we want to show parts in
        part_order = [
            'eyes', 'hair', 'face', 'hands', 'arms', 'chest', 
            'stomach', 'back', 'legs', 'feet', 'groin', 'bottom'
        ]
        
        # Add race-specific parts
        if race in ["Kobold", "Ashenkin"]:
            part_order.extend(["horns", "tail"])
        elif race == "Feline":
            part_order.append("tail")
            
        # Display descriptions in order
        for part in part_order:
            if part in caller.ndb._menutree.descriptions:
                text += f"\n|w{part}:|n {caller.ndb._menutree.descriptions[part]}"
    
    text += "\n\n|wIs this correct? Enter |gyes|w to create your character or |rno|w to start over:|n"

    def _final_confirm(caller, raw_string):
        """Handle final confirmation input."""
        choice = raw_string.strip().lower()
        if choice == "yes":
            return "node_create_char"
        elif choice == "no":
            # Clear all stored data
            if hasattr(caller.ndb._menutree, 'race'):
                del caller.ndb._menutree.race
            if hasattr(caller.ndb._menutree, 'subrace'):
                del caller.ndb._menutree.subrace
            if hasattr(caller.ndb._menutree, 'gender'):
                del caller.ndb._menutree.gender
            if hasattr(caller.ndb._menutree, 'background'):
                del caller.ndb._menutree.background
            if hasattr(caller.ndb._menutree, 'charname'):
                del caller.ndb._menutree.charname
            if hasattr(caller.ndb._menutree, 'descriptions'):
                del caller.ndb._menutree.descriptions
            return "node_race_select"
        else:
            caller.msg("Please enter 'yes' or 'no'.")
            return None

    options = {"key": "_default", "goto": _final_confirm}
    return text, options

def node_gender_select(caller):
    """Select character gender."""
    text = """
|c== Character Creation - Gender Selection ==|n

Is your character male or female?
Enter |wm|n or |wf|n:"""
    
    def _set_gender(caller, raw_string):
        """Handle gender selection."""
        choice = raw_string.strip().lower()
        
        if choice in ['m', 'male']:
            caller.ndb._menutree.gender = 'Male'
            return "node_height_select"
        elif choice in ['f', 'female']:
            caller.ndb._menutree.gender = 'Female'
            return "node_height_select"
        else:
            caller.msg("Please enter 'm' or 'f'.")
            return None
    
    options = {"key": "_default", "goto": _set_gender}
    return wrap_text(text), options

def node_height_select(caller):
    """Select character height."""
    race = caller.ndb._menutree.race
    subrace = caller.ndb._menutree.subrace if hasattr(caller.ndb._menutree, 'subrace') else None
    gender = caller.ndb._menutree.gender.lower()
    
    text = f"""
|c== Character Creation - Height Selection ==|n

Choose your character's height. Different races have different natural height ranges.

|wHeight Range for {race}{f" ({subrace})" if subrace else ""}:|n"""

    # Get height ranges for race/subrace/gender
    if subrace and race in settings.RACE_HEIGHT_RANGES and subrace in settings.RACE_HEIGHT_RANGES[race]:
        height_range = settings.RACE_HEIGHT_RANGES[race][subrace][gender]
    elif race in settings.RACE_HEIGHT_RANGES:
        if isinstance(settings.RACE_HEIGHT_RANGES[race], dict) and gender in settings.RACE_HEIGHT_RANGES[race]:
            height_range = settings.RACE_HEIGHT_RANGES[race][gender]
        else:
            height_range = settings.RACE_HEIGHT_RANGES["Human"]["normal"][gender]
    else:
        height_range = settings.RACE_HEIGHT_RANGES["Human"]["normal"][gender]

    # Convert min/max to feet and inches for display
    min_feet = height_range["min"] // 12
    min_inches = height_range["min"] % 12
    max_feet = height_range["max"] // 12
    max_inches = height_range["max"] % 12
    
    # Calculate average height for example
    avg_inches = (height_range["min"] + height_range["max"]) // 2
    avg_feet = avg_inches // 12
    avg_inch = avg_inches % 12
    
    text += f"\nMinimum: {min_feet}'{min_inches}"
    text += f"\nMaximum: {max_feet}'{max_inches}"

    text += f"\n\n|wEnter your desired height (in feet/inches like {avg_feet}'{avg_inch}):|n"

    def _set_height(caller, raw_string):
        """Handle height selection."""
        try:
            # Clean up the input string
            height_str = raw_string.replace("'", " ").replace(".", " ")
            parts = height_str.split()
            
            if len(parts) >= 2:
                feet = int(parts[0])
                inches = int(parts[1])
            else:
                feet = int(parts[0])
                inches = 0
                
            # Convert to total inches
            total_inches = (feet * 12) + inches
            
            # Get gender
            gender = caller.ndb._menutree.gender.lower()
            
            # Get valid height range
            if subrace and race in settings.RACE_HEIGHT_RANGES and subrace in settings.RACE_HEIGHT_RANGES[race]:
                valid_range = settings.RACE_HEIGHT_RANGES[race][subrace][gender]
            elif race in settings.RACE_HEIGHT_RANGES:
                if isinstance(settings.RACE_HEIGHT_RANGES[race], dict) and gender in settings.RACE_HEIGHT_RANGES[race]:
                    valid_range = settings.RACE_HEIGHT_RANGES[race][gender]
                else:
                    valid_range = settings.RACE_HEIGHT_RANGES["Human"]["normal"][gender]
            else:
                valid_range = settings.RACE_HEIGHT_RANGES["Human"]["normal"][gender]
            
            # Check if height is within valid range
            if total_inches < valid_range["min"] or total_inches > valid_range["max"]:
                min_feet = valid_range["min"] // 12
                min_inches = valid_range["min"] % 12
                max_feet = valid_range["max"] // 12
                max_inches = valid_range["max"] % 12
                caller.msg(f"Height must be between {min_feet}'{min_inches} and {max_feet}'{max_inches}")
                return None
            
            # Store height in inches
            caller.ndb._menutree.height = total_inches
            return "node_height_confirm"
            
        except ValueError:
            caller.msg("Please enter a valid height (e.g. 6'2)")
            return None
    
    options = {"key": "_default", "goto": _set_height}
    return wrap_text(text), options

def node_height_confirm(caller):
    """Confirm height selection."""
    total_inches = caller.ndb._menutree.height
    feet = total_inches // 12
    inches = total_inches % 12
    
    text = f"""
|c== Character Creation - Height Confirmation ==|n

You have selected a height of:
|w{feet}'{inches}|n

Is this the height you want?
|wEnter |gyes|w to confirm or |rno|w to choose again:|n
"""
    
    def _confirm_height(caller, raw_string):
        """Handle height confirmation."""
        choice = raw_string.strip().lower()
        if choice == "yes":
            return "node_age_select"
        elif choice == "no":
            return "node_height_select"
        else:
            caller.msg("Please enter 'yes' or 'no'.")
            return None
    
    options = {"key": "_default", "goto": _confirm_height}
    return wrap_text(text), options

def node_age_select(caller):
    """Select character age."""
    race = caller.ndb._menutree.race
    
    # Define age ranges for each race
    age_ranges = {
        "Human": {"min": 18, "max": 75},
        "Elf": {"min": 18, "max": 600},  # Elves are long-lived
        "Dwarf": {"min": 18, "max": 300},  # Dwarves live several centuries
        "Gnome": {"min": 18, "max": 350},  # Gnomes are also long-lived
        "Kobold": {"min": 18, "max": 50},  # Shorter lifespan
        "Feline": {"min": 18, "max": 70},  # Similar to humans
        "Ashenkin": {"min": 18, "max": 175}  # Magical nature extends life
    }
    
    # Get the age range for the selected race
    age_range = age_ranges.get(race, age_ranges["Human"])  # Default to human if race not found
    
    text = f"""
|c== Character Creation - Age Selection ==|n

Choose your character's age. Different races have different natural lifespans.

|wAge Range for {race}:|n
Minimum: {age_range['min']} years
Maximum: {age_range['max']} years

|wEnter your character's age (in years):|n"""

    def _set_age(caller, raw_string):
        """Handle age selection."""
        try:
            age = int(raw_string.strip())
            
            # Validate age range
            if age < age_range["min"]:
                caller.msg(f"Age must be at least {age_range['min']} years.")
                return None
            elif age > age_range["max"]:
                caller.msg(f"Age cannot exceed {age_range['max']} years for {race}s.")
                return None
                
            # Store age
            caller.ndb._menutree.age = age
            return "node_age_confirm"
            
        except ValueError:
            caller.msg("Please enter a valid number for age.")
            return None
    
    options = {"key": "_default", "goto": _set_age}
    return wrap_text(text), options

def node_age_confirm(caller):
    """Confirm age selection."""
    age = caller.ndb._menutree.age
    race = caller.ndb._menutree.race
    
    text = f"""
|c== Character Creation - Age Confirmation ==|n

You have selected an age of:
|w{age} years|n

Is this the age you want for your {race}?
|wEnter |gyes|w to confirm or |rno|w to choose again:|n
"""
    
    def _confirm_age(caller, raw_string):
        """Handle age confirmation."""
        choice = raw_string.strip().lower()
        if choice == "yes":
            return "node_background_select"
        elif choice == "no":
            return "node_age_select"
        else:
            caller.msg("Please enter 'yes' or 'no'.")
            return None
    
    options = {"key": "_default", "goto": _confirm_age}
    return wrap_text(text), options

def node_description_edit(caller):
    """Allow editing of character descriptions."""
    # Set flag to allow desc command
    caller.ndb._menutree.chargen_in_progress = True
    
    text = """
|c== Character Creation - Description Editing ==|n

You can now edit the descriptions of your character's features.
Use the following command to view and edit descriptions:

|wdesc|n                  - Show all current descriptions
|wdesc <part>|n          - Show description for specific part
|wdesc <part> <text>|n   - Set new description for part

Available body parts: eyes, hair, face, hands, arms, chest, stomach, back, legs, feet, groin, bottom
"""

    # Add race-specific parts to the help text
    race = caller.ndb._menutree.race
    if race in ["Kobold", "Ashenkin"]:
        text += ", horns, tail"
    elif race == "Feline":
        text += ", tail"

    text += "\n\nWhen you are satisfied with your descriptions, type |wcontinue|n to proceed."

    def _desc_done(caller, raw_string):
        """Handle completion of description editing."""
        if raw_string.strip().lower() == "continue":
            # Remove the flag that allows desc command
            del caller.ndb._menutree.chargen_in_progress
            return "node_final_confirm"
        return None

    options = {"key": "_default", "goto": _desc_done}
    return text, options

class CharacterGenerator:
    def __init__(self):
        # Load body part descriptions
        data_path = Path("data/descriptions/body_parts.json")
        with open(data_path, 'r') as f:
            self.body_descriptions = json.load(f)

    def generate_default_descriptions(self, race):
        """
        Generate default descriptions for all body parts based on race
        Returns a dictionary of body parts and their randomly selected descriptions
        """
        if race not in self.body_descriptions:
            # Fallback to Human if race not found
            race = "Human"
        
        race_descriptions = self.body_descriptions[race]
        default_descriptions = {}
        
        for part, descriptions in race_descriptions.items():
            # Handle both single string and list of descriptions
            if isinstance(descriptions, list):
                default_descriptions[part] = random.choice(descriptions)
            else:
                default_descriptions[part] = descriptions
                
        return default_descriptions

    def apply_descriptions_to_character(self, character, descriptions):
        """
        Apply the generated descriptions to the character's db attributes
        """
        # Initialize descriptions dict if it doesn't exist
        if not character.db.descriptions:
            character.db.descriptions = {}
            
        # Apply the descriptions
        for part, desc in descriptions.items():
            character.db.descriptions[part] = desc

class DescCommand(Command):
    """
    Set the description for a body part during character creation
    
    Usage:
        desc <body_part> <description>
        desc <body_part>          - shows current description
        desc                      - shows all body part descriptions
    """
    
    key = "desc"
    locks = "cmd:all()"
    
    def func(self):
        # Check if we're in character creation
        if not self.caller.ndb._menutree or not hasattr(self.caller.ndb._menutree, 'chargen_in_progress'):
            self.caller.msg("This command is only available during character creation.")
            return
            
        # Initialize descriptions if they don't exist
        if not self.caller.db.descriptions:
            self.caller.db.descriptions = {}
            
        if not self.args:
            # Show all descriptions
            self.caller.msg("|c== Your Body Part Descriptions ==|n")
            for part, desc in self.caller.db.descriptions.items():
                self.caller.msg(f"\n|w{part.title()}:|n\n{desc}")
            return
            
        try:
            part = self.args.split(" ", 1)[0].lower()
        except ValueError:
            self.caller.msg("Usage: desc <body_part> <description>")
            return
            
        # If no description provided, show current description
        if len(self.args.split(" ", 1)) == 1:
            if part in self.caller.db.descriptions:
                self.caller.msg(f"|w{part.title()}:|n\n{self.caller.db.descriptions[part]}")
            else:
                self.caller.msg(f"No description set for {part}.")
            return
            
        part, description = self.args.split(" ", 1)
        part = part.lower()
        
        valid_parts = [
            "eyes", "hair", "face", "hands", "arms", "chest", 
            "stomach", "back", "legs", "feet", "groin", "bottom"
        ]
        
        # Add race-specific parts if character has them
        if hasattr(self.caller, "race"):
            if self.caller.race in ["Kobold", "Ashenkin"]:
                valid_parts.extend(["horns", "tail"])
            elif self.caller.race == "Feline":
                valid_parts.append("tail")
        
        if part not in valid_parts:
            self.caller.msg(f"Valid body parts are: {', '.join(valid_parts)}")
            return
            
        # Set the new description
        self.caller.db.descriptions[part] = description
        self.caller.msg(f"Your {part} description has been updated.")

def ensure_default_home():
    """Ensure the default home location exists."""
    from evennia.utils import create, search
    from django.conf import settings
    
    # First try to find Limbo
    limbo = search.search_object("Limbo")
    if limbo:
        return limbo[0]
    
    # If Limbo doesn't exist, create it
    limbo = create.create_object(
        "typeclasses.rooms.WeatherAwareRoom",
        key="Limbo",
        nohome=True
    )
    limbo.db.desc = "This is a blank room serving as the default home location."
    
    # Set the default home setting
    settings.DEFAULT_HOME = "#{}".format(limbo.id)
    
    return limbo

class CmdCreateCharacter(Command):
    """
    Create a new character
    
    Usage:
        charcreate
    """
    key = "charcreate"
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Start character creation menu."""
        # Check character limit
        if len(self.caller.db._playable_characters) >= settings.MAX_CHARACTERS_PER_ACCOUNT:
            self.caller.msg("|rYou have reached the maximum number of characters allowed (5).|n")
            self.caller.msg("You must delete a character before creating a new one.")
            return

        # Only show age verification if this is their first character
        if not self.caller.db._playable_characters and not self.caller.db.age_verified:
            start_node = "node_age_verification"
        else:
            start_node = "node_race_select"
            
        # Ensure we have a default home location
        default_home = ensure_default_home()
        
        # Clean up any existing character creation data
        if hasattr(self.caller.ndb, '_menutree'):
            del self.caller.ndb._menutree
            
        # Store the default home in the menu tree for later use
        self.caller.ndb._menutree = type('MenuData', (), {'default_home': default_home})
        
        def custom_formatter(optionlist):
            """
            Don't display the options - they're already in the node text
            """
            return ""
            
        def node_formatter(nodetext, optionstext):
            """
            Simply return the node text without any formatting
            """
            return nodetext
            
        # Start the menu with custom formatting
        EvMenu(self.caller,
               {
                   "node_age_verification": node_age_verification,     # 0. Age verification
                   "node_race_select": node_race_select,              # 1. Select race
                   "node_subrace_select": node_subrace_select,        # 2. Select subrace (if applicable)
                   "node_gender_select": node_gender_select,          # 3. Select gender
                   "node_height_select": node_height_select,          # 4. Select height
                   "node_height_confirm": node_height_confirm,        # 5. Confirm height
                   "node_age_select": node_age_select,               # 6. Select age
                   "node_age_confirm": node_age_confirm,             # 7. Confirm age
                   "node_background_select": node_background_select,  # 8. Select background
                   "node_description_select": node_description_select, # 9. Customize descriptions
                   "node_text_descriptor": node_text_descriptor,      # 10. Overall text description
                   "node_name_select": node_name_select,             # 11. Choose name
                   "node_name_confirm": node_name_confirm,           # 12. Confirm name
                   "node_final_confirm": node_final_confirm,         # 13. Final review
                   "node_create_char": node_create_char              # 14. Create character
               },
               startnode=start_node,
               cmd_on_exit=None,
               options_formatter=custom_formatter,
               node_formatter=node_formatter,
               options_separator="")
  
def node_age_verification(caller):
    """Initial age verification check."""
    text = """
|r== AGE VERIFICATION REQUIRED ==|n

|rWARNING: This is an adult-oriented game with mature themes and content.|n

This game contains:
- Adult situations and themes
- Mature content and descriptions
- Content not suitable for minors

|rBy continuing, you verify that:|n
- You are at least 18 years of age
- You are legally able to view adult content in your jurisdiction
- You understand this is an adult-oriented game

|wEnter |g'yes'|w to confirm you are 18+ and accept these terms.
Enter |r'no'|w to disconnect.|n
"""

    def _verify_age(caller, raw_string):
        """Handle age verification response."""
        choice = raw_string.strip().lower()
        if choice == "yes":
            # Store verification on the account
            caller.db.age_verified = True
            return "node_race_select"
        elif choice == "no":
            caller.msg("\n|rYou must be 18 or older to play this game. Disconnecting...|n")
            caller.session_disconnect()
            return None
        else:
            caller.msg("Please enter 'yes' or 'no'.")
            return None

    options = {"key": "_default", "goto": _verify_age}
    return wrap_text(text), options
  
def node_text_descriptor(caller):
    """Allow setting an overall character description."""
    text = """
|c== Character Creation - Overall Description ==|n

Here you can provide an overall description of your character that goes beyond individual body parts.
This is your chance to paint a complete picture of how others see your character.

You can describe:
- General appearance and presence
- How they carry themselves
- Distinctive features or mannerisms
- Overall impression they make
- Clothing style or typical attire
- Notable scars, markings, or accessories

Current description:
"""
    
    if hasattr(caller.ndb._menutree, 'text_description'):
        text += f"\n{format_description(caller.ndb._menutree.text_description)}\n"
    else:
        text += "\n|yNo description set yet.|n\n"
    
    text += """
|wCommands:|n
- Type your description to set it
- Type |wshow|n to see your current description
- Type |wclear|n to remove your description
- Type |wskip|n to continue without a description
- Type |wdone|n when finished

Your description should be a paragraph or two that brings your character to life."""

    def _handle_text_description(caller, raw_string):
        """Handle text description input."""
        command = raw_string.strip().lower()
        
        if command == 'done':
            if not hasattr(caller.ndb._menutree, 'text_description'):
                caller.msg("You haven't set a description yet. Type |wskip|n if you don't want to set one.")
                return None
            return "node_name_select"
            
        if command == 'skip':
            return "node_name_select"
            
        if command == 'show':
            if hasattr(caller.ndb._menutree, 'text_description'):
                caller.msg("|wCurrent Description:|n")
                caller.msg(format_description(caller.ndb._menutree.text_description))
            else:
                caller.msg("|yNo description set yet.|n")
            return None
            
        if command == 'clear':
            if hasattr(caller.ndb._menutree, 'text_description'):
                del caller.ndb._menutree.text_description
                caller.msg("Description cleared.")
            else:
                caller.msg("No description to clear.")
            return None
            
        # If not a command, treat as new description
        if raw_string.strip():
            caller.ndb._menutree.text_description = format_description(raw_string.strip())
            caller.msg("\n|wDescription set to:|n")
            caller.msg(caller.ndb._menutree.text_description)
            caller.msg("\nType |wdone|n when satisfied or enter a new description to change it.")
        return None
            
    options = {"key": "_default", "goto": _handle_text_description}
    return wrap_text(text), options
  