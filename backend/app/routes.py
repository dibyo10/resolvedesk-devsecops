from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from . import services
from .db import get_db
from .schemas import Priority, StatsOut, Status, TicketCreate, TicketOut, TicketUpdate

router = APIRouter(prefix="/api/tickets", tags=["tickets"])
Database = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[TicketOut])
def list_tickets(
    db: Database,
    search: str = Query(default="", max_length=200),
    status: Status | None = None,
    priority: Priority | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return services.list_tickets(db, search.strip(), status, priority, limit, offset)


@router.get("/stats", response_model=StatsOut)
def stats(db: Database):
    return services.ticket_stats(db)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Database):
    return services.find_ticket(db, ticket_id)


@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(payload: TicketCreate, db: Database):
    return services.create_ticket(db, payload)


@router.put("/{ticket_id}", response_model=TicketOut)
@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Database):
    return services.update_ticket(db, ticket_id, payload)


@router.delete("/{ticket_id}", status_code=204)
def delete_ticket(ticket_id: int, db: Database):
    services.delete_ticket(db, ticket_id)
    return Response(status_code=204)
