"""
Relationship and knowledge tracking for characters.
"""

from enum import IntEnum

class KnowledgeLevel(IntEnum):
    """Enum for tracking how well one character knows another."""
    STRANGER = 0      # Basic race/height info only
    ACQUAINTANCE = 1  # Basic physical description + name if introduced
    FRIEND = 2        # Full description + name + messaging
    
def get_brief_description(character, include_height=True, include_race=True, include_subrace=True, include_gender=True):
    """
    Get a brief description of a character (for strangers).
    Returns height + race description based on included parameters.
    """
    description_parts = []
    
    # Get height description if included
    if include_height:
        height = character.db.height if hasattr(character.db, 'height') else 0
        race = character.db.race
        subrace = character.db.subrace if hasattr(character.db, 'subrace') else None
        gender = character.db.gender.lower() if hasattr(character.db, 'gender') else 'male'

        # Get height ranges for race/subrace/gender from settings
        from evennia.conf import settings
        height_ranges = settings.RACE_HEIGHT_RANGES

        if subrace and race in height_ranges and subrace in height_ranges[race]:
            height_range = height_ranges[race][subrace][gender]
        elif race in height_ranges:
            if isinstance(height_ranges[race], dict) and gender in height_ranges[race]:
                height_range = height_ranges[race][gender]
            else:
                height_range = height_ranges["Human"]["normal"][gender]
        else:
            height_range = height_ranges["Human"]["normal"][gender]

        if height:
            min_height = height_range["min"]
            max_height = height_range["max"]
            height_span = max_height - min_height
            quarter_span = height_span / 4

            if height < (min_height + quarter_span):
                description_parts.append("very short")
            elif height < (min_height + (2 * quarter_span)):
                description_parts.append("short")
            elif height > (max_height - quarter_span):
                description_parts.append("very tall") 
            elif height > (max_height - (2 * quarter_span)):
                description_parts.append("tall")
            else:
                description_parts.append("average height")
                
    # Get race description if included
    if include_race:
        race = character.db.race
        if include_subrace and character.db.subrace:
            race_desc = f"{character.db.subrace} {race}"
        else:
            race_desc = race
        description_parts.append(race_desc.lower())
        
    # Get gender if included
    if include_gender and hasattr(character.db, 'gender'):
        description_parts.insert(0, character.db.gender.lower())
        
    # Combine all parts
    if description_parts:
        return "a " + " ".join(description_parts)
    else:
        return "a person"
        
def get_basic_description(character):
    """
    Get a basic description of a character (for acquaintances).
    Returns notable physical features.
    """
    descriptions = character.db.descriptions or {}
    notable_features = []
    
    # Check for eye description
    if 'eyes' in descriptions:
        # Extract basic eye color from the full description
        eye_desc = descriptions['eyes'].lower()
        for color in ['blue', 'brown', 'green', 'gray', 'hazel']:
            if color in eye_desc:
                notable_features.append(f"{color} eyes")
                break
                
    # Check for hair description
    if 'hair' in descriptions:
        # Extract basic hair description
        hair_desc = descriptions['hair'].lower()
        for color in ['black', 'brown', 'blonde', 'red', 'white', 'gray']:
            if color in hair_desc:
                notable_features.append(f"{color} hair")
                break
    
    # Combine features without capitalization or period
    if notable_features:
        features_text = " and ".join(notable_features)
        return f"a {character.db.race.lower()} with {features_text} can be seen"
    else:
        # Return basic race description without period
        return f"a {character.db.race.lower()}"
    
def get_full_description(character):
    """
    Get the full description of a character (for friends).
    Returns all description fields in a formatted way.
    """
    descriptions = character.db.descriptions or {}
    
    # Get the overall text description first
    text = ""
    if hasattr(character.db, 'text_description') and character.db.text_description:
        text = character.db.text_description + "\n\n"
    
    # Define the order for body parts
    part_order = [
        'face', 'eyes', 'hair',      # Head area
        'chest', 'arms', 'hands',    # Upper body
        'back', 'stomach',           # Mid body
        'groin', 'bottom',           # Lower body
        'legs', 'feet'               # Extremities
    ]
    
    # Add race-specific parts
    if character.db.race in ["Kobold", "Ashenkin"]:
        part_order.insert(0, "horns")
        part_order.append("tail")
    elif character.db.race == "Feline":
        part_order.append("tail")
        
    # Build the detailed description
    details = []
    for part in part_order:
        if part in descriptions:
            details.append(f"{descriptions[part]}")
            
    return text + " ".join(details)
