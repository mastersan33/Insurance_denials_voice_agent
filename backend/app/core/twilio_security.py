"""Twilio request signature validation.

Every POST from Twilio to our webhooks is signed with our auth token.
This module provides a FastAPI dependency that validates the signature
and returns HTTP 403 if the request is not from Twilio.

Day 4 / Day 14 requirement:
  "Send a fake POST to /twilio/voice with curl (no signature) — must get 403"
"""
from fastapi import Depends, HTTPException, Request, status
from twilio.request_validator import RequestValidator

from backend.app.config.settings import settings


async def _get_request_body(request: Request) -> bytes:
    """Cache body so it can be read by both the validator and the route handler."""
    body = await request.body()
    # Store so request.form() can still read it downstream
    request._body = body  # type: ignore[attr-defined]
    return body


async def validate_twilio_signature(
    request: Request,
    _body: bytes = Depends(_get_request_body),
) -> None:
    """FastAPI dependency — raises 403 if the request lacks a valid Twilio signature.

    Twilio docs: https://www.twilio.com/docs/usage/webhooks/webhooks-security
    """
    if not settings.twilio_auth_token:
        # Auth token not configured (local dev without Twilio) — skip validation
        return

    validator = RequestValidator(settings.twilio_auth_token)

    # Reconstruct the full URL Twilio signed — use X-Forwarded-Proto if behind a proxy
    proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.headers.get("host", request.url.netloc))
    url = f"{proto}://{host}{request.url.path}"
    if request.url.query:
        url += f"?{request.url.query}"

    signature = request.headers.get("X-Twilio-Signature", "")

    # Parse form fields for signature computation
    form_data: dict = {}
    try:
        form = await request.form()
        form_data = dict(form)
    except Exception:
        pass

    if not validator.validate(url, form_data, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature",
        )


# Convenience type alias for route injection
TwilioSignatureCheck = Depends(validate_twilio_signature)
