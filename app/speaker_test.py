#!/usr/bin/env python3

import os
import sys

from pyannote.audio import Pipeline

from runtime_config import DIARIZATION_MODEL, FFMPEG

MODEL = DIARIZATION_MODEL

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

if len(sys.argv) != 2:
    print("Usage:")
    print("  speaker_test.py <audio-file>")
    sys.exit(1)

audio_file = sys.argv[1]

if not os.path.isfile(audio_file):
    print(f"Error: file not found: {audio_file}")
    sys.exit(1)

print("Loading diarization model...")

pipeline = Pipeline.from_pretrained(MODEL)

print("Analyzing speakers...")

output = pipeline(audio_file)

# Exclusive diarization is better suited
# to subsequent alignment with Whisper timestamps.
diarization = output.exclusive_speaker_diarization

print()
print("Result:")
print()

for turn, speaker in diarization:
    print(
        f"{speaker:12s} "
        f"{turn.start:8.2f} - {turn.end:8.2f}"
    )
