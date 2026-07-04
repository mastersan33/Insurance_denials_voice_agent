"""CSV/JSON report export endpoints.

All export endpoints require `supervisor` or higher role — they stream raw
patient / financial data and must not be accessible to operators or viewers.

Row cap: 10 000 rows per export to prevent memory exhaustion.  If more rows
are needed, consumers must paginate via the `skip` / `limit` parameters.
"""
import csv
import io
import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser, require_role
from backend.app.db.session import get_db
from backend.app.models.billing_case import BillingCase
from backend.app.models.call_job import CallJob
from backend.app.models.call_session import CallSession
from backend.app.models.transcript import Transcript
from backend.app.services.audit_service import audit

_MAX_EXPORT_ROWS = 10_000

router = APIRouter()


def _csv_response(rows: list[dict], filename: str) -> StreamingResponse:
    if not rows:
        return StreamingResponse(
            iter([""]), media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/billing-cases")
async def export_billing_cases(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_role("supervisor")] = None,
    fmt: str = Query("csv", regex="^(csv|json)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(_MAX_EXPORT_ROWS, ge=1, le=_MAX_EXPORT_ROWS),
):
    result = await db.execute(
        select(BillingCase).order_by(BillingCase.created_at.desc()).offset(skip).limit(limit)
    )
    cases = result.scalars().all()
    rows = [
        {
            "id": c.id,
            "patient_name": c.patient_name,
            "payer_name": c.payer_name,
            "claim_number": c.claim_number,
            "denial_code": c.denial_code or "",
            "denial_reason": c.denial_reason or "",
            "amount_billed": c.amount_billed or "",
            "status": c.status,
            "priority": c.priority,
            "created_at": c.created_at.isoformat() if c.created_at else "",
        }
        for c in cases
    ]
    audit("report.export", actor=user, resource_type="BillingCase", detail=f"fmt={fmt} count={len(rows)}")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if fmt == "json":
        return Response(content=json.dumps(rows), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="billing_cases_{ts}.json"'})
    return _csv_response(rows, f"billing_cases_{ts}.csv")


@router.get("/calls")
async def export_calls(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_role("supervisor")] = None,
    fmt: str = Query("csv", regex="^(csv|json)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(_MAX_EXPORT_ROWS, ge=1, le=_MAX_EXPORT_ROWS),
):
    result = await db.execute(
        select(CallJob).order_by(CallJob.created_at.desc()).offset(skip).limit(limit)
    )
    jobs = result.scalars().all()
    rows = [
        {
            "id": j.id,
            "billing_case_id": j.billing_case_id,
            "phone_number": j.phone_number,
            "status": j.status,
            "priority": j.priority,
            "attempt_count": j.attempt_count,
            "outcome": j.outcome or "",
            "created_at": j.created_at.isoformat() if j.created_at else "",
        }
        for j in jobs
    ]
    audit("report.export", actor=user, resource_type="CallJob", detail=f"fmt={fmt} count={len(rows)}")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if fmt == "json":
        return Response(content=json.dumps(rows), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="calls_{ts}.json"'})
    return _csv_response(rows, f"calls_{ts}.csv")


@router.get("/transcripts")
async def export_transcripts(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_role("supervisor")] = None,
    session_id: str | None = None,
    fmt: str = Query("csv", regex="^(csv|json)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(_MAX_EXPORT_ROWS, ge=1, le=_MAX_EXPORT_ROWS),
):
    stmt = (
        select(Transcript)
        .order_by(Transcript.call_session_id, Transcript.sequence_number)
        .offset(skip)
        .limit(limit)
    )
    if session_id:
        stmt = stmt.where(Transcript.call_session_id == session_id)
    result = await db.execute(stmt)
    turns = result.scalars().all()
    rows = [
        {
            "id": t.id,
            "call_session_id": t.call_session_id,
            "speaker": t.speaker,
            "content": t.content,
            "sequence_number": t.sequence_number,
            "created_at": t.created_at.isoformat() if t.created_at else "",
        }
        for t in turns
    ]
    audit("report.export", actor=user, resource_type="Transcript", detail=f"fmt={fmt} count={len(rows)}")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if fmt == "json":
        return Response(content=json.dumps(rows), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="transcripts_{ts}.json"'})
    return _csv_response(rows, f"transcripts_{ts}.csv")
