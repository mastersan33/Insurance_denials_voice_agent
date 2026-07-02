from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser
from backend.app.core.exceptions import NotFoundException
from backend.app.db.session import get_db
from backend.app.models.billing_case import BillingCase
from backend.app.repositories.billing_case_repository import BillingCaseRepository
from backend.app.schemas.billing_case import (
    BillingCaseCreate,
    BillingCaseResponse,
    BillingCaseUpdate,
)

router = APIRouter()


@router.get("", response_model=list[BillingCaseResponse])
async def list_billing_cases(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    repo = BillingCaseRepository(db)
    if status:
        cases = await repo.get_by_status(status, skip, limit)
    else:
        cases = await repo.get_all(skip, limit)
    return [BillingCaseResponse.model_validate(c) for c in cases]


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
