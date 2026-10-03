# Shared configuration for the command wrappers.
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Read literal KEY=value assignments; never execute the .env file.
if [ -f "$REPO_DIR/.env" ]; then
    while IFS= read -r config_line || [ -n "$config_line" ]; do
        config_line="${config_line%$'\r'}"
        case "$config_line" in
            ''|\#*) continue ;;
        esac
        if [[ "$config_line" != *=* ]]; then
            echo "Error: invalid .env assignment" >&2
            exit 1
        fi
        config_key="${config_line%%=*}"
        config_value="${config_line#*=}"
        case "$config_key" in
            LT_RUNTIME_DIR|LT_PYTHON|LT_WHISPER|LT_WHISPER_MODEL|LT_DIARIZATION_MODEL|LT_HUNSPELL_DICT|LT_CUSTOM_DICT|LT_FFMPEG|LT_HUNSPELL) ;;
            *) echo "Error: unknown .env setting: $config_key" >&2; exit 1 ;;
        esac
        if [[ "$config_value" == \"*\" && "$config_value" == *\" ]]; then
            config_value="${config_value:1:${#config_value}-2}"
        elif [[ "$config_value" == \'*\' && "$config_value" == *\' ]]; then
            config_value="${config_value:1:${#config_value}-2}"
        fi
        if [ -z "${!config_key+x}" ]; then
            export "$config_key=$config_value"
        fi
    done < "$REPO_DIR/.env"
fi

export LT_RUNTIME_DIR="${LT_RUNTIME_DIR:-$REPO_DIR}"
export LT_PYTHON="${LT_PYTHON:-$LT_RUNTIME_DIR/.venv/bin/python}"
export LT_WHISPER="${LT_WHISPER:-$LT_RUNTIME_DIR/.venv/bin/mlx_whisper}"
export LT_WHISPER_MODEL="${LT_WHISPER_MODEL:-$LT_RUNTIME_DIR/models/whisper-large-v3-mlx}"
export LT_DIARIZATION_MODEL="${LT_DIARIZATION_MODEL:-$LT_RUNTIME_DIR/models/pyannote-speaker-diarization-community-1}"
export LT_HUNSPELL_DICT="${LT_HUNSPELL_DICT:-$LT_RUNTIME_DIR/dictionaries/hu_HU}"
export LT_CUSTOM_DICT="${LT_CUSTOM_DICT:-$REPO_DIR/config/custom_replacements.tsv}"
export LT_FFMPEG="${LT_FFMPEG:-ffmpeg}"
export LT_HUNSPELL="${LT_HUNSPELL:-hunspell}"
