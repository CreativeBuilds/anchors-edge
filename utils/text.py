def ensure_sentence_period(text):
    """
    Ensures a sentence ends with a period. If not, adds one.
    
    Args:
        text (str): The text to check
        
    Returns:
        str: Text ending with a period
    """
    if not text:
        return ""
    text = text.rstrip()
    if text and text[-1] not in ".!?":
        text += "."
    return text 