import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.live_transcript import LiveTranscript, speech_end_sample


def committed_words(transcript: LiveTranscript) -> list[str]:
    return transcript._committed


def test_first_ingest_holds_back_the_tail_and_renders_everything():
    transcript = LiveTranscript(hold=2)

    assert transcript.ingest("alpha bravo charlie delta") == "alpha bravo charlie delta"
    assert committed_words(transcript) == ["alpha", "bravo"]
    assert transcript.render() == "alpha bravo charlie delta"


def test_append_passes_advance_committed_without_changing_it():
    transcript = LiveTranscript(hold=2)
    transcript.ingest("alpha bravo charlie delta")

    display = transcript.ingest("alpha bravo charlie delta echo")
    assert display == "alpha bravo charlie delta echo"
    assert committed_words(transcript) == ["alpha", "bravo"]

    transcript.ingest("alpha bravo charlie delta echo foxtrot")

    assert committed_words(transcript) == ["alpha", "bravo", "charlie"]
    assert transcript.render() == "alpha bravo charlie delta echo foxtrot"


def test_tail_revision_is_accepted():
    transcript = LiveTranscript(hold=2)
    transcript.ingest("alpha bravo charlie delta")

    assert transcript.ingest("alpha bravo charlie echo") == "alpha bravo charlie echo"


def test_committed_revision_is_rejected():
    transcript = LiveTranscript(hold=2)
    transcript.ingest("alpha bravo charlie delta echo")

    assert transcript.ingest("alpha bravo charlieX delta echo") is None
    assert transcript.render() == "alpha bravo charlie delta echo"


def test_mid_committed_revision_keeps_committed_and_appends_new_words():
    transcript = LiveTranscript(hold=6)
    words = [f"word{n:02d}" for n in range(1, 21)]
    transcript.ingest(" ".join(words))
    assert len(committed_words(transcript)) == 14

    revised = words[:4] + ["revised05"] + words[5:] + ["new21"]
    display = transcript.ingest(" ".join(revised))

    assert display is not None
    assert display.startswith(" ".join(words[:14]))
    assert "revised05" not in display
    assert display.count("new21") == 1
    assert display.endswith("word20 new21")


def test_decoded_head_loss_holds_display_then_recovery_appends_once():
    transcript = LiveTranscript(hold=6)
    words = [f"word{n:02d}" for n in range(1, 21)]
    transcript.ingest(" ".join(words))

    assert transcript.ingest(" ".join(words[12:])) is None
    assert transcript.render() == " ".join(words)

    display = transcript.ingest(" ".join(words + ["new21"]))
    assert display == " ".join(words + ["new21"])
    assert display.count("new21") == 1


def test_duplicate_and_empty_decodes_are_no_ops():
    transcript = LiveTranscript(hold=2)
    transcript.ingest("alpha bravo charlie")

    assert transcript.ingest("alpha bravo charlie") is None
    assert transcript.ingest("   ") is None
    assert transcript.render() == "alpha bravo charlie"


def test_committed_never_shrinks_over_a_scripted_sequence():
    transcript = LiveTranscript(hold=3)
    decodes = [
        "alpha bravo charlie delta echo foxtrot",
        "alpha bravo charlie delta echo foxtrot golf",
        "alpha bravo charlieX delta echo foxtrot golf hotel",
        "alpha bravo charlieX delta echo foxtrot golf hotel india",
    ]

    previous_committed: list[str] = []
    for decode in decodes:
        transcript.ingest(decode)
        committed = committed_words(transcript)
        assert committed[: len(previous_committed)] == previous_committed
        previous_committed = committed


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
