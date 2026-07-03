import asyncio
import base64
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urlencode

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config.logging import get_logger
from backend.app.config.settings import settings
from backend.app.db.session import async_session_factory as AsyncSessionLocal
from backend.app.models.human_handoff import HumanHandoff
from backend.app.models.ticket import Ticket
from backend.app.models.transcript import Transcript
from backend.app.repositories.billing_case_repository import BillingCaseRepository
from backend.app.repositories.call_job_repository import CallJobRepository
from backend.app.repositories.call_session_repository import CallSessionRepository
from backend.app.repositories.human_handoff_repository import HumanHandoffRepository
from backend.app.repositories.ticket_repository import TicketRepository
from backend.app.repositories.transcript_repository import TranscriptRepository
from backend.app.voice.audio_formats import is_silence_frame
from backend.app.voice.text_chunker import split_text_into_tts_chunks
from backend.app.voice.transcript_normalizer import normalize_transcript_text
from backend.app.websocket.manager import ws_manager
from agent.outcomes import CallOutcome

router = APIRouter()
logger = get_logger(__name__)

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

# ---------------------------------------------------------------------------
# Denial code knowledge base (Day 9 — billing tools)
# ---------------------------------------------------------------------------
DENIAL_CODE_INFO: dict[str, dict] = {
    "CO-97": {
        "description": "Payment is included in the allowance for another service/procedure that has already been adjudicated.",
        "appeal_steps": "Submit a corrected claim with modifier -59 or XU to unbundle. Attach operative notes proving medical necessity for separate billing.",
        "common_fix": "Add modifier -59 (distinct procedural service) or modifier -25 (significant separate E&M).",
    },
    "CO-4": {
        "description": "Service is inconsistent with the modifier used.",
        "appeal_steps": "Review modifier usage, correct the claim, resubmit with appropriate modifier and documentation.",
        "common_fix": "Remove or correct the conflicting modifier.",
    },
    "CO-16": {
        "description": "Claim lacks information or has submission/billing error.",
        "appeal_steps": "Identify the missing field (often NPI, diagnosis pointer, or dates), correct the claim, and resubmit.",
        "common_fix": "Complete all required fields and resubmit.",
    },
    "CO-50": {
        "description": "Non-covered service — not deemed a medical necessity by the payer.",
        "appeal_steps": "Submit a Letter of Medical Necessity from the treating physician with supporting clinical documentation.",
        "common_fix": "Obtain and attach Letter of Medical Necessity.",
    },
    "CO-22": {
        "description": "This care may be covered by another payer per coordination of benefits.",
        "appeal_steps": "Confirm primary vs secondary payer order. Submit to primary first, then secondary with EOB attached.",
        "common_fix": "Submit to correct primary payer first.",
    },
}

def _get_denial_info(denial_code: str) -> str:
    """Return structured denial code info for agent context."""
    info = DENIAL_CODE_INFO.get(denial_code.upper())
    if not info:
        return f"Denial code {denial_code}: No specific information available. Request detailed explanation from payer."
    return (
        f"Denial code {denial_code}: {info['description']} "
        f"Appeal approach: {info['appeal_steps']} "
        f"Quick fix: {info['common_fix']}"
    )

