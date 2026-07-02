from fastapi import APIRouter, Request, Response
from fastapi.responses import PlainTextResponse
from openai import AsyncOpenAI

from backend.app.config.logging import get_logger
from backend.app.config.settings import settings

router = APIRouter()
logger = get_logger(__name__)

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

AGENT_GREETING = (
    "Hello, this is Sarah calling from Medical Billing Solutions on behalf of City Medical Center. "
    "I'm calling regarding a denied insurance claim for patient John Doe, claim number CLM-2026-002, "
    "denied under code CO-97. I'd like to speak with someone in your claims department to discuss "
    "the denial and explore options for appeal or reconsideration. Are you able to assist me with this today?"
)

SYSTEM_PROMPT = (
    "You are Sarah, a professional medical billing specialist making an outbound call to an insurance company "
    "to dispute a denied claim. The claim is for patient John Doe, claim number CLM-2026-002, denial code CO-97 "
    "(procedure not paid separately). Your goal is to get the denial overturned or get clear appeal instructions. "
    "Be professional, concise, and persistent. Keep responses under 3 sentences for voice clarity."
)


@router.post("/voice/answer")
async def voice_answer(request: Request):
    """TwiML response when outbound call is answered — speak greeting and listen."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    logger.info("call_answered", call_sid=call_sid)

    base_url = settings.twilio_webhook_base_url
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" language="en-US">{AGENT_GREETING}</Say>
    <Gather input="speech" timeout="5" speechTimeout="2" action="{base_url}/api/v1/twilio/voice/gather" method="POST">
        <Say voice="Polly.Joanna" language="en-US">I'm listening.</Say>
    </Gather>
    <Say voice="Polly.Joanna">I didn't hear a response. I'll call back shortly. Thank you.</Say>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/gather")
async def voice_gather(request: Request):
    """Process speech input from Twilio and respond with AI-generated reply."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    speech_result = form_data.get("SpeechResult", "")
    logger.info("speech_received", call_sid=call_sid, speech=speech_result)

    base_url = settings.twilio_webhook_base_url

    if not speech_result:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">I'm sorry, I didn't catch that. Could you please repeat?</Say>
    <Gather input="speech" timeout="5" speechTimeout="2" action="{base_url}/api/v1/twilio/voice/gather" method="POST"/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Get AI response
    try:
        completion = await openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": speech_result},
            ],
            max_tokens=150,
            temperature=0.7,
        )
        ai_reply = completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error("openai_error", error=str(e))
        ai_reply = "Thank you for that information. Could you please transfer me to your claims department supervisor?"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" language="en-US">{ai_reply}</Say>
    <Gather input="speech" timeout="5" speechTimeout="2" action="{base_url}/api/v1/twilio/voice/gather" method="POST">
        <Say voice="Polly.Joanna" language="en-US">Go ahead.</Say>
    </Gather>
    <Say voice="Polly.Joanna">Thank you for your time. We will follow up in writing. Goodbye.</Say>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/status")
async def voice_status_callback(request: Request):
    """Twilio status callback for call state changes."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    call_status = form_data.get("CallStatus", "")
    duration = form_data.get("CallDuration", "0")
    logger.info("call_status_update", call_sid=call_sid, status=call_status, duration=duration)
    return PlainTextResponse("OK")


@router.post("/voice/recording")
async def voice_recording_callback(request: Request):
    """Twilio recording callback."""
    form_data = await request.form()
    recording_url = form_data.get("RecordingUrl", "")
    call_sid = form_data.get("CallSid", "")
    logger.info("recording_available", call_sid=call_sid, recording_url=recording_url)
    return PlainTextResponse("OK")
