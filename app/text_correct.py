#!/usr/bin/env python3

import difflib
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


from runtime_config import CUSTOM_DICT, HUNSPELL, HUNSPELL_DICT

SPEAKER_RE = re.compile(r"^\s*SPEAKER_[A-Za-z0-9_]+:\s*$")

# Words consisting of Unicode letters.
# Keeps hyphenated and apostrophe-containing forms together.
WORD_RE = re.compile(
    r"[^\W\d_]+(?:[-’'][^\W\d_]+)*",
    re.UNICODE
)


def load_custom_replacements():
    replacements = {}

    path = Path(CUSTOM_DICT)

    if not path.exists():
        return replacements

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line or line.lstrip().startswith("#"):
                continue

            parts = line.split("\t", 1)

            if len(parts) != 2:
                continue

            wrong, correct = parts

            wrong = wrong.strip()
            correct = correct.strip()

            if wrong and correct:
                replacements[wrong.casefold()] = correct

    return replacements


def preserve_case(original, replacement):
    if original.isupper():
        return replacement.upper()

    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]

    return replacement


def hunspell_check(words):
    """
    Check all unique words in one batch.

    Returns:
      word -> {
          "correct": bool,
          "suggestions": [...]
      }
    """

    if not words:
        return {}

    proc = subprocess.run(
        [
            HUNSPELL,
            "-a",
            "-i", "UTF-8",
            "-d", HUNSPELL_DICT,
        ],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        check=True,
    )

    lines = proc.stdout.splitlines()

    # first line: Hunspell version/banner
    result_lines = []

    for line in lines[1:]:
        line = line.strip()

        if not line:
            continue

        if line.startswith(("*", "+", "-", "&", "#", "?")):
            result_lines.append(line)

    results = {}

    for word, line in zip(words, result_lines):

        if line.startswith(("*", "+", "-")):
            results[word] = {
                "correct": True,
                "suggestions": [],
            }
            continue

        suggestions = []

        if line.startswith("&") and ":" in line:
            _, suggestion_string = line.split(":", 1)
            suggestions = [
                x.strip()
                for x in suggestion_string.split(",")
                if x.strip()
            ]

        results[word] = {
            "correct": False,
            "suggestions": suggestions,
        }

    return results


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("  jogijavit <text-file>")
        sys.exit(1)

    input_path = Path(sys.argv[1]).expanduser().resolve()

    if not input_path.is_file():
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() != ".txt":
        print("Error: input must be a TXT file.")
        sys.exit(1)

    base = input_path.with_suffix("")

    output_path = Path(str(base) + ".jav.txt")
    diff_path = Path(str(base) + ".diff.txt")
    uncertain_path = Path(str(base) + ".gyanus.txt")

    original = input_path.read_text(encoding="utf-8")

    custom = load_custom_replacements()

    #
    # Collect words.
    #

    words = []

    for line in original.splitlines():

        if SPEAKER_RE.match(line):
            continue

        for match in WORD_RE.finditer(line):
            word = match.group(0)

            # Words in the custom dictionary do not need to be sent to Hunspell.
            if word.casefold() not in custom:
                words.append(word)

    unique_words = list(dict.fromkeys(words))

    print(f"Hunspell check: {len(unique_words)} unique words...")

    spell_data = hunspell_check(unique_words)

    custom_count = Counter()
    hunspell_count = Counter()
    uncertain = Counter()

    #
    # Correction.
    #

    def replace_word(match):
        word = match.group(0)
        key = word.casefold()

        # 1. Custom ASR dictionary
        if key in custom:
            replacement = preserve_case(word, custom[key])

            if replacement != word:
                custom_count[(word, replacement)] += 1

            return replacement

        # 2. Hunspell
        data = spell_data.get(word)

        if not data:
            return word

        if data["correct"]:
            return word

        suggestions = data["suggestions"]

        # Automatically correct only unambiguous cases.
        if len(suggestions) == 1:
            replacement = preserve_case(word, suggestions[0])

            if replacement != word:
                hunspell_count[(word, replacement)] += 1

            return replacement

        # Multiple or no suggestions:
        # avoid guessing in legal text.
        uncertain[word] += 1

        return word

    corrected_lines = []

    for line in original.splitlines(keepends=True):

        if SPEAKER_RE.match(line.rstrip("\r\n")):
            corrected_lines.append(line)
            continue

        corrected_lines.append(
            WORD_RE.sub(replace_word, line)
        )

    corrected = "".join(corrected_lines)

    output_path.write_text(corrected, encoding="utf-8")

    #
    # Diff
    #

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        corrected.splitlines(keepends=True),
        fromfile=input_path.name,
        tofile=output_path.name,
    )

    diff_path.write_text(
        "".join(diff),
        encoding="utf-8",
    )

    #
    # Uncertain words
    #

    with uncertain_path.open("w", encoding="utf-8") as f:

        for word, count in uncertain.most_common():

            suggestions = spell_data.get(word, {}).get(
                "suggestions", []
            )

            f.write(f"{word}\t{count}")

            if suggestions:
                f.write("\t" + " | ".join(suggestions))

            f.write("\n")

    #
    # Summary
    #

    print()
    print("Done:")
    print(f"  corrected:    {output_path}")
    print(f"  changes:  {diff_path}")
    print(f"  uncertain: {uncertain_path}")

    print()

    custom_total = sum(custom_count.values())
    hunspell_total = sum(hunspell_count.values())

    print(f"Corrections from custom dictionary: {custom_total}")
    print(f"Corrections from Hunspell:     {hunspell_total}")
    print(f"Uncertain word forms:            {sum(uncertain.values())}")


if __name__ == "__main__":
    main()
