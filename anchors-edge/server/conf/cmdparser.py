"""
Changing the default command parser to handle no-space emotes and other special cases.
"""

def cmdparser(raw_string, cmdset, caller, match_index=None):
    """
    This function is called by the cmdhandler once it has
    gathered and merged all valid cmdsets valid for this particular parsing.

    raw_string - the unparsed text entered by the caller.
    cmdset - the merged, currently valid cmdset
    caller - the caller triggering this parsing
    match_index - an optional integer index to pick a given match in a
                  list of same-named command matches.

    Returns:
     list of tuples: [(cmdname, args, cmdobj, cmdlen, mratio, raw_cmdname), ...]
            where cmdname is the matching command name and args is
            everything not included in the cmdname. Cmdobj is the actual
            command instance taken from the cmdset, cmdlen is the length
            of the command name, mratio is some quality value to
            separate multiple matches, and raw_cmdname is the original
            form of the command name as entered.
    """
    if not raw_string:
        return []

    # Special case for emote command with no space
    if raw_string.startswith(';'):
        # Find the emote command in the cmdset
        emote_matches = [cmd for cmd in cmdset if cmd.key == 'emote' or ';' in (cmd.aliases or [])]
        if emote_matches:
            emote_cmd = emote_matches[0]
            # Return the emote command with everything after ; as args
            return [('emote', raw_string[1:], emote_cmd, 1, 1.0, 'emote')]

    # Special case for say command with no space
    if raw_string.startswith("'"):
        say_matches = [cmd for cmd in cmdset if cmd.key == 'say' or "'" in (cmd.aliases or [])]
        if say_matches:
            say_cmd = say_matches[0]
            # Return the say command with everything after ' as args
            return [('say', raw_string[1:], say_cmd, 1, 1.0, 'say')]

    # Special case for lsay command with no space
    if raw_string.startswith('"'):
        lsay_matches = [cmd for cmd in cmdset if cmd.key == 'lsay' or '"' in (cmd.aliases or [])]
        if lsay_matches:
            lsay_cmd = lsay_matches[0]
            # Return the lsay command with everything after " as args
            return [('lsay', raw_string[1:], lsay_cmd, 1, 1.0, 'lsay')]

    # Default parsing for all other commands
    raw_string = raw_string.strip()
    
    # Split by spaces for normal command processing
    if not raw_string:
        return []
    
    parts = raw_string.split(None, 1)
    cmdname = parts[0].lower()
    raw_cmdname = parts[0]  # Keep the original case
    args = parts[1] if len(parts) > 1 else ''

    # Build a list of matching commands
    matches = []
    for cmd in cmdset:
        try:
            # Match command names
            if cmd.key == cmdname or \
               cmdname in [alias.lower() for alias in cmd.aliases]:
                matches.append((cmdname, args, cmd, len(cmdname), 1.0, raw_cmdname))
        except Exception:
            continue

    # Handle match_index
    if match_index is not None and matches:
        if 0 <= match_index < len(matches):
            return [matches[match_index]]
        return []

    return matches
