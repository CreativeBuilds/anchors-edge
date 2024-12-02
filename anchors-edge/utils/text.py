"""
Text formatting utilities.
"""

def format_description(text):
    """
    Format description text by:
    1. Ensuring first letter is capitalized
    2. Adding period at end if missing
    3. Preserving existing punctuation
    
    Args:
        text (str): The text to format
        
    Returns:
        str: The formatted text
    """
    if not text:
        return text
        
    # Capitalize first letter
    text = text[0].upper() + text[1:] if len(text) > 1 else text.capitalize()
    
    # Add period if no ending punctuation
    if not text[-1] in '.!?':
        text += '.'
        
    return text 