from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser
from backend.app.core.exceptions import NotFoundException
from backend.app.db.session import get_db
from backend.app.models.ticket import Ticket
from backend.app.repositories.ticket_repository import TicketRepository
from backend.app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate

router = APIRouter()


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    repo = TicketRepository(db)
    if status:
        tickets = await repo.get_by_status(status, skip, limit)
    else:
        tickets = await repo.get_all(skip, limit)
    return [TicketResponse.model_validate(t) for t in tickets]


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    data: TicketCreate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = TicketRepository(db)
    ticket = Ticket(**data.model_dump())
    ticket = await repo.create(ticket)
    return TicketResponse.model_validate(ticket)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = TicketRepository(db)
    ticket = await repo.get_by_id(ticket_id)
    if not ticket:
        raise NotFoundException("Ticket", ticket_id)
    return TicketResponse.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    data: TicketUpdate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = TicketRepository(db)
    ticket = await repo.get_by_id(ticket_id)
    if not ticket:
        raise NotFoundException("Ticket", ticket_id)
    ticket = await repo.update(ticket, data.model_dump(exclude_none=True))
    return TicketResponse.model_validate(ticket)
