# modules/variable_flags.py

import re

def parse_flags(var_text: str):
    """
    Extract variable name and flags from a token like {{venue[CAPS|CUSTOM]}}.
    Returns (var_name, set_of_flags)
    """
    m = re.match(r"([a-zA-Z0-9_]+)(?:\[([A-Z|]+)\])?", var_text)
    if not m:
        return var_text, set()
    var_name = m.group(1)
    flags = set(m.group(2).split("|")) if m.group(2) else set()
    return var_name, flags

def apply_flags(text: str, flags: set, custom_map: dict = None):
    """
    Apply flags to the text:
        - 'CAPS': uppercase
        - 'CUSTOM': replace [[custom]] with the provided custom_map value
    """
    if text is None:
        text = ""
    if "CUSTOM" in flags and custom_map:
        for key, value in custom_map.items():
            text = text.replace(f"[[{key}]]", value)
    if "CAPS" in flags:
        text = text.upper()
    return text
