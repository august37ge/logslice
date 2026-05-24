"""transform.py — Entry transformation pipeline for logslice.

Provides a composable way to apply a sequence of transformations
(normalize, redact, truncate, annotate, etc.) to a stream of LogEntry
objects without having to wire each step manually in calling code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List, Optional

from logslice.parser import LogEntry

# A single transformation: takes a LogEntry and returns a (possibly
# modified) LogEntry, or None to drop the entry from the stream.
TransformFn = Callable[[LogEntry], Optional[LogEntry]]


@dataclass
class TransformPipeline:
    """An ordered list of transformation functions applied left-to-right.

    If any transform returns ``None`` the entry is dropped and subsequent
    transforms are not called for that entry.
    """

    steps: List[TransformFn] = field(default_factory=list)

    def add(self, fn: TransformFn) -> "TransformPipeline":
        """Append *fn* to the pipeline and return *self* for chaining."""
        self.steps.append(fn)
        return self

    def apply(self, entry: LogEntry) -> Optional[LogEntry]:
        """Run *entry* through every step; return the final entry or None."""
        current: Optional[LogEntry] = entry
        for step in self.steps:
            if current is None:
                return None
            current = step(current)
        return current

    def run(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Yield transformed entries, skipping any that a step drops."""
        for entry in entries:
            result = self.apply(entry)
            if result is not None:
                yield result


def build_transform_pipeline(
    *,
    normalize: bool = False,
    redact: bool = False,
    truncate: bool = False,
    max_length: int = 200,
    extra_steps: Optional[List[TransformFn]] = None,
) -> TransformPipeline:
    """Construct a :class:`TransformPipeline` from high-level flags.

    Parameters
    ----------
    normalize:
        Apply :func:`logslice.normalize.normalize_entry` to each entry.
    redact:
        Apply default redaction patterns via
        :func:`logslice.redact.redact_entry`.
    truncate:
        Truncate long messages via :func:`logslice.truncate.truncate_entry`.
    max_length:
        Character limit passed to ``truncate_entry`` when *truncate* is True.
    extra_steps:
        Additional :data:`TransformFn` callables appended after the built-in
        steps.
    """
    pipeline = TransformPipeline()

    if normalize:
        from logslice.normalize import normalize_entry  # local import avoids circularity
        pipeline.add(normalize_entry)

    if redact:
        from logslice.redact import RedactConfig, redact_entry
        cfg = RedactConfig()  # uses built-in patterns
        pipeline.add(lambda e, _cfg=cfg: redact_entry(e, _cfg))

    if truncate:
        from logslice.truncate import truncate_entry
        pipeline.add(lambda e, _ml=max_length: truncate_entry(e, _ml))

    for step in (extra_steps or []):
        pipeline.add(step)

    return pipeline


def transform_entries(
    entries: Iterable[LogEntry],
    pipeline: TransformPipeline,
) -> Iterator[LogEntry]:
    """Convenience wrapper — equivalent to ``pipeline.run(entries)``."""
    return pipeline.run(entries)
