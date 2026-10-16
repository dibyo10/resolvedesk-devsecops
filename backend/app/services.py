from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .models import Ticket
from .schemas import StatsOut, TicketCreate, TicketUpdate


def find_ticket(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def list_tickets(
    db: Session,
    search: str,
    status: str | None,
    priority: str | None,
    limit: int,
    offset: int,
):
    query = select(Ticket)
    if search:
        query = query.where(
            or_(
                Ticket.subject.icontains(search, autoescape=True),
                Ticket.description.icontains(search, autoescape=True),
                Ticket.requester_email.icontains(search, autoescape=True),
            )
        )
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    return list(
        db.scalars(query.order_by(Ticket.id.desc()).offset(offset).limit(limit))
    )


def ticket_stats(db: Session) -> StatsOut:
    rows = db.execute(
        select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
    )
    counts = dict(rows.all())
    urgent = db.scalar(
        select(func.count(Ticket.id)).where(
            Ticket.priority == "URGENT", Ticket.status != "RESOLVED"
        )
    )
    return StatsOut(
        total=sum(counts.values()),
        open=counts.get("OPEN", 0),
        inProgress=counts.get("IN_PROGRESS", 0),
        resolved=counts.get("RESOLVED", 0),
        urgent=urgent,
    )


def create_ticket(db: Session, payload: TicketCreate) -> Ticket:
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(db: Session, ticket_id: int, payload: TicketUpdate) -> Ticket:
    ticket = find_ticket(db, ticket_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket


def delete_ticket(db: Session, ticket_id: int) -> None:
    db.delete(find_ticket(db, ticket_id))
    db.commit()
