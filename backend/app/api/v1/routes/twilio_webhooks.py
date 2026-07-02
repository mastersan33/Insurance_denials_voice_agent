from fastapi import APIRouter, Request, Response
from fastapi.responses import PlainTextResponse

from backend.app.config.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/voice/answer")
async def voice_answer(request: Request):
    """TwiML response when outbound call is answered."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    logger.info("call_answered", call_sid=call_sid)

    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://{host}/api/v1/twilio/media-stream/{call_sid}" />
    </Connect>
</Response>""".format(
        host=request.headers.get("host", "localhost:8000"),
        call_sid=call_sid,
    )
    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/status")
async def voice_status_callback(request: Request):
    """Twilio status callback for call state changes."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    call_status = form_data.get("CallStatus", "")
    duration = form_data.get("CallDuration", "0")

    logger.info(
        "call_status_update",
        call_sid=call_sid,
        status=call_status,
        duration=duration,
    )
    return PlainTextResponse("OK")


@router.post("/voice/recording")
async def voice_recording_callback(request: Request):
    """Twilio recording callback."""
    form_data = await request.form()
    recording_url = form_data.get("RecordingUrl", "")
    call_sid = form_data.get("CallSid", "")

    logger.info("recording_available", call_sid=call_sid, recording_url=recording_url)
    return PlainTextResponse("OK")
