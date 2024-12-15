"""
Relationship and knowledge tracking for characters.
"""

from enum import IntEnum
from django.conf import settings

class KnowledgeLevel(IntEnum):
    """Enum for different levels of character knowledge"""
    NONE = 0
    STRANGER = 1
    ACQUAINTANCE = 2
    FRIEND = 3
    
def get_brief_description(character, include_height=True, include_race=True, include_subrace=True, include_gender=True, include_rstatus=False, include_ostatus=False):
    """
    Get a brief description of a character (for strangers).
    Returns height + race description based on included parameters.
    
    Args:
        character: The character to describe
        include_height (bool): Whether to include height description
        include_race (bool): Whether to include race
        include_subrace (bool): Whether to include subrace
        include_gender (bool): Whether to include gender
        include_rstatus (bool): Whether to include roleplay status
        include_ostatus (bool): Whether to include optional status
    """
    # Start with optional status if included
    if include_ostatus and hasattr(character, 'get_ostatus'):
        ostatus = character.get_ostatus()
        if ostatus:
            return f"{ostatus}\n\na {get_brief_description(character, include_height, include_race, include_subrace, include_gender)}"
    
    description_parts = []
    
    # Get height description if included
    if include_height:
        height = character.db.height if hasattr(character.db, 'height') else 0
        race = character.db.race
        subrace = character.db.subrace if hasattr(character.db, 'subrace') else None
        gender = character.db.gender.lower() if hasattr(character.db, 'gender') else 'male'

        # Get height ranges for race/subrace/gender from settings
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
        
    # Get gender if included
    if include_gender and hasattr(character.db, 'gender'):
        description_parts.append(character.db.gender.lower())
        
     # Get race description if included
    if include_race:
        race = character.db.race
        if include_subrace and character.db.subrace:
            race_desc = f"{character.db.subrace} {race}"
        else:
            race_desc = race
        description_parts.append(race_desc.lower())
        
    # Build base description
    base_desc = "a person"
    if description_parts:
        base_desc = "a " + " ".join(description_parts)

    # Add roleplay status if included
    if include_rstatus and hasattr(character, 'get_rstatus'):
        rstatus = character.get_rstatus()
        if rstatus:
            # Check if character is drunk
            is_drunk = hasattr(character.db, 'intoxication') and character.db.intoxication > 0
            if is_drunk:
                rstatus = f"{rstatus} (and appears to be drunk)"
            return f"{base_desc} ({rstatus})"

    return base_desc
        
def get_basic_description(character, include_rstatus=False, include_ostatus=False):
    """
    Get a basic description of a character (for acquaintances).
    Returns notable physical features.
    
    Args:
        character: The character to describe
        include_rstatus (bool): Whether to include roleplay status
        include_ostatus (bool): Whether to include optional status
    """
    # Start with optional status if included
    if include_ostatus and hasattr(character, 'get_ostatus'):
        ostatus = character.get_ostatus()
        if ostatus:
            return f"{ostatus}\n\n{get_basic_description(character)}"
    
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
    
    # Build base description
    base_desc = f"a {character.db.race.lower()}"
    if notable_features:
        features_text = " and ".join(notable_features)
        base_desc = f"a {character.db.race.lower()} with {features_text} can be seen"

    # Add roleplay status if included
    if include_rstatus and hasattr(character, 'get_rstatus'):
        rstatus = character.get_rstatus()
        if rstatus:
            # Check if character is drunk
            is_drunk = hasattr(character.db, 'intoxication') and character.db.intoxication > 0
            if is_drunk:
                rstatus = f"{rstatus} (and appears to be drunk)"
            return f"{base_desc} ({rstatus})"

    return base_desc
    
def get_full_description(character, include_rstatus=False, include_ostatus=False):
    """
    Get the full description of a character (for friends).
    Returns all description fields in a formatted way.
    
    Args:
        character: The character to describe
        include_rstatus (bool): Whether to include roleplay status
        include_ostatus (bool): Whether to include optional status
    """
    # Start with optional status if included
    if include_ostatus and hasattr(character, 'get_ostatus'):
        ostatus = character.get_ostatus()
        if ostatus:
            return f"{ostatus}\n\n{get_full_description(character)}"
    
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
            
    base_desc = text + " ".join(details)

    # Add roleplay status if included
    if include_rstatus and hasattr(character, 'get_rstatus'):
        rstatus = character.get_rstatus()
        if rstatus:
            # Check if character is drunk
            is_drunk = hasattr(character.db, 'intoxication') and character.db.intoxication > 0
            if is_drunk:
                rstatus = f"{rstatus} (and appears to be drunk)"
            return f"{base_desc}\n\n{character.name} ({rstatus})"

    return base_desc
