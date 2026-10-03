#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "${1:-}" = "--help" ]; then
    echo "Usage: ./scripts/setup.sh [--skip-assets]"
    echo "Requires macOS 26+ arm64, Python 3.12, FFmpeg, and Hunspell."
    exit 0
fi
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--skip-assets" ]; }; then
    echo "Error: unknown setup option" >&2; exit 1
fi
if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
    echo "Error: this dependency lock targets Apple Silicon macOS." >&2; exit 1
fi
if [ "$(sw_vers -productVersion | cut -d. -f1)" -lt 26 ]; then
    echo "Error: the pinned MLX wheels require macOS 26 or newer." >&2; exit 1
fi
for tool in python3.12 ffmpeg hunspell; do
    command -v "$tool" >/dev/null || { echo "Missing $tool. Run: brew install python@3.12 ffmpeg hunspell" >&2; exit 1; }
done
python3.12 -c 'import platform, sys; assert sys.version_info[:2] == (3, 12) and platform.machine() == "arm64", "Python 3.12 arm64 required"'
if [ ! -d "$ROOT/.venv" ]; then
    python3.12 -m venv "$ROOT/.venv"
fi
"$ROOT/.venv/bin/python" -c 'import platform, sys; assert sys.version_info[:2] == (3, 12) and platform.machine() == "arm64", "Existing .venv must use Python 3.12 arm64"'
"$ROOT/.venv/bin/python" -m pip install --disable-pip-version-check --quiet -r "$ROOT/requirements.txt"
"$ROOT/.venv/bin/python" -m pip check
if [ ! -f "$ROOT/.env" ]; then cp "$ROOT/.env.example" "$ROOT/.env"; fi
if [ "${1:-}" != "--skip-assets" ]; then
    # Setup downloads online; offline flags apply only when running transcription.
    env HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 "$ROOT/.venv/bin/python" "$ROOT/scripts/download_assets.py"
fi
echo "Setup complete. Run: $ROOT/bin/jogi /path/to/audio.m4a"
