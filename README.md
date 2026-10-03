# LegalTranscriber

An offline transcription system for Hungarian legal audio on macOS.

The goal is to process 1–2 hours of Hungarian audio locally, without cloud services, and produce:

- a raw transcript,
- SRT subtitles with timestamps,
- Whisper JSON,
- a transcript separated by speaker (`SPEAKER_00`, `SPEAKER_01`, ...),
- an automatically corrected version,
- a diff and a list of uncertain words.

## Usage

Run the complete pipeline with a single command:

```bash
./bin/jogi /path/to/targyalas.m4a
```

Example:

```bash
./bin/jogi ~/Desktop/targyalas.m4a
```

Supported input formats include `.m4a`, `.mp3`, and `.wav`.

The main output is:

```text
targyalas.speakers.jav.txt
```

Additional outputs:

```text
targyalas.txt
targyalas.srt
targyalas.json
targyalas.speakers.txt
targyalas.speakers.diff.txt
targyalas.speakers.gyanus.txt
```

## Pipeline

```text
Audio file
   ↓
FFmpeg
   ↓
Whisper large-v3 / MLX
   ↓
TXT + SRT + JSON
   ↓
pyannote speaker diarization
   ↓
SPEAKER_00 / SPEAKER_01 / ...
   ↓
Hunspell + custom ASR dictionary
   ↓
Corrected TXT + diff + uncertain words
```

## Main components

### `jogi`

The main entry point. Runs transcription, speaker diarization, and automatic text correction in sequence.

### `jogirat`

Uses FFmpeg to temporarily convert the audio to a 16 kHz mono WAV file, then transcribes it with the local `whisper-large-v3-mlx` model.

Usage:

```bash
./bin/jogirat hanganyag.m4a
./bin/jogirat --srt hanganyag.m4a
./bin/jogirat --json hanganyag.m4a
./bin/jogirat --all hanganyag.m4a
```

### `jogispeaker`

Uses the local pyannote `speaker-diarization-community-1` model to identify when each speaker is speaking, then aligns that information with the timestamps in the Whisper JSON output.

Output:

```text
SPEAKER_00:
...

SPEAKER_01:
...
```

### `jogijavit`

Performs conservative automatic error correction using a Hungarian Hunspell dictionary and a custom ASR correction dictionary.

The correction dictionary is `config/custom_replacements.tsv`.

Example:

```text
jótárási\tjótállási
megbizotja\tmegbízottja
üzembehelyezés\tüzembe helyezés
elemikár\telemi kár
```

The correction tool leaves the original file intact, preserves the `SPEAKER_XX:` labels, creates a separate diff, and lists uncertain word forms separately.

## Privacy

All processing takes place locally. Once the models have been downloaded, transcription and diarization work without an internet connection.

The runner scripts enforce offline mode:

```text
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

Audio and transcripts are not uploaded to the cloud during processing.


## Note

Speaker diarization and automatic correction are not completely accurate. For legal use, the final text should be reviewed by a person.

The original Whisper transcript, the speaker-labeled version, the corrected version, and the diff are retained as separate files so that the processing can be audited.

## Repository layout and local development

- `bin/`: command wrappers (English terminal messages).
- `app/`: transcription post-processing and diarization scripts.
- `config/`: Hungarian ASR correction dictionary.
- `.env.example`: runtime and model path settings; copy to `.env` to customize.

Run the repository version from the project directory:

```bash
./bin/jogi /path/to/audio.m4a
```

Run `./scripts/setup.sh` first to create the project-local `.venv/`, `models/`,
and `dictionaries/`. See [Installation](INSTALL.md) for setup instructions and
[Development guide](docs/DEVELOPMENT.md) for configuration, dependency maintenance,
porting requirements, and future improvements. Downloaded assets and the Python
environment are excluded from Git.

The coordinator invokes its sibling commands, which run the repository's Python
scripts and correction dictionary. Command names and the `.jav.txt` and
`.gyanus.txt` suffixes retain their existing spelling for compatibility.
Transcription and correction target Hungarian audio and text.
