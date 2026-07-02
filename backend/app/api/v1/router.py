from fastapi import APIRouter

from backend.app.api.v1.routes import (
    auth,
    billing_cases,
    call_jobs,
    calls,
    dashboard,
    health,
    tickets,
    transcripts,
    twilio_webhooks,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(billing_cases.router, prefix="/billing-cases", tags=["Billing Cases"])
api_router.include_router(call_jobs.router, prefix="/call-jobs", tags=["Call Jobs"])
api_router.include_router(calls.router, prefix="/calls", tags=["Calls"])
api_router.include_router(transcripts.router, prefix="/transcripts", tags=["Transcripts"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
api_router.include_router(twilio_webhooks.router, prefix="/twilio", tags=["Twilio Webhooks"])
