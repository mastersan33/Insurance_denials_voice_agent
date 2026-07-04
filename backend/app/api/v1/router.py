from fastapi import APIRouter

from backend.app.api.v1.routes import (
    analytics,
    audit,
    auth,
    billing_cases,
    call_jobs,
    calls,
    dashboard,
    health,
    human_handoff,
    reports,
    tickets,
    transcripts,
    twilio_webhooks,
    users,
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
api_router.include_router(human_handoff.router, prefix="/human-handoff", tags=["Human Handoff"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(twilio_webhooks.router, prefix="/twilio", tags=["Twilio Webhooks"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
