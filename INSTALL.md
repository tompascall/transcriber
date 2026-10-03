# Installation

Supported target: Apple Silicon macOS 26 or newer with native arm64 Python 3.12. A machine
with 16 GB memory can use the current pipeline. Initial setup needs internet
access and several gigabytes of free disk space; transcription runs offline.

## Prerequisites

Install Homebrew, then:

```bash
brew install python@3.12 ffmpeg hunspell
```

Python packages, models, and the Hungarian dictionary live inside the checkout.
FFmpeg, Hunspell, and Python itself are system tools managed by Homebrew.
Homebrew versions are not pinned by the Python dependency lock.

## Setup

From the repository root:

```bash
./scripts/setup.sh
```

Before downloading the diarization model, accept the terms for
[pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
and obtain a Hugging Face read token. Provide it to setup through the environment:

```bash
read -s HF_TOKEN
export HF_TOKEN
./scripts/setup.sh
unset HF_TOKEN
```

The script creates `.venv/`, installs the pinned runtime packages, checks their
compatibility, and downloads the models and dictionary specified in
`assets.lock.json`. It creates `.env` from `.env.example` if absent. Existing
configuration is preserved. No administrator access is needed for project files.
A failed download can be retried by running setup again.

To install only the Python environment:

```bash
./scripts/setup.sh --skip-assets
```

Model downloads require a token only during setup. Keep tokens out of committed
files. If `.env` overrides paths, you must provision those locations separately:
setup always prepares the default directories inside this checkout.

## Run and verify

```bash
./bin/jogi /path/to/recording.m4a
```

Expected outputs next to the recording:

```text
recording.txt
recording.srt
recording.json
recording.speakers.txt
recording.speakers.jav.txt
recording.speakers.diff.txt
recording.speakers.gyanus.txt
```

Check that the full recording was processed, speaker labels were created,
corrections worked, and the original transcript was preserved by the correction
stage. Rerunning transcription for the same recording can replace existing
outputs. Test without a network connection to confirm the offline installation.

See [Development guide](docs/DEVELOPMENT.md) for configuration, dependency
maintenance, architecture, and porting requirements.

## Troubleshooting

If Whisper reports `No Metal device available`, run it from a regular Terminal
session on the Mac. MLX needs access to the Apple GPU; a restricted or headless
execution environment may prevent it from loading even when installation is valid.
