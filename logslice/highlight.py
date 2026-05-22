"""ANSI highlight helpers for search matches within log messages."""

import re
from typing import Optional, Pattern

ANSI_BOLD_YELLOW = "\033[1;33m"
ANSI_RESET = "\033[0m"


def highlight_match(
    text: str,
    pattern: Pattern,
    open_tag: str = ANSI_BOLD_YELLOW,
    close_tag: str = ANSI_RESET,
) -> str:
    """Wrap every match of *pattern* in *text* with ANSI colour tags.

    Args:
        text:      The source string to scan.
        pattern:   A compiled regex pattern.
        open_tag:  Escape sequence inserted before each match.
        close_tag: Escape sequence inserted after each match.

    Returns:
        A new string with all matches wrapped.  If there are no matches
        the original string is returned unchanged.
    """
    if not pattern.search(text):
        return text
    return pattern.sub(lambda m: f"{open_tag}{m.group()}{close_tag}", text)


def highlight_in_line(
    line: str,
    keyword: Optional[str],
    ignore_case: bool = False,
) -> str:
    """Convenience wrapper that compiles *keyword* and highlights *line*.

    Returns *line* unmodified when *keyword* is None or empty.
    """
    if not keyword:
        return line
    flags = re.IGNORECASE if ignore_case else 0
    try:
        pattern = re.compile(keyword, flags)
    except re.error:
        return line
    return highlight_match(line, pattern)