# ---------------------------------------------------------------------------
# System prompt builder (injects billing case context)
# ---------------------------------------------------------------------------
def _build_system_prompt(billing_context: dict | None) -> str:
    base = (
        "You are an AI billing specialist assistant making an outbound call "
        "to an insurance company to dispute a denied claim. "
        "You must disclose that you are an AI assistant if asked directly. "
        "Your goal is to get the denial overturned or obtain clear appeal instructions. "
        "Be professional, concise, and persistent. Keep every response under 3 sentences for voice clarity. "
        "Never invent claim details not provided to you — only state facts from the case data below. "
        "If the caller says 'transfer', 'supervisor', 'manager', 'human', or 'agent', "
        "respond EXACTLY with: [HANDOFF] I understand, let me connect you with a senior specialist."
    )
    if billing_context:
        base += (
            f"\n\nCASE DETAILS — use these facts only:\n"
            f"Patient: {billing_context.get('patient_name', 'N/A')}\n"
            f"Payer: {billing_context.get('payer_name', 'N/A')}\n"
            f"Claim #: {billing_context.get('claim_number', 'N/A')}\n"
            f"Denial Code: {billing_context.get('denial_code', 'N/A')}\n"
            f"Denial Reason: {billing_context.get('denial_reason', 'N/A')}\n"
            f"Amount Billed: ${billing_context.get('amount_billed', 'N/A')}\n"
            f"Provider: {billing_context.get('provider_name', 'N/A')} (NPI: {billing_context.get('provider_npi', 'N/A')})\n"
            f"Denial Guidance: {_get_denial_info(billing_context.get('denial_code', ''))}"
        )
    return base

SILENCE_FRAMES_THRESHOLD = 35   # ~700ms of silence triggers STT
MAX_BUFFER_FRAMES = 250          # ~5 seconds max buffer
PROLONGED_SILENCE_FRAMES = 750  # ~15 seconds — send fallback phrase

# ---------------------------------------------------------------------------
# Call context (per active call)
# ---------------------------------------------------------------------------
@dataclass
class CallContext:
    stream_sid: str = ""
    audio_frames: list = field(default_factory=list)  # list of raw mulaw bytes chunks
    messages: list = field(default_factory=list)
    is_processing: bool = False
    silence_frames: int = 0
    speech_frames: int = 0
    call_session_id: str = ""          # DB call session ID
    billing_context: dict | None = None  # BillingCase fields
    transcript_seq: int = 0            # sequence counter for DB transcripts
    handoff_requested: bool = False    # human handoff flag
    system_prompt: str = ""            # built once per call
    prolonged_silence_frames: int = 0  # total silence counter for 15s fallback
    fallback_spoken: bool = False       # whether the prolonged-silence prompt was sent

_call_contexts: dict[str, CallContext] = {}


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------
def _frame_is_silence(frame: bytes) -> bool:
    return is_silence_frame(frame)


# ---------------------------------------------------------------------------
# DB helpers (Day 13 — save transcripts + update session)
# ---------------------------------------------------------------------------
async def _save_transcript(call_session_id: str, speaker: str, content: str, seq: int, db: AsyncSession) -> None:
    try:
        repo = TranscriptRepository(db)
        t = Transcript(
            call_session_id=call_session_id,
            speaker=speaker,
            content=content,
            sequence_number=seq,
        )
        await repo.create(t)
    except Exception as e:
        logger.error("transcript_save_error", error=str(e))


async def _update_session_outcome(call_session_id: str, outcome: str, outcome_details: str) -> None:
    try:
        async with AsyncSessionLocal() as db:
            repo = CallSessionRepository(db)
            session = await repo.get_by_id(call_session_id)
            if session:
                await repo.update(session, {
                    "outcome": outcome,
                    "outcome_details": outcome_details,
                    "ended_at": datetime.now(UTC),
                    "status": "completed",
                })
    except Exception as e:
        logger.error("session_outcome_error", error=str(e))


async def _create_handoff_record(call_session_id: str, reason: str, context_summary: str) -> None:
    """Day 10 — persist human handoff request to DB and auto-create a ticket."""
    try:
        async with AsyncSessionLocal() as db:
            handoff_repo = HumanHandoffRepository(db)
            ticket_repo = TicketRepository(db)
            handoff = HumanHandoff(
                call_session_id=call_session_id,
                reason=reason,
                context_summary=context_summary,
                status="pending",
            )
            await handoff_repo.create(handoff)
            ticket = Ticket(
                title=f"Human handoff requested — {reason[:80]}",
                description=context_summary,
                priority="high",
                status="open",
            )
            await ticket_repo.create(ticket)
            await db.commit()
            logger.info("handoff_created", call_session_id=call_session_id)
    except Exception as e:
        logger.error("handoff_create_error", error=str(e))


