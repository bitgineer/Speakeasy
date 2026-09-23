"""Live transcription text that only ever grows; the final decode owns corrections."""

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

    ``committed`` words have been rendered and never change. ``pending`` words are held
    back until a decode moves past them. A decode that revises a committed word is
    ignored: shown words stay, and its words beyond the committed region are appended.
    """

    def __init__(self, hold: int = HOLD_WORDS) -> None:
        self._hold = max(0, hold)
        self._committed: list[str] = []
        self._pending: list[str] = []

    def render(self) -> str:
        return " ".join(self._committed)

    def ingest(self, text: str) -> str | None:
        """Merge one decode into the display.

        Returns the rendered text only when the committed prefix grew this call.
        """
        new = text.split()
        if not new:
            return None

        if not self._committed and not self._pending:
            cut = max(0, len(new) - self._hold)
            self._committed, self._pending = new[:cut], new[cut:]
            return self.render() if self._committed else None

        display = self._committed + self._pending
        common = _common_prefix_length(display, new)
        if common >= len(self._committed):
            commit_end = max(len(self._committed), common - self._hold)
            new_committed = display[:commit_end]
            new_pending = new[commit_end:]
        else:
            anchor = _aligned_committed_end(self._committed, new)
            if anchor is None:
                return None
            continuation = new[anchor:]
            held = min(self._hold, len(continuation))
            new_committed = self._committed + continuation[: len(continuation) - held]
            new_pending = continuation[len(continuation) - held :]

        grew = new_committed != self._committed
        self._committed = new_committed
        self._pending = new_pending
        return self.render() if grew else None


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
