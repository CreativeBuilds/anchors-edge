"""
Utility functions for text formatting and manipulation.
"""

def ensure_sentence_period(text, no_period=False):
    """
    Ensures the text ends with a period if it doesn't end with ., !, or ?
    Args:
        text (str): The text to check
        no_period (bool): If True, don't add a period at the end
    Returns:
        str: The text ending with proper punctuation (unless no_period is True)
    """
    if not text:
        return text
    text = text.strip()
    if not no_period and not text.endswith(('.', '!', '?')):
        text = text + '.'
    return text


def format_sentence(text: str, capitalize: bool = True, no_period: bool = False) -> str:
    """
    Formats text as a proper sentence with capitalization and period.
    Args:
        text (str): The text to format
        capitalize (bool): Whether to capitalize the first letter
        no_period (bool): If True, don't add a period at the end
    Returns:
        str: The formatted text
    """
    if not text:
        return text
    text = text.strip()
    # Add period if needed
    text = ensure_sentence_period(text, no_period)
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