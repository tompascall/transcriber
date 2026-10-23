"""Render speaker blocks with seek positions from Whisper segment timestamps."""


import argparse
import json
from pathlib import Path


def format_timestamp(seconds):
    # Round down so seeking does not skip the beginning of a segment.
    hours, remainder = divmod(max(0, int(seconds)), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def merge_blocks(segments):
    blocks = []
    for segment in segments:
        if blocks and blocks[-1]["speaker"] == segment["speaker"]:
            blocks[-1]["text"] += " " + segment["text"]
            blocks[-1]["end"] = segment["end"]
        else:
            blocks.append(dict(segment))
    return blocks


def render_blocks(blocks):
    return "".join(
        f'{block["speaker"]} [{format_timestamp(block["start"])}]:\n'
        f'{block["text"]}\n\n'
        for block in blocks
    )


def save_blocks(path, blocks):
    """Keep original text and full-precision recording positions for later rendering."""
    data = {"version": 1, "time_unit": "seconds", "blocks": blocks}
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_blocks(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("version") != 1 or data.get("time_unit") != "seconds":
        raise ValueError("Unsupported speaker JSON format")
    return data["blocks"]


def main():
    parser = argparse.ArgumentParser(description="Render a timestamped transcript without running models.")
    parser.add_argument("input", type=Path, help="Existing recording.speakers.json")
    parser.add_argument("--output", type=Path, help="Default: input path with .txt suffix")
    args = parser.parse_args()
    output = args.output or args.input.with_suffix(".txt")
    if output.resolve() == args.input.resolve():
        parser.error("Output must differ from input")
    # Read and render before opening output, preserving it if loading fails.
    text = render_blocks(load_blocks(args.input))
    output.write_text(text, encoding="utf-8")
    print(f"Done: {output}")


if __name__ == "__main__":
    main()
