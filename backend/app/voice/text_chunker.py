"""Split agent response text into sentence-level chunks for streaming TTS."""

from __future__ import annotations

import re
from typing import List


def split_text_into_tts_chunks(text: str) -> List[str]:
    """Return sentence-level chunks for lower-latency TTS streaming.

    Splits on '.', '!', '?' so ElevenLabs can start generating audio for
    sentence 1 while sentence 2 is still being queued.
    """
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    sentences = re.findall(r"[^.!?]+[.!?]?", cleaned)
    return [s.strip() for s in sentences if s.strip()]
