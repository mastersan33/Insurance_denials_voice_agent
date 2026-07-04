"""
Security headers middleware.

Adds OWASP-recommended HTTP security headers to every response:
- Strict-Transport-Security (HSTS)
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy
- Content-Security-Policy (strict, with WebSocket support)
- X-XSS-Protection (legacy browsers)
- Cache-Control on /api routes (no-store)
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"

        # Deny cross-domain Flash/PDF/Silverlight requests
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Legacy XSS filter
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Don't leak referrer to external sites
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # Content Security Policy
        # - default-src 'self'
        # - Allow inline styles (Tailwind injects), external fonts
        # - Allow WebSocket connections to same host (ws: + wss:)
        # - Upgrade insecure requests in production
        csp_parts = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",   # Vite injects inline scripts in dev
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: blob:",
            "connect-src 'self' ws: wss: https:",   # WebSocket + API calls
            "frame-ancestors 'none'",
        ]
        if settings.environment == "production":
            csp_parts.append("upgrade-insecure-requests")

        response.headers["Content-Security-Policy"] = "; ".join(csp_parts)

        # HSTS — only in production (prevents mixed-content loops in dev)
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # No caching for API responses (contains PII / auth tokens)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response
