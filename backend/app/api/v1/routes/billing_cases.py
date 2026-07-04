import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser, require_role
from backend.app.core.exceptions import NotFoundException
from backend.app.db.session import get_db
from backend.app.models.billing_case import BillingCase
from backend.app.repositories.billing_case_repository import BillingCaseRepository
from backend.app.schemas.billing_case import (
    BillingCaseCreate,
    BillingCaseResponse,
    BillingCaseUpdate,
    PaginatedResponse,
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[BillingCaseResponse])
async def list_billing_cases(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = Query(None, description="Search patient, claim, payer"),
    status: str | None = None,
    priority: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    repo = BillingCaseRepository(db)
    cases, total = await repo.search(q=q, status=status, priority=priority, skip=skip, limit=limit)
    return PaginatedResponse(
        items=[BillingCaseResponse.model_validate(c) for c in cases],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=BillingCaseResponse, status_code=201)
async def create_billing_case(
    data: BillingCaseCreate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = BillingCaseRepository(db)
    case = BillingCase(**data.model_dump())
    case = await repo.create(case)
    return BillingCaseResponse.model_validate(case)


@router.get("/{case_id}", response_model=BillingCaseResponse)
async def get_billing_case(
    case_id: str,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = BillingCaseRepository(db)
    case = await repo.get_by_id(case_id)
    if not case:
        raise NotFoundException("BillingCase", case_id)
    return BillingCaseResponse.model_validate(case)


@router.patch("/{case_id}", response_model=BillingCaseResponse)
async def update_billing_case(
    case_id: str,
    data: BillingCaseUpdate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = BillingCaseRepository(db)
    case = await repo.get_by_id(case_id)
    if not case:
        raise NotFoundException("BillingCase", case_id)
    case = await repo.update(case, data.model_dump(exclude_none=True))
    return BillingCaseResponse.model_validate(case)


@router.delete("/{case_id}", status_code=204, dependencies=[require_role("supervisor")])
async def delete_billing_case(
    case_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = BillingCaseRepository(db)
    case = await repo.get_by_id(case_id)
    if not case:
        raise NotFoundException("BillingCase", case_id)
    await repo.delete(case)


@router.post("/bulk-import", response_model=dict, status_code=201)
async def bulk_import_billing_cases(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
):
    """
    Import billing cases from a CSV file.
    Required columns: patient_name, payer_name, claim_number
    Optional: patient_dob, subscriber_id, payer_phone, denial_code, denial_reason,
              amount_billed, provider_name, provider_npi, priority, notes
    Max file size: 5 MB. Only text/csv and text/plain content types accepted.
    """
    # --- Security: validate content type and file size -----------------------
    _ALLOWED_CONTENT_TYPES = {"text/csv", "text/plain", "application/csv"}
    _MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

    if file.content_type and file.content_type.lower().split(";")[0].strip() not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are accepted (text/csv)",
        )

    content = await file.read(_MAX_UPLOAD_BYTES + 1)
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 5 MB upload limit",
        )
    # -------------------------------------------------------------------------
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    repo = BillingCaseRepository(db)
    created = 0
    errors: list[str] = []

    for i, row in enumerate(reader, start=2):  # row 1 is header
        try:
            data = BillingCaseCreate(
                patient_name=row.get("patient_name", "").strip(),
                payer_name=row.get("payer_name", "").strip(),
                claim_number=row.get("claim_number", "").strip(),
                patient_dob=row.get("patient_dob") or None,
                subscriber_id=row.get("subscriber_id") or None,
                payer_phone=row.get("payer_phone") or None,
                service_date=row.get("service_date") or None,
                cpt_codes=row.get("cpt_codes") or None,
                icd10_codes=row.get("icd10_codes") or None,
                amount_billed=float(row["amount_billed"]) if row.get("amount_billed") else None,
                denial_code=row.get("denial_code") or None,
                denial_reason=row.get("denial_reason") or None,
                provider_name=row.get("provider_name") or None,
                provider_npi=row.get("provider_npi") or None,
                priority=row.get("priority") or "normal",
                notes=row.get("notes") or None,
            )
            case = BillingCase(**data.model_dump())
            await repo.create(case)
            created += 1
        except Exception as exc:
            errors.append(f"Row {i}: {exc}")

    return {"created": created, "errors": errors}

