"""Dependency-free literal .env configuration for direct Python invocation."""

import os
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
KEYS = {
    "LT_RUNTIME_DIR", "LT_PYTHON", "LT_WHISPER", "LT_WHISPER_MODEL",
    "LT_DIARIZATION_MODEL", "LT_HUNSPELL_DICT", "LT_CUSTOM_DICT",
    "LT_FFMPEG", "LT_HUNSPELL",
}


def load_env():
    path = REPO_DIR / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or key not in KEYS:
            raise ValueError("Invalid or unknown .env setting")
        if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        os.environ.setdefault(key, value)


load_env()
RUNTIME_DIR = os.environ.get("LT_RUNTIME_DIR") or str(REPO_DIR)
DIARIZATION_MODEL = os.environ.get("LT_DIARIZATION_MODEL") or str(
    Path(RUNTIME_DIR) / "models/pyannote-speaker-diarization-community-1"
)
HUNSPELL_DICT = os.environ.get("LT_HUNSPELL_DICT") or str(Path(RUNTIME_DIR) / "dictionaries/hu_HU")
CUSTOM_DICT = os.environ.get("LT_CUSTOM_DICT") or str(REPO_DIR / "config/custom_replacements.tsv")
FFMPEG = os.environ.get("LT_FFMPEG") or "ffmpeg"
HUNSPELL = os.environ.get("LT_HUNSPELL") or "hunspell"