async def _load_billing_context(call_sid: str) -> tuple[str, dict | None]:
    """Load call session ID and billing case data from DB by Twilio call SID."""
    try:
        async with AsyncSessionLocal() as db:
            repo = CallSessionRepository(db)
            session = await repo.get_by_call_sid(call_sid)
            if not session:
                return "", None
            # Navigate to billing case via call_job
            job_repo = CallJobRepository(db)
            job = await job_repo.get_by_id(session.call_job_id)
            if not job:
                return session.id, None
            case_repo = BillingCaseRepository(db)
            case = await case_repo.get_by_id(job.billing_case_id)
            if not case:
                return session.id, None
            return session.id, {
                "patient_name": case.patient_name,
                "payer_name": case.payer_name,
                "claim_number": case.claim_number,
                "denial_code": case.denial_code or "",
                "denial_reason": case.denial_reason or "",
                "amount_billed": case.amount_billed,
                "provider_name": case.provider_name or "",
                "provider_npi": case.provider_npi or "",
            }
    except Exception as e:
        logger.error("billing_context_load_error", error=str(e))
        return "", None


# ---------------------------------------------------------------------------
# STT — ElevenLabs realtime WebSocket
# ---------------------------------------------------------------------------
def _stt_is_final(payload: dict) -> bool:
    etype = str(payload.get("type") or payload.get("event") or "").lower()
    if etype in {"final", "committed", "transcript_final", "speech_final"}:
        return True
    return bool(payload.get("is_final") or payload.get("final")
                or payload.get("is_committed") or payload.get("committed"))


def _stt_extract_text(payload: dict) -> str:
    for key in ("text", "transcript", "partial", "final"):
        v = payload.get(key)
        if isinstance(v, str) and v:
            return v
    inner = payload.get("transcript")
    if isinstance(inner, dict):
        for key in ("text", "transcript"):
            v = inner.get(key)
            if isinstance(v, str) and v:
                return v
    return ""


async def _stt(audio_frames: list[bytes], call_sid: str) -> str:
    api_key = settings.elevenlabs_api_key
    if not api_key or not audio_frames:
        return ""
    total_bytes = sum(len(f) for f in audio_frames)
    if total_bytes < 3200:
        return ""

    url = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"
    headers = {"xi-api-key": api_key}
    final_text = ""
    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            # Send all buffered audio frames
            for chunk in audio_frames:
                if chunk:
                    await ws.send(json.dumps({
                        "audio": base64.b64encode(chunk).decode("ascii"),
                        "encoding": "mulaw",
                        "sample_rate": 8000,
                    }))
            # Signal end of audio
            await ws.send(json.dumps({"audio": ""}))
            # Collect transcript until final arrives
            async with asyncio.timeout(10.0):
                async for raw_msg in ws:
                    try:
                        payload = json.loads(raw_msg)
                    except json.JSONDecodeError:
                        continue
                    text = _stt_extract_text(payload)
                    if text:
                        final_text = text
                    if _stt_is_final(payload):
                        break
    except Exception as e:
        logger.error("stt_error", call_sid=call_sid, error=str(e))
    return normalize_transcript_text(final_text)


