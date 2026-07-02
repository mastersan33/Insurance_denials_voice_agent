from twilio.rest import Client as TwilioRestClient

from backend.app.config.logging import get_logger
from backend.app.config.settings import settings

logger = get_logger(__name__)


class TwilioClient:
    def __init__(self):
        self._client: TwilioRestClient | None = None

    @property
    def client(self) -> TwilioRestClient:
        if self._client is None:
            self._client = TwilioRestClient(
                settings.twilio_account_sid,
                settings.twilio_auth_token,
            )
        return self._client

    async def initiate_call(
        self,
        to_number: str,
        call_sid_callback: str | None = None,
    ) -> str:
        """Initiate an outbound call. Returns the Call SID."""
        base_url = settings.twilio_webhook_base_url

        call = self.client.calls.create(
            to=to_number,
            from_=settings.twilio_phone_number,
            url=f"{base_url}/api/v1/twilio/voice/answer",
            status_callback=f"{base_url}/api/v1/twilio/voice/status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            status_callback_method="POST",
            record=True,
            recording_status_callback=f"{base_url}/api/v1/twilio/voice/recording",
        )

        logger.info("call_initiated", call_sid=call.sid, to=to_number)
        return call.sid

    async def end_call(self, call_sid: str) -> None:
        """End an active call."""
        self.client.calls(call_sid).update(status="completed")
        logger.info("call_ended", call_sid=call_sid)

    async def send_dtmf(self, call_sid: str, digits: str) -> None:
        """Send DTMF tones during a call."""
        self.client.calls(call_sid).update(
            twiml=f'<Response><Play digits="{digits}"/><Connect><Stream url="wss://{settings.twilio_webhook_base_url.replace("https://", "").replace("http://", "")}/api/v1/twilio/media-stream/{call_sid}"/></Connect></Response>'
        )
        logger.info("dtmf_sent", call_sid=call_sid, digits=digits)


twilio_client = TwilioClient()
