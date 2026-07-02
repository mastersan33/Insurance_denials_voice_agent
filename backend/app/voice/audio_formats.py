"""Audio format helpers for the Twilio Media Stream pipeline.

Twilio Media Streams send telephony audio as 8 kHz, mono, mu-law (ulaw) payloads.
ElevenLabs TTS outputs ulaw_8000 natively so no conversion is needed for playback.
For STT (speech-to-text) we send mulaw directly to ElevenLabs Scribe which accepts it.
"""
from __future__ import annotations

from typing import Dict, Union

TWILIO_SAMPLE_RATE_HZ = 8000
TWILIO_ENCODING = "mulaw"
TWILIO_CHANNELS = 1


def describe_twilio_audio_format() -> Dict[str, Union[int, str]]:
    """Return the raw audio format spec of Twilio Media Stream payloads."""
    return {
        "sample_rate_hz": TWILIO_SAMPLE_RATE_HZ,
        "encoding": TWILIO_ENCODING,
        "channels": TWILIO_CHANNELS,
    }


def prepare_audio_for_stt(audio_chunk: bytes) -> bytes:
    """Pass Twilio mulaw audio through unchanged.

    ElevenLabs Scribe accepts mulaw at 8000 Hz directly via the realtime STT
    WebSocket, so no conversion is required.  This function is the abstraction
    boundary: if a future STT provider needs PCM/WAV, implement the conversion
    here without touching media_stream.py.
    """
    return audio_chunk


def is_silence_frame(frame: bytes, threshold: float = 0.80) -> bool:
    """Return True if the mulaw frame is predominantly silence.

    Twilio mulaw silence bytes cluster around 0xFF (127 in signed) and the
    midpoint 0x7F/0x80.  A frame is considered silent when the proportion of
    bytes in those ranges exceeds *threshold*.
    """
    if not frame:
        return True
    silent = sum(1 for b in frame if b >= 0xF0 or 0x7A <= b <= 0x80)
    return (silent / len(frame)) > threshold