async def _get_agent_response(ctx: CallContext, transcript: str) -> str:
    """Run the LangGraph billing agent and return its text response.

    The agent has access to billing tools (lookup_claim, update_gathered_info,
    search_knowledge_base, request_human_handoff, end_call) so every factual
    statement is grounded in a tool call result — not invented by the LLM.
    Falls back to direct GPT if the agent graph fails.
    """
    from agent.graph import agent_graph

    ctx.messages.append({"role": "user", "content": transcript})

    # Build LangGraph state from current call context
    billing = ctx.billing_context or {}
    state = {
        "messages": [HumanMessage(content=transcript)],
        "call_id": ctx.call_session_id,
        "call_sid": "",
        "call_job_id": "",
        "billing_case_id": "",
        "patient_name": billing.get("patient_name", ""),
        "payer_name": billing.get("payer_name", ""),
        "claim_number": billing.get("claim_number", ""),
        "denial_code": billing.get("denial_code", ""),
        "denial_reason": billing.get("denial_reason", ""),
        "current_phase": "information_gathering",
        "phase_turn_count": len(ctx.messages) // 2,
        "representative_name": "",
        "reference_number": "",
        "appeal_deadline": "",
        "appeal_method": "",
        "resolution_offered": "",
        "gathered_info": {},
        "confidence_score": 1.0,
        "should_escalate": False,
        "escalation_reason": "",
        "should_end_call": False,
        "ivr_attempts": 0,
        "human_detected": True,
        "response_text": "",
        "dtmf_to_send": "",
    }

    try:
        result = await agent_graph.ainvoke(state)
        response = result.get("response_text", "")
        if not response:
            # Extract last AI message from messages list
            for msg in reversed(result.get("messages", [])):
                content = getattr(msg, "content", None)
                if isinstance(content, str) and content.strip():
                    response = content.strip()
                    break
        if result.get("should_escalate"):
            response = f"[HANDOFF] {result.get('escalation_reason', 'Escalating to human specialist.')}"
        if response:
            ctx.messages.append({"role": "assistant", "content": response})
            return response
    except Exception as e:
        logger.error("langgraph_error", error=str(e))

    # Fallback: direct GPT call (maintains voice loop even if agent graph fails)
    try:
        completion = await openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "system", "content": ctx.system_prompt}] + ctx.messages[-10:],
            max_tokens=120,
            temperature=0.7,
        )
        response = completion.choices[0].message.content.strip()
        ctx.messages.append({"role": "assistant", "content": response})
        return response
    except Exception as e:
        logger.error("llm_fallback_error", error=str(e))
        return "I apologize, could you please repeat that?"


# ---------------------------------------------------------------------------
# TTS — ElevenLabs streaming WebSocket (ulaw_8000 native → no audioop needed)
# ---------------------------------------------------------------------------
async def _speak(call_sid: str, text: str) -> None:
    ctx = _call_contexts.get(call_sid)
    if not ctx:
        return
    api_key = settings.elevenlabs_api_key
    voice_id = settings.elevenlabs_voice_id
    if not api_key or not voice_id:
        logger.error("tts_missing_config", call_sid=call_sid)
        return

    logger.info("tts_start", call_sid=call_sid, chars=len(text))
    params = urlencode({"model_id": settings.elevenlabs_model_id, "output_format": "ulaw_8000"})
    url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?{params}"
    chunks = split_text_into_tts_chunks(text)

    try:
        async with websockets.connect(url) as ws:
            # Auth + voice settings start payload
            await ws.send(json.dumps({
                "text": " ",
                "xi_api_key": api_key,
                "voice_settings": {
                    "stability": settings.elevenlabs_tts_stability,
                    "similarity_boost": settings.elevenlabs_tts_similarity_boost,
                    "use_speaker_boost": settings.elevenlabs_tts_use_speaker_boost,
                },
            }))
            # Send sentence chunks — last one with try_trigger_generation=True
            for i, chunk in enumerate(chunks):
                await ws.send(json.dumps({
                    "text": chunk,
                    "try_trigger_generation": i == len(chunks) - 1,
                }))
            # EOF
            await ws.send(json.dumps({"text": ""}))
            # Stream audio as it arrives → directly to Twilio
            async for raw_msg in ws:
                try:
                    payload = json.loads(raw_msg)
                except (json.JSONDecodeError, TypeError):
                    continue
                audio_b64 = payload.get("audio")
                if audio_b64 and isinstance(audio_b64, str):
                    audio_bytes = base64.b64decode(audio_b64)
                    if ctx.stream_sid and audio_bytes:
                        await send_audio_to_stream(call_sid, ctx.stream_sid, audio_bytes)
    except Exception as e:
        logger.error("tts_error", call_sid=call_sid, error=str(e))
    logger.info("tts_done", call_sid=call_sid)


