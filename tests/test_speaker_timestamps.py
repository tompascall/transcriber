"""Speaker timestamps and correction preservation without model inference."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from speaker_blocks import format_timestamp, merge_blocks, render_blocks
import text_correct


class SpeakerTimestampsTest(unittest.TestCase):
    def test_seek_times_round_down_and_handle_hours(self):
        for seconds, expected in [(0, "00:00:00"), (59.99, "00:00:59"),
                                  (60, "00:01:00"), (3661.8, "01:01:01"),
                                  (360000, "100:00:00")]:
            with self.subTest(seconds=seconds):
                self.assertEqual(format_timestamp(seconds), expected)

    def test_merged_blocks_keep_first_start_and_returning_speakers_get_new_time(self):
        segments = [
            dict(speaker="SPEAKER_00", start=12.8, end=15, text="First."),
            dict(speaker="SPEAKER_00", start=15, end=20, text="Second."),
            dict(speaker="SPEAKER_01", start=65, end=70, text="Reply."),
            dict(speaker="SPEAKER_00", start=3661.5, end=3665, text="Again."),
        ]
        blocks = merge_blocks(segments)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(render_blocks(blocks),
                         "SPEAKER_00 [00:00:12]:\nFirst. Second.\n\n"
                         "SPEAKER_01 [00:01:05]:\nReply.\n\n"
                         "SPEAKER_00 [01:01:01]:\nAgain.\n\n")
        self.assertEqual(segments[0]["text"], "First.")

    def test_correction_preserves_new_and_legacy_headers(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "sample.speakers.txt"
            original = "SPEAKER_00 [01:02:03]:\njótárási\n\nSPEAKER_UNKNOWN:\njótárási\n"
            source.write_text(original)
            with patch.object(sys, "argv", ["jogijavit", str(source)]), \
                 patch.object(text_correct, "load_custom_replacements", return_value={"jótárási": "jótállási"}), \
                 patch.object(text_correct, "hunspell_check", return_value={}) as spell, \
                 contextlib.redirect_stdout(io.StringIO()):
                text_correct.main()
            spell.assert_called_once_with([])
            self.assertEqual(source.read_text(), original)
            self.assertEqual(source.with_suffix(".jav.txt").read_text(),
                             original.replace("jótárási", "jótállási"))


if __name__ == "__main__":
    unittest.main()
