#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook


from runtime_config import DIARIZATION_MODEL, FFMPEG
from speaker_blocks import merge_blocks, render_blocks

MODEL = DIARIZATION_MODEL

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


def overlap(a_start, a_end, b_start, b_end):
    return max(
        0.0,
        min(a_end, b_end) - max(a_start, b_start),
    )


def normalize_audio(audio_path: Path, target_path: Path):
    """
    Convert input audio to 16 kHz mono WAV.
    For damaged AAC/MP3 frames, FFmpeg attempts to
    continue decoding.
    """

    result = subprocess.run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(audio_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(target_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print()
        print("Error: audio cannot be converted to WAV.")
        print()

        if result.stderr.strip():
            print(result.stderr.strip())

        sys.exit(1)

    if result.stderr.strip():
        print()
        print(
            "WARNING: while decoding the original audio, "
            "an error or warning occurred:"
        )
        print()
        print(result.stderr.strip())
        print()
        print(
            "Processing continues with the successfully decoded "
            "audio."
        )
        print()


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("  speaker_merge.py <audio-file>")
        sys.exit(1)

    audio_path = Path(sys.argv[1]).expanduser().resolve()

    if not audio_path.is_file():
        print(f"Error: audio file not found: {audio_path}")
        sys.exit(1)

    json_path = audio_path.with_suffix(".json")

    if not json_path.is_file():
        print("Error: matching Whisper JSON file not found:")
        print(f"  {json_path}")
        print()
        print("First run, for example:")
        print(f'  jogirat --all "{audio_path}"')
        sys.exit(1)

    output_path = audio_path.with_suffix(".speakers.txt")

    #
    # Whisper JSON
    #

    print("Reading Whisper JSON...")

    with open(json_path, "r", encoding="utf-8") as f:
        whisper = json.load(f)

    segments = whisper.get("segments", [])

    if not segments:
        print("Error: JSON contains no Whisper segments.")
        sys.exit(1)

    #
    # Pyannote
    #

    print("Loading diarization model...")

    pipeline = Pipeline.from_pretrained(MODEL)

    #
    # Audio normalization + diarization
    #

    print("Preparing audio for diarization...")

    with tempfile.TemporaryDirectory(
        prefix="legaltranscriber-speaker-"
    ) as tmp_dir:

        normalized_audio = Path(tmp_dir) / "input.wav"

        normalize_audio(
            audio_path=audio_path,
            target_path=normalized_audio,
        )

        print("Analyzing speakers...")

        with ProgressHook() as hook:
            output = pipeline(
                str(normalized_audio),
                hook=hook,
            )

    #
    # Exclusive diarization
    #

    diarization = output.exclusive_speaker_diarization

    speaker_turns = []

    for turn, speaker in diarization:
        speaker_turns.append(
            {
                "start": float(turn.start),
                "end": float(turn.end),
                "speaker": speaker,
            }
        )

    if not speaker_turns:
        print("Error: diarization found no speaker turns.")
        sys.exit(1)

    #
    # Align Whisper segments with speaker turns
    #

    print("Aligning Whisper and speaker timestamps...")

    assigned = []

    for segment in segments:

        start = float(segment["start"])
        end = float(segment["end"])
        text = segment.get("text", "").strip()

        if not text:
            continue

        best_speaker = "SPEAKER_UNKNOWN"
        best_overlap = 0.0

        for turn in speaker_turns:

            ov = overlap(
                start,
                end,
                turn["start"],
                turn["end"],
            )

            if ov > best_overlap:
                best_overlap = ov
                best_speaker = turn["speaker"]

        assigned.append(
            {
                "speaker": best_speaker,
                "start": start,
                "end": end,
                "text": text,
            }
        )

    #
    # Merge consecutive segments from the same speaker
    #

    blocks = merge_blocks(assigned)
    output_path.write_text(render_blocks(blocks), encoding="utf-8")

    print()
    print("Done:")
    print(f"  {output_path}")


if __name__ == "__main__":
    main()
