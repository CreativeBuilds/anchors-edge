"""
Utility functions for text formatting and manipulation.
"""

def ensure_sentence_period(text):
    """
    Ensures the text ends with a period if it doesn't end with ., !, or ?
    Args:
        text (str): The text to check
    Returns:
        str: The text ending with proper punctuation
    """
    if not text:
        return text
    text = text.strip()
    if not text.endswith(('.', '!', '?')):
        text = text + '.'
    return text


def format_sentence(text: str, capitalize: bool = True) -> str:
    """
    Formats text as a proper sentence with capitalization and period.
    Args:
        text (str): The text to format
        capitalize (bool): Whether to capitalize the first letter
    Returns:
        str: The formatted text
    """
    if not text:
        return text
    text = text.strip()
    # Add period if needed
    text = ensure_sentence_period(text)
    # Capitalize first letter if requested
    if capitalize and text:
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    return text 

def capitalize_first_letter(text: str) -> str:
    """
    Capitalizes the first letter of the text.
    Args:
        text (str): The text to capitalize
    Returns:
        str: The capitalized text
    """
    return text[0].upper() + text[1:] if len(text) > 1 else text.upper()