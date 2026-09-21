"""Stable live transcription text: a frozen committed prefix plus a short revisable tail.

The live thread re-decodes the whole recording each pass, and the model does not
guarantee that two decodes of the same speech agree. This module keeps the words the
user has already read stable and leaves only the newest words revisable.
"""

from difflib import SequenceMatcher
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

HOLD_WORDS = 6
FRAME_SECONDS = 0.02
SPEECH_MARGIN_SECONDS = 0.2
FLOOR_RMS = 1e-3
PEAK_RATIO = 0.01


def speech_end_sample(
    audio: "NDArray[np.float32]",
    sample_rate: int,
    frame_seconds: float = FRAME_SECONDS,
    margin_seconds: float = SPEECH_MARGIN_SECONDS,
    floor_rms: float = FLOOR_RMS,
    peak_ratio: float = PEAK_RATIO,
) -> int:
    """Index after the last speech frame plus a margin. 0 when no speech is present."""
    if len(audio) == 0 or sample_rate <= 0:
        return 0

    frame_length = max(1, int(sample_rate * frame_seconds))
    frame_count = len(audio) // frame_length
    if frame_count == 0:
        return 0

    frames = np.asarray(audio[: frame_count * frame_length]).reshape(frame_count, frame_length)
    rms = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=1))
    peak = float(rms.max())
    if peak <= 0.0:
        return 0

    speech_frames = np.nonzero(rms > max(floor_rms, peak_ratio * peak))[0]
    if speech_frames.size == 0:
        return 0

    speech_end = int(speech_frames[-1] + 1) * frame_length + int(margin_seconds * sample_rate)
    return min(len(audio), speech_end)


class LiveTranscript:
    """One recording session's live display.

    ``committed`` words have been read by the user and never change. ``tail`` covers the
    newest words and is the only region a later decode may revise.
    """

    def __init__(self, hold: int = HOLD_WORDS) -> None:
        self._hold = max(0, hold)
        self._committed: list[str] = []
        self._tail: list[str] = []

    def render(self) -> str:
        return " ".join(self._committed + self._tail)

    def ingest(self, text: str) -> str | None:
        """Merge one decode into the display. Returns the full text when it changed."""
        new = text.split()
        if not new:
            return None

        if not self._committed and not self._tail:
            cut = max(0, len(new) - self._hold)
            self._committed, self._tail = new[:cut], new[cut:]
            return self.render()

        display = self._committed + self._tail
        common = _common_prefix_length(display, new)
        if common >= len(self._committed):
            commit_end = max(len(self._committed), common - self._hold)
            new_committed = display[:commit_end]
            new_tail = new[commit_end:]
        else:
            anchor = _aligned_committed_end(self._committed, new)
            if anchor is None:
                return None
            new_committed = self._committed
            new_tail = new[anchor:]

        if new_committed == self._committed and new_tail == self._tail:
            return None

        self._committed = new_committed
        self._tail = new_tail
        return self.render()


def _common_prefix_length(left: list[str], right: list[str]) -> int:
    count = 0
    for a, b in zip(left, right):
        if a != b:
            break
        count += 1
    return count


def _aligned_committed_end(committed: list[str], decoded: list[str]) -> int | None:
    """Index in ``decoded`` just past its match of the committed region's end, or None
    when the decode dropped it."""
    matcher = SequenceMatcher(None, committed, decoded, autojunk=False)
    for block in reversed(matcher.get_matching_blocks()):
        if block.size and block.a + block.size == len(committed):
            return block.b + block.size
    return None
