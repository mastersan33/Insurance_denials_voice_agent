"""Transcript event schema.

Used by STT adapters, the media stream pipeline, and the transcript repository.
Provides a typed contract so any STT provider can emit events in a consistent format.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TranscriptEvent(BaseModel):
    call_session_id: Optional[str] = None
    stream_sid: Optional[str] = None
    speaker: str = "caller"      # "caller" | "agent"
    text: str
    is_final: bool
    confidence: Optional[float] = None
    provider: str = "elevenlabs"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def partial(
        cls,
        text: str,
        call_session_id: Optional[str] = None,
        stream_sid: Optional[str] = None,
        provider: str = "elevenlabs",
    ) -> "TranscriptEvent":
        return cls(
            call_session_id=call_session_id,
            stream_sid=stream_sid,
            text=text,
            is_final=False,
            provider=provider,
        )

    @classmethod
    def final(
        cls,
        text: str,
        call_session_id: Optional[str] = None,
        stream_sid: Optional[str] = None,
        confidence: Optional[float] = None,
        provider: str = "elevenlabs",
    ) -> "TranscriptEvent":
        return cls(
            call_session_id=call_session_id,
            stream_sid=stream_sid,
            text=text,
            is_final=True,
            confidence=confidence,
            provider=provider,
        )
