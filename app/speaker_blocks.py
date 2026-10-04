"""Render speaker blocks with seek positions from Whisper segment timestamps."""


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
