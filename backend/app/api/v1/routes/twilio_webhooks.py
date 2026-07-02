from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import PlainTextResponse

from backend.app.config.logging import get_logger
from backend.app.config.settings import settings
from backend.app.core.twilio_security import validate_twilio_signature
from backend.app.db.session import async_session_factory
from backend.app.repositories.call_session_repository import CallSessionRepository
from agent.outcomes import CallOutcome

router = APIRouter()
logger = get_logger(__name__)

# Map Twilio CallStatus strings → CallOutcome enum values
_TWILIO_STATUS_TO_OUTCOME: dict[str, str] = {
    "completed": CallOutcome.COMPLETED.value,
    "failed": CallOutcome.FAILED.value,
    "busy": CallOutcome.FAILED.value,
    "no-answer": CallOutcome.NO_ANSWER.value,
}


@router.post("/voice/answer", dependencies=[Depends(validate_twilio_signature)])
async def voice_answer(request: Request):
    """TwiML: open bidirectional media stream to our WebSocket pipeline."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    logger.info("call_answered", call_sid=call_sid)

    ws_host = settings.twilio_webhook_base_url.replace("https://", "").replace("http://", "")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://{ws_host}/api/v1/twilio/media-stream/{call_sid}" />
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/status", dependencies=[Depends(validate_twilio_signature)])
async def voice_status_callback(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    call_status = form_data.get("CallStatus", "")
    duration = int(form_data.get("CallDuration", "0") or 0)
    logger.info("call_status_update", call_sid=call_sid, status=call_status, duration=duration)

    if call_status in _TWILIO_STATUS_TO_OUTCOME and call_sid:
        try:
            async with async_session_factory() as db:
                repo = CallSessionRepository(db)
                session = await repo.get_by_call_sid(call_sid)
                if session:
                    updates: dict = {"status": call_status}
                    if duration:
                        updates["duration_seconds"] = duration
                    if not session.outcome:
                        updates["outcome"] = _TWILIO_STATUS_TO_OUTCOME[call_status]
                    await repo.update(session, updates)
                    await db.commit()
        except Exception as e:
            logger.error("status_update_db_error", call_sid=call_sid, error=str(e))

    return PlainTextResponse("OK")


@router.post("/voice/recording", dependencies=[Depends(validate_twilio_signature)])
async def voice_recording_callback(request: Request):
    form_data = await request.form()
    recording_url = form_data.get("RecordingUrl", "")
    call_sid = form_data.get("CallSid", "")
    logger.info("recording_available", call_sid=call_sid, recording_url=recording_url)

    if recording_url and call_sid:
        try:
            async with async_session_factory() as db:
                repo = CallSessionRepository(db)
                session = await repo.get_by_call_sid(call_sid)
                if session:
                    await repo.update(session, {"recording_url": recording_url})
                    await db.commit()
        except Exception as e:
            logger.error("recording_url_db_error", call_sid=call_sid, error=str(e))

    return PlainTextResponse("OK")

