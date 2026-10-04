# Development guide

## Prerequisites and environment setup

Follow [Installation](../INSTALL.md) for Apple Silicon macOS 26+ setup. The runtime
uses native arm64 Python 3.12, FFmpeg, and Hunspell. The setup command creates:

```text
transcriber/
├── .venv/                 # ignored Python environment
├── models/                # ignored fixed-revision model snapshots
├── dictionaries/          # ignored Hungarian Hunspell files
├── app/                   # Python processing scripts
├── bin/                   # command wrappers
├── config/                # custom ASR replacements
├── scripts/               # setup and asset download tools
├── requirements.in        # direct runtime dependencies
├── requirements.txt       # pinned transitive runtime dependencies
├── assets.lock.json       # model revisions and dictionary checksums
└── .env                   # ignored local overrides
```

The runtime lock was derived from the previously working Python 3.12 macOS arm64
installation, excluding packages only needed by the experimental LLM layer.
`requirements.txt` pins versions throughout the runtime dependency closure.
`assets.lock.json` fixes Hugging Face model revisions and the LibreOffice
Hungarian dictionary revision and SHA-256 checksums. Python package artifact
hashes are not currently locked. Homebrew tools and Python patch versions remain
outside this lock.

## Runtime configuration

Defaults resolve relative to the checkout, independently of the working directory.
No external LegalTranscriber installation is required.

```bash
cp .env.example .env
```

Copy the example only when creating or deliberately replacing configuration.
`.env` is ignored by Git. Set `LT_RUNTIME_DIR` to a directory containing `.venv/`,
`models/`, and `dictionaries/`, or override individual paths. Environment variables
take precedence over `.env`; empty values use defaults. Values are literal,
optionally quoted: use absolute paths without `~`, shell variable expansion,
`export`, or inline comments. The file is parsed as data, never executed.

Available settings are listed in `.env.example`. `LT_FFMPEG` and `LT_HUNSPELL`
accept executable paths or names resolved through `PATH`. `LT_HUNSPELL_DICT` is
the dictionary prefix without `.aff` or `.dic`. `LT_CUSTOM_DICT` defaults to
`config/custom_replacements.tsv` in the checkout.

## Running the checkout

```bash
./bin/jogi /path/to/audio.m4a
```

The wrappers run the checkout's Python scripts using `.venv/`. Transcription uses
`models/whisper-large-v3-mlx`; diarization uses
`models/pyannote-speaker-diarization-community-1`. Both run offline.

## Dependency maintenance

Change direct requirements in `requirements.in`, resolve their full dependency
closure for Python 3.12 on macOS arm64, and update `requirements.txt` together.
Keep experimental packages outside the runtime lock. Verify a clean environment
with `./scripts/setup.sh --skip-assets`, `./.venv/bin/python -m pip check`, and a
representative full audio run before accepting new pins.

Update model revisions or dictionary URLs and checksums in `assets.lock.json`
deliberately; setup downloads those fixed revisions rather than the latest branch.
Do not commit the virtual environment or downloaded weights.

## Architecture

The coordinator runs Whisper transcription, speaker diarization, then conservative
text correction. FFmpeg normalizes audio to 16 kHz mono WAV. Whisper writes TXT,
SRT, and JSON. The merge script assigns each Whisper segment to the speaker with
the greatest temporal overlap and merges consecutive same-speaker segments.
Each speaker block is labeled with the first segment’s start time as
`SPEAKER_00 [HH:MM:SS]:`, rounded down for seeking. Correction preserves the
complete header and also supports older headers without timestamps. The merge
still does not split speaker changes within a Whisper segment.

Correction preserves speaker labels, applies custom replacements, and accepts a
Hunspell suggestion only when there is exactly one. It writes a separate corrected
transcript, a unified diff, and uncertain words. The custom dictionary uses actual
tabs between incorrect and corrected forms; commented entries are inactive.

## Porting guidelines

Preserve the following requirements when porting.

### Functional requirements

1. The user supplies one input audio file.
2. One main command coordinates the pipeline.
3. Hungarian ASR should provide `large-v3` quality.
4. Speaker diarization uses a separate audio-based model.
5. Align ASR timestamps with diarization timestamps.
6. The correction stage must preserve the original transcript.
7. Write corrections to a separate file.
8. Make every automatic correction auditable.
9. Do not automatically apply uncertain spelling corrections.
10. Require no internet access at runtime.

The correction stage preserves its input, but rerunning the full pipeline for the same audio can replace earlier generated outputs. Preserve previous outputs separately when retaining processing history.

### Privacy requirements

- Keep audio and transcripts local.
- Store models locally.
- Operate without a network connection.

### Platform-dependent components

Currently specific to Apple Silicon:

```text
MLX
mlx-whisper
mlx-lm
```

A Linux/NVIDIA port may replace `mlx-whisper` with `faster-whisper`, `whisper.cpp`, or a CUDA Whisper implementation.

`pyannote.audio` may be retained, with changes to device or backend configuration. Hunspell and FFmpeg are conceptually platform-independent, but package managers and paths may change.

## Suggested future improvements

1. Use word-level Whisper timestamps in the merge stage.
2. Assign speakers at word level.
3. Add speaker aliases, such as `SPEAKER_00 -> judge`.
4. Add a `--speakers N` option.
5. Support batch processing.
6. Add a GUI or drag-and-drop wrapper.
7. Expand the legal terminology dictionary.
8. Add a conservative local LLM as an optional second correction pass.
9. Export HTML or DOCX.
10. Link audio timestamps to the final transcript.
