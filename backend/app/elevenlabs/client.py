import asyncio
from collections.abc import AsyncGenerator

import httpx

from backend.app.config.logging import get_logger
from backend.app.config.settings import settings

logger = get_logger(__name__)

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


class ElevenLabsClient:
    def __init__(self):
        self._http_client: httpx.AsyncClient | None = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=ELEVENLABS_BASE_URL,
                headers={
                    "xi-api-key": settings.elevenlabs_api_key,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._http_client

    async def text_to_speech_stream(
        self,
        text: str,
        voice_id: str | None = None,
        output_format: str = "ulaw_8000",
    ) -> AsyncGenerator[bytes, None]:
        """Stream TTS audio chunks from ElevenLabs."""
        vid = voice_id or settings.elevenlabs_voice_id
        url = f"/text-to-speech/{vid}/stream"

        payload = {
            "text": text,
            "model_id": settings.elevenlabs_model_id,
            "voice_settings": {
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.3,
                "use_speaker_boost": True,
            },
        }

        async with self.http_client.stream(
            "POST",
            url,
            json=payload,
            params={"output_format": output_format, "optimize_streaming_latency": "3"},
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size=1024):
                yield chunk

    async def speech_to_text(self, audio_data: bytes) -> str:
        """Transcribe audio using ElevenLabs STT."""
        url = "/speech-to-text"
        files = {"audio": ("audio.wav", audio_data, "audio/wav")}

        response = await self.http_client.post(
            url,
            files=files,
            headers={"Content-Type": None},  # Let httpx set multipart
        )
        response.raise_for_status()
        result = response.json()
        return result.get("text", "")

    async def close(self) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


elevenlabs_client = ElevenLabsClient()
