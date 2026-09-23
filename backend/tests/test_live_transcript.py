import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.live_transcript import LiveTranscript, speech_end_sample


def committed_words(transcript: LiveTranscript) -> list[str]:
    return transcript._committed


def test_first_ingest_holds_back_the_newest_words_and_renders_the_rest():
    transcript = LiveTranscript(hold=2)

    assert transcript.ingest("alpha bravo charlie delta") == "alpha bravo"
    assert committed_words(transcript) == ["alpha", "bravo"]
    assert transcript.render() == "alpha bravo"


def test_first_ingest_within_the_hold_renders_nothing():
    transcript = LiveTranscript(hold=6)

    assert transcript.ingest("alpha bravo") is None
    assert transcript.render() == ""


def test_agreeing_decode_advances_display_while_equal_or_shorter_decodes_do_nothing():
    transcript = LiveTranscript(hold=2)
    assert transcript.ingest("alpha bravo charlie delta") == "alpha bravo"

    assert transcript.ingest("alpha bravo charlie delta echo") is None
    assert transcript.render() == "alpha bravo"

    assert transcript.ingest("alpha bravo charlie delta echo foxtrot") == "alpha bravo charlie"

    assert transcript.ingest("alpha bravo charlie") is None
    assert transcript.ingest("alpha bravo") is None
    assert transcript.render() == "alpha bravo charlie"


def test_held_word_revision_never_reaches_the_display_and_later_commits_recover():
    transcript = LiveTranscript(hold=2)
    transcript.ingest("alpha bravo charlie delta")

    assert transcript.ingest("alpha bravo charlieX delta echo") is None
    assert transcript.render() == "alpha bravo"

    assert transcript.ingest("alpha bravo charlie delta echo foxtrot") is None
    assert transcript.render() == "alpha bravo"

    display = transcript.ingest("alpha bravo charlie delta echo foxtrot golf")

    assert display == "alpha bravo charlie delta"
    assert "charlieX" not in display
    assert "charlieX" not in transcript.render()


def test_committed_revision_with_a_locatable_end_appends_without_rewriting():
    transcript = LiveTranscript(hold=2)
    transcript.ingest("alpha bravo charlie delta echo foxtrot golf")
    assert transcript.render() == "alpha bravo charlie delta echo"

    display = transcript.ingest("alpha bravo charlieX delta echo foxtrot golf hotel india")

    assert display == "alpha bravo charlie delta echo foxtrot golf"
    assert "charlieX" not in display


def test_revision_of_the_committed_end_holds_the_render():
    transcript = LiveTranscript(hold=2)
    transcript.ingest("alpha bravo charlie delta echo")

    assert transcript.ingest("alpha bravo charlieX delta echo foxtrot") is None
    assert transcript.render() == "alpha bravo charlie"


def test_head_loss_grows_from_the_aligned_end_without_duplicating():
    transcript = LiveTranscript(hold=2)
    words = [f"word{n:02d}" for n in range(1, 9)]
    transcript.ingest(" ".join(words))
    assert transcript.render() == " ".join(words[:6])

    display = transcript.ingest(" ".join(words[4:] + ["new09"]))
    assert display == " ".join(words[:7])
    assert display.count("word05") == 1
    assert display.count("word06") == 1

    assert transcript.ingest(" ".join(words + ["new09", "new10"])) is None
    assert transcript.ingest(" ".join(words + ["new09", "new10", "new11"])) == " ".join(words[:8])


def test_empty_and_duplicate_decodes_are_no_ops():
    transcript = LiveTranscript(hold=2)
    assert transcript.ingest("alpha bravo charlie") == "alpha"

    assert transcript.ingest("alpha bravo charlie") is None
    assert transcript.ingest("") is None
    assert transcript.ingest("   ") is None
    assert transcript.render() == "alpha"


def test_displayed_words_never_shrink_or_change_over_a_scripted_sequence():
    transcript = LiveTranscript(hold=3)
    decodes = [
        "alpha bravo charlie delta echo foxtrot",
        "alpha bravo charlie delta echo foxtrot golf",
        "alpha bravo charlieX delta echo foxtrot golf hotel",
        "alpha bravo charlieX delta echo foxtrot golf hotel india",
        "alpha bravo charlie delta echo foxtrot golf hotel india juliet",
    ]

    previous_display = ""
    for decode in decodes:
        transcript.ingest(decode)
        display = transcript.render()
        if previous_display:
            assert display == previous_display or display.startswith(previous_display + " "), (
                f"display changed:\n  before: {previous_display}\n  after:  {display}"
            )
        previous_display = display

    assert previous_display == "alpha bravo charlie delta"


def test_speech_end_sample_finds_the_end_of_speech():
    ones = np.ones(16000, dtype=np.float32)
    zeros = np.zeros(16000, dtype=np.float32)

    assert speech_end_sample(ones, 16000) == 16000
    assert speech_end_sample(zeros, 16000) == 0
    assert speech_end_sample(np.concatenate([ones, zeros]), 16000) == 19200
    assert speech_end_sample(np.zeros(0, dtype=np.float32), 16000) == 0


def test_speech_end_sample_ignores_audio_under_the_floor_and_peak_ratio():
    quiet = np.full(16000, 5e-4, dtype=np.float32)
    assert speech_end_sample(quiet, 16000) == 0

    loud = np.ones(1600, dtype=np.float32)
    faint = np.full(16000 - 1600, 0.005, dtype=np.float32)
    assert speech_end_sample(np.concatenate([loud, faint]), 16000) == 4800
