import base64
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.config.logging import get_logger
from backend.app.websocket.manager import ws_manager

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/media-stream/{call_sid}")
async def media_stream_websocket(websocket: WebSocket, call_sid: str):
    """Handle Twilio Media Stream WebSocket connection."""
    await ws_manager.connect(websocket, call_sid)
    stream_sid: str | None = None

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            event_type = message.get("event")

            if event_type == "connected":
                logger.info("media_stream_connected", call_sid=call_sid)

            elif event_type == "start":
                stream_sid = message.get("start", {}).get("streamSid")
                logger.info("media_stream_started", call_sid=call_sid, stream_sid=stream_sid)

            elif event_type == "media":
                payload = message.get("media", {}).get("payload", "")
                audio_data = base64.b64decode(payload)
                # Process audio through STT pipeline
                await _process_audio_chunk(call_sid, audio_data)

            elif event_type == "dtmf":
                digit = message.get("dtmf", {}).get("digit")
                logger.info("dtmf_received", call_sid=call_sid, digit=digit)

            elif event_type == "stop":
                logger.info("media_stream_stopped", call_sid=call_sid)
                break

    except WebSocketDisconnect:
        logger.info("media_stream_disconnected", call_sid=call_sid)
    except Exception as e:
        logger.error("media_stream_error", call_sid=call_sid, error=str(e))
    finally:
        await ws_manager.disconnect(call_sid)


async def send_audio_to_stream(call_sid: str, audio_bytes: bytes) -> None:
    """Send audio back to Twilio Media Stream."""
    payload = base64.b64encode(audio_bytes).decode("utf-8")
    message = {
        "event": "media",
        "media": {"payload": payload},
    }
    await ws_manager.send_json(call_sid, message)


async def clear_audio_stream(call_sid: str) -> None:
    """Clear queued audio (for barge-in handling)."""
    message = {"event": "clear"}
    await ws_manager.send_json(call_sid, message)


async def _process_audio_chunk(call_sid: str, audio_data: bytes) -> None:
    """Process incoming audio chunk through STT and AI pipeline."""
    # This integrates with ElevenLabs STT and the LangGraph agent
    # Audio accumulation and processing happens here
    pass
