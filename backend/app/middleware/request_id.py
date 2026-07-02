import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request correlation ID to every request and response.

    If the client sends an ``X-Request-ID`` header it is reused; otherwise a
    new UUID4 is generated.  The ID is:
    - stored in ``request.state.request_id``
    - injected into structlog context vars so every log line for that request
      includes it automatically
    - returned to the client in the response header
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        import structlog

        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