# ---------------------------------------------------------------------------
# Main pipeline (STT → Agent → TTS + handoff + DB saves)
# ---------------------------------------------------------------------------
async def _run_pipeline(call_sid: str) -> None:
    ctx = _call_contexts.get(call_sid)
    if not ctx or ctx.is_processing or ctx.handoff_requested:
        return

    audio_frames = ctx.audio_frames[:]
    ctx.audio_frames = []
    ctx.speech_frames = 0
    ctx.silence_frames = 0

    if sum(len(f) for f in audio_frames) < 3200:
        return

    ctx.is_processing = True
    try:
        # STT — ElevenLabs realtime WS
        transcript = await _stt(audio_frames, call_sid)
        logger.info("transcript_received", call_sid=call_sid, chars=len(transcript), empty=not transcript)
        if not transcript:
            return

        # Save human turn to DB (Day 13)
        if ctx.call_session_id:
            ctx.transcript_seq += 1
            async with AsyncSessionLocal() as db:
                await _save_transcript(ctx.call_session_id, "human", transcript, ctx.transcript_seq, db)
                await db.commit()

        # Agent response (Day 9 — uses billing context in system prompt)
        response = await _get_agent_response(ctx, transcript)
        logger.info("agent_response", call_sid=call_sid, chars=len(response), handoff="[HANDOFF]" in response)

        # Check for human handoff signal (Day 10)
        if "[HANDOFF]" in response:
            ctx.handoff_requested = True
            clean_response = response.replace("[HANDOFF]", "").strip()
            logger.info("handoff_triggered", call_sid=call_sid)
            await clear_audio_stream(call_sid, ctx.stream_sid)
            await _speak(call_sid, clean_response)
            # Save agent handoff response to transcript DB
            if ctx.call_session_id and clean_response:
                ctx.transcript_seq += 1
                async with AsyncSessionLocal() as db:
                    await _save_transcript(ctx.call_session_id, "agent", clean_response, ctx.transcript_seq, db)
                    await db.commit()
            # Persist handoff + ticket
            summary = " | ".join(
                f"{m['role']}: {m['content'][:80]}" for m in ctx.messages[-6:]
            )
            if ctx.call_session_id:
                await _create_handoff_record(ctx.call_session_id, "Caller requested human agent", summary)
                await _update_session_outcome(
                    ctx.call_session_id,
                    CallOutcome.TRANSFERRED_TO_HUMAN.value,
                    "Human handoff requested during call",
                )
        elif response:
            # Normal conversation flow — speak and save agent response to DB
            await clear_audio_stream(call_sid, ctx.stream_sid)
            await _speak(call_sid, response)
            if ctx.call_session_id:
                ctx.transcript_seq += 1
                async with AsyncSessionLocal() as db:
                    await _save_transcript(ctx.call_session_id, "agent", response, ctx.transcript_seq, db)
                    await db.commit()
    except Exception as e:
        logger.error("pipeline_error", call_sid=call_sid, error=str(e))
    finally:
        ctx.is_processing = False


