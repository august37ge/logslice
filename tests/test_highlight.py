"""Tests for logslice.highlight."""

import re

from logslice.highlight import (
    ANSI_BOLD_YELLOW,
    ANSI_RESET,
    highlight_in_line,
    highlight_match,
)


def _pat(expr: str, ignore_case: bool = False) -> re.Pattern:
    flags = re.IGNORECASE if ignore_case else 0
    return re.compile(expr, flags)


def test_highlight_match_wraps_single_occurrence():
    result = highlight_match("disk error occurred", _pat("error"))
    assert f"{ANSI_BOLD_YELLOW}error{ANSI_RESET}" in result


def test_highlight_match_wraps_multiple_occurrences():
    result = highlight_match("error and error again", _pat("error"))
    assert result.count(ANSI_BOLD_YELLOW) == 2


def test_highlight_match_no_match_returns_original():
    text = "all systems nominal"
    result = highlight_match(text, _pat("error"))
    assert result == text


def test_highlight_match_custom_tags():
    result = highlight_match("hello world", _pat("world"), open_tag="[", close_tag="]")
    assert "[world]" in result
    assert ANSI_BOLD_YELLOW not in result


def test_highlight_match_preserves_surrounding_text():
    result = highlight_match("prefix error suffix", _pat("error"))
    assert result.startswith("prefix ")
    assert result.endswith(" suffix")


def test_highlight_in_line_none_keyword_unchanged():
    line = "some log line"
    assert highlight_in_line(line, None) == line


def test_highlight_in_line_empty_keyword_unchanged():
    line = "some log line"
    assert highlight_in_line(line, "") == line


def test_highlight_in_line_applies_highlight():
    result = highlight_in_line("connection timeout", "timeout")
    assert ANSI_BOLD_YELLOW in result
    assert "timeout" in result


def test_highlight_in_line_ignore_case():
    result = highlight_in_line("Connection TIMEOUT", "timeout", ignore_case=True)
    assert ANSI_BOLD_YELLOW in result


def test_highlight_in_line_bad_regex_returns_original():
    line = "some line"
    result = highlight_in_line(line, "[bad", ignore_case=False)
    assert result == line
