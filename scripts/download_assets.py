#!/usr/bin/env python3
"""Download fixed model revisions and checksum-verified dictionary files."""
import hashlib
import json
import os
from pathlib import Path
from urllib.request import urlopen

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parent.parent
lock = json.loads((ROOT / "assets.lock.json").read_text())
for folder, model in lock["models"].items():
    snapshot_download(
        repo_id=model["repo_id"], revision=model["revision"],
        local_dir=ROOT / "models" / folder, token=os.environ.get("HF_TOKEN"),
    )
for name, info in lock["dictionary"]["files"].items():
    data = urlopen(info["url"]).read()
    if hashlib.sha256(data).hexdigest() != info["sha256"]:
        raise RuntimeError("Dictionary checksum mismatch: " + name)
    path = ROOT / "dictionaries" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
print("Models and Hungarian dictionary are ready.")