# ---------------------------------------------------------------------------
# WebSocket handler
# ---------------------------------------------------------------------------
@router.websocket("/media-stream/{call_sid}")
async def media_stream_websocket(websocket: WebSocket, call_sid: str):
    await ws_manager.connect(websocket, call_sid)
    logger.info("media_stream_connected", call_sid=call_sid)

    # Load billing context and build per-call system prompt (Day 9)
    session_id, billing_ctx = await _load_billing_context(call_sid)

    denial_code = (billing_ctx or {}).get("denial_code", "CO-97")
    payer = (billing_ctx or {}).get("payer_name", "the insurance company")
    claim_no = (billing_ctx or {}).get("claim_number", "the claim")
    provider = (billing_ctx or {}).get("provider_name", "our facility")

    greeting = (
        f"Hello, this is an AI assistant calling on behalf of {provider} from Medical Billing Solutions. "
        f"I am an automated system, not a human agent. "
        f"I'm calling regarding a denied insurance claim — claim number {claim_no}, denial code {denial_code}, "
        f"with {payer}. I'd like to speak with someone in your claims department. "
        "Are you able to assist me today?"
    )

    _call_contexts[call_sid] = CallContext(
        call_session_id=session_id,
        billing_context=billing_ctx,
        system_prompt=_build_system_prompt(billing_ctx),
    )

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            event = msg.get("event")

            if event == "connected":
                logger.info("twilio_stream_connected", call_sid=call_sid)

            elif event == "start":
                stream_sid = msg.get("start", {}).get("streamSid", "")
                _call_contexts[call_sid].stream_sid = stream_sid
                logger.info("stream_started", call_sid=call_sid, stream_sid=stream_sid)
                asyncio.create_task(_speak(call_sid, greeting))

                # Save greeting to DB
                if session_id:
                    _call_contexts[call_sid].transcript_seq += 1
                    async with AsyncSessionLocal() as db:
                        await _save_transcript(session_id, "agent", greeting, 1, db)
                        await db.commit()

            elif event == "media":
                ctx = _call_contexts.get(call_sid)
                if not ctx or ctx.handoff_requested:
                    continue
                payload = msg.get("media", {}).get("payload", "")
                frame = base64.b64decode(payload)

                if _frame_is_silence(frame):
                    ctx.silence_frames += 1
                    ctx.prolonged_silence_frames += 1

                    # 15-second silence → send fallback prompt once (Day 13 test)
                    if (
                        ctx.prolonged_silence_frames >= PROLONGED_SILENCE_FRAMES
                        and not ctx.is_processing
                        and not ctx.fallback_spoken
                    ):
                        from agent.prompts import FALLBACK_PHRASES
                        ctx.fallback_spoken = True
                        ctx.prolonged_silence_frames = 0
                        asyncio.create_task(_speak(call_sid, FALLBACK_PHRASES["silence"]))

                    if (ctx.silence_frames >= SILENCE_FRAMES_THRESHOLD
                            and ctx.speech_frames >= 5
                            and not ctx.is_processing):
                        asyncio.create_task(_run_pipeline(call_sid))
                else:
                    ctx.silence_frames = 0
                    ctx.prolonged_silence_frames = 0
                    ctx.fallback_spoken = False
                    ctx.speech_frames += 1
                    if not ctx.is_processing:
                        ctx.audio_frames.append(frame)

                if ctx.speech_frames >= MAX_BUFFER_FRAMES and not ctx.is_processing:
                    asyncio.create_task(_run_pipeline(call_sid))

            elif event == "dtmf":
                digit = msg.get("dtmf", {}).get("digit", "")
                logger.info("dtmf", call_sid=call_sid, digit=digit)

            elif event == "stop":
                logger.info("stream_stopped", call_sid=call_sid)
                break

    except WebSocketDisconnect:
        logger.info("media_stream_disconnected", call_sid=call_sid)
    except Exception as e:
        logger.error("media_stream_error", call_sid=call_sid, error=str(e))
    finally:
        ctx = _call_contexts.pop(call_sid, None)
        # Mark session completed if not already handled
        if ctx and ctx.call_session_id and not ctx.handoff_requested:
            await _update_session_outcome(
                ctx.call_session_id,
                CallOutcome.COMPLETED.value,
                "Call ended normally",
            )
        await ws_manager.disconnect(call_sid)


async def send_audio_to_stream(call_sid: str, stream_sid: str, audio_bytes: bytes) -> None:
    payload = base64.b64encode(audio_bytes).decode("utf-8")
    await ws_manager.send_json(call_sid, {
        "event": "media",
        "streamSid": stream_sid,
        "media": {"payload": payload},
    })


async def clear_audio_stream(call_sid: str, stream_sid: str) -> None:
    await ws_manager.send_json(call_sid, {"event": "clear", "streamSid": stream_sid})


