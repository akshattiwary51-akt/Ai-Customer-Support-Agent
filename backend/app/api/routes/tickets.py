from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models import SupportTicket, TicketEvent, User
from app.schemas import TicketCreate, TicketNoteCreate, TicketRead, TicketUpdate
from app.services.business_service import create_ticket

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def post_ticket(
    payload: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_ticket(
        db,
        current_user,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        category=payload.category,
        conversation_id=payload.conversation_id,
        escalation_reason=payload.escalation_reason,
    )


@router.get("", response_model=list[TicketRead])
def list_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    statement = select(SupportTicket)
    if current_user.role == "CUSTOMER":
        statement = statement.where(SupportTicket.customer_id == current_user.id)
    return db.execute(statement.order_by(SupportTicket.created_at.desc())).scalars().all()


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None or (current_user.role == "CUSTOMER" and ticket.customer_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    current_user: User = Depends(require_roles("SUPPORT_AGENT", "ADMIN")),
    db: Session = Depends(get_db),
):
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if payload.status:
        ticket.status = payload.status
    if payload.assigned_to_id is not None:
        ticket.assigned_to_id = payload.assigned_to_id
    db.add(TicketEvent(ticket_id=ticket.id, actor_id=current_user.id, event_type="UPDATED", note="Ticket updated"))
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/notes")
def add_ticket_note(
    ticket_id: int,
    payload: TicketNoteCreate,
    current_user: User = Depends(require_roles("SUPPORT_AGENT", "ADMIN")),
    db: Session = Depends(get_db),
):
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    event = TicketEvent(ticket_id=ticket.id, actor_id=current_user.id, event_type="NOTE", note=payload.note)
    db.add(event)
    db.commit()
    return {"status": "created", "note_id": event.id}
