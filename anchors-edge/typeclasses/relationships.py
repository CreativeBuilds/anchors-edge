"""
Relationship and knowledge tracking for characters.
"""

from enum import IntEnum

class KnowledgeLevel(IntEnum):
    """Enum for tracking how well one character knows another."""
    STRANGER = 0      # Basic race/height info only
    ACQUAINTANCE = 1  # Basic physical description + name if introduced
    FRIEND = 2        # Full description + name + messaging
    
def get_brief_description(character):
    """
    Get a brief description of a character (for strangers).
    Returns height + race description.
    """
    race = character.db.race
    subrace = character.db.subrace if character.db.subrace else ""
    height = character.db.height if hasattr(character.db, 'height') else 0
    
    # Convert height to feet/inches
    feet = height // 12
    inches = height % 12
    
    # Height descriptors
    if height:
        if height < 60:  # Under 5 feet
            height_desc = "short"
        elif height > 72:  # Over 6 feet
            height_desc = "tall"
        else:
            height_desc = "average height"
    else:
        height_desc = ""
    
    # Combine race and subrace
    if subrace:
        race_desc = f"{subrace} {race}"
    else:
        race_desc = race
        
    # Format the description
    if height_desc:
        return f"A {height_desc} {race_desc.lower()}"
    else:
        return f"A {race_desc}"
        
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
    
    # Combine features
    if notable_features:
        features_text = " and ".join(notable_features)
        return f"A {character.db.race.lower()} with {features_text} can be seen."
    else:
        return get_brief_description(character)
        
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
