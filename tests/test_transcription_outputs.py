"""Check output validation without loading models or using the GPU."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class TranscriptionOutputsTest(unittest.TestCase):
    def run_wrapper(self, mode, generated, coordinator=False):
        with tempfile.TemporaryDirectory(prefix="transcriber outputs ") as temp:
            directory = Path(temp)
            audio = directory / "recording.wav"
            audio.write_bytes(b"stub audio")
            for extension in ("txt", "srt", "json"):
                audio.with_suffix("." + extension).write_text("old " + extension)
            stub = directory / "stub.py"
            stub.write_text(
                "#!/usr/bin/env python3\n"
                "import os, sys\nfrom pathlib import Path\n"
                "if '--output-dir' in sys.argv:\n"
                "    out = Path(sys.argv[sys.argv.index('--output-dir') + 1])\n"
                "    for ext in os.environ['TEST_FORMATS'].split():\n"
                "        (out / ('input.' + ext)).write_text('new ' + ext)\n"
            )
            stub.chmod(0o755)
            env = dict(os.environ, LT_FFMPEG=str(stub), LT_WHISPER=str(stub),
                       TEST_FORMATS=" ".join(generated))
            # The coordinator must stop before invoking diarization.
            env["LT_PYTHON"] = str(directory / "missing-python")
            args = [str(ROOT / "bin" / ("jogi" if coordinator else "jogirat"))]
            if not coordinator and mode != "txt":
                args.append("--" + mode)
            result = subprocess.run(args + [str(audio)], env=env, capture_output=True, text=True)
            contents = {ext: audio.with_suffix("." + ext).read_text()
                        for ext in ("txt", "srt", "json")}
            return result, contents

    def test_missing_outputs_preserve_all_previous_results(self):
        modes = {"txt": {"txt"}, "srt": {"txt", "srt"},
                 "json": {"txt", "json"}, "all": {"txt", "srt", "json"}}
        for mode, required in modes.items():
            for missing in required:
                with self.subTest(mode=mode, missing=missing):
                    result, contents = self.run_wrapper(mode, required - {missing})
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("did not create", result.stderr)
                    self.assertEqual(contents, {ext: "old " + ext for ext in contents})

    def test_success_replaces_only_requested_outputs(self):
        for mode, requested in [("txt", {"txt"}), ("srt", {"txt", "srt"}),
                                ("json", {"txt", "json"}), ("all", {"txt", "srt", "json"})]:
            with self.subTest(mode=mode):
                result, contents = self.run_wrapper(mode, requested)
                self.assertEqual(result.returncode, 0, result.stderr)
                for ext, content in contents.items():
                    self.assertEqual(content, ("new " if ext in requested else "old ") + ext)

    def test_coordinator_stops_before_using_stale_json(self):
        result, contents = self.run_wrapper("all", {"txt", "srt"}, coordinator=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requested json output", result.stderr)
        self.assertNotIn("[2/3]", result.stdout)
        self.assertEqual(contents["json"], "old json")


if __name__ == "__main__":
    unittest.main()
