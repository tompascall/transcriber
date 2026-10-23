"""Saved speaker blocks can regenerate a transcript without model inference."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from speaker_blocks import load_blocks, merge_blocks, render_blocks, save_blocks


class SpeakerJsonTest(unittest.TestCase):
    def test_roundtrip_preserves_precision_text_and_rendering(self):
        segments = [
            dict(speaker="SPEAKER_00", start=12.375, end=14.5, text="Első mondat."),
            dict(speaker="SPEAKER_00", start=14.5, end=17.625, text="Második."),
            dict(speaker="SPEAKER_01", start=65.125, end=70.875, text="Válasz."),
        ]
        blocks = merge_blocks(segments)
        with tempfile.TemporaryDirectory(prefix="speaker json ") as temp:
            source = Path(temp) / "recording.speakers.json"
            save_blocks(source, blocks)
            original = source.read_bytes()
            self.assertEqual(load_blocks(source), blocks)
            self.assertIn("Első", source.read_text())
            result = subprocess.run([str(ROOT / "bin/jogirender"), str(source)],
                                    env=dict(os.environ, LT_PYTHON=sys.executable),
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(source.with_suffix(".txt").read_text(), render_blocks(blocks))
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(load_blocks(source)[0]["start"], 12.375)
            self.assertEqual(load_blocks(source)[0]["end"], 17.625)
            output = Path(temp) / "separate.txt"
            subprocess.run([str(ROOT / "bin/jogirender"), str(source), "--output", str(output)],
                           env=dict(os.environ, LT_PYTHON=sys.executable), check=True,
                           capture_output=True)
            self.assertEqual(output.read_text(), render_blocks(blocks))

    def test_invalid_input_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "recording.speakers.json"
            source.write_text(json.dumps({"version": 99, "blocks": []}))
            output = source.with_suffix(".txt")
            output.write_text("Existing edited transcript")
            result = subprocess.run([sys.executable, str(ROOT / "app/speaker_blocks.py"), str(source)],
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(), "Existing edited transcript")


if __name__ == "__main__":
    unittest.main()
