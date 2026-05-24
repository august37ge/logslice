"""Annotate log entries with extra metadata tags."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List, Optional

from logslice.parser import LogEntry


@dataclass
class AnnotatedEntry:
    """A log entry with an additional list of annotation tags."""

    entry: LogEntry
    tags: List[str] = field(default_factory=list)

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)


# Annotator type: receives an entry and returns a tag string or None.
Annotator = Callable[[LogEntry], Optional[str]]


def severity_annotator(entry: LogEntry) -> Optional[str]:
    """Tag entries whose severity is ERROR or CRITICAL."""
    if entry.severity.upper() in ("ERROR", "CRITICAL"):
        return "high-severity"
    return None


def keyword_annotator(*keywords: str) -> Annotator:
    """Return an annotator that tags entries containing any of the given keywords."""
    lower_kws = [kw.lower() for kw in keywords]

    def _annotate(entry: LogEntry) -> Optional[str]:
        msg = entry.message.lower()
        for kw in lower_kws:
            if kw in msg:
                return f"keyword:{kw}"
        return None

    return _annotate


def source_annotator(source_tag_map: dict[str, str]) -> Annotator:
    """Return an annotator that maps source names to custom tags."""

    def _annotate(entry: LogEntry) -> Optional[str]:
        return source_tag_map.get(entry.source)

    return _annotate


def annotate_entries(
    entries: Iterable[LogEntry],
    annotators: List[Annotator],
) -> Iterator[AnnotatedEntry]:
    """Apply all annotators to each entry and yield AnnotatedEntry objects."""
    for entry in entries:
        annotated = AnnotatedEntry(entry=entry)
        for annotator in annotators:
            tag = annotator(entry)
            if tag is not None:
                annotated.add_tag(tag)
        yield annotated


def filter_by_tag(
    annotated: Iterable[AnnotatedEntry],
    tag: str,
) -> Iterator[AnnotatedEntry]:
    """Yield only annotated entries that carry the given tag."""
    for ae in annotated:
        if tag in ae.tags:
            yield ae
