"""Normalization helpers for STT transcript output."""

from __future__ import annotations

import re

SPOKEN_DIGITS: dict[str, str] = {
    "zero": "0", "oh": "0", "o": "0",
    "one": "1", "two": "2", "three": "3",
    "four": "4", "for": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8",
    "ate": "8", "nine": "9",
}


def normalize_transcript_text(text: str) -> str:
    """Strip extra whitespace from transcript text."""
    return re.sub(r"\s+", " ", text).strip()


def normalize_spoken_digits(text: str) -> str:
    """Convert simple spoken digit sequences to numeric strings."""
    words = normalize_transcript_text(text).lower().split()
    if all(w in SPOKEN_DIGITS for w in words):
        return "".join(SPOKEN_DIGITS[w] for w in words)
    return " ".join(SPOKEN_DIGITS.get(w, w) for w in words)


def normalize_claim_number(text: str) -> str:
    """Normalize a spoken or typed claim number for comparison."""
    return re.sub(r"[^a-zA-Z0-9]", "", normalize_spoken_digits(text)).upper()
