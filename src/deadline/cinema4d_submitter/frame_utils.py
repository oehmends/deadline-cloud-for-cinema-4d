"""Utilities for working with Cinema 4D frame range specifications."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from deadline.client.job_bundle.adaptors import parse_frame_range


@dataclass(frozen=True)
class FrameSpec:
    """Parsed information about a frame specification string."""

    frames: List[int]

    @property
    def count(self) -> int:
        return len(self.frames)

    @property
    def first(self) -> int | None:
        return self.frames[0] if self.frames else None

    @property
    def last(self) -> int | None:
        return self.frames[-1] if self.frames else None


def _split_frame_spec(frame_spec: str) -> Iterable[str]:
    for part in frame_spec.replace(";", ",").split(","):
        stripped = part.strip()
        if stripped:
            yield stripped


def parse_frame_spec(frame_spec: str) -> FrameSpec:
    """Parse a frame specification string into an ordered list of frames.

    The specification can include comma-separated segments. Each segment can be a
    single frame (``42``), a start-stop range (``1-10``), or a start-stop range with a
    step (``1-10:2``).

    If the specification cannot be parsed, an empty frame list is returned.
    """

    frames: list[int] = []
    try:
        for segment in _split_frame_spec(frame_spec):
            frames.extend(parse_frame_range(segment))
    except ValueError:
        return FrameSpec(frames=[])

    # Remove duplicates while preserving order.
    unique_frames: list[int] = []
    seen = set()
    for frame in frames:
        if frame not in seen:
            seen.add(frame)
            unique_frames.append(frame)

    unique_frames.sort()
    return FrameSpec(frames=unique_frames)


def has_multiple_frames(frame_spec: str) -> bool:
    """Return ``True`` if the frame specification contains more than one frame."""

    if not frame_spec.strip():
        return False
    return parse_frame_spec(frame_spec).count > 1
