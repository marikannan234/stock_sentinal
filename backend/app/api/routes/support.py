"""
Support ticket management endpoints.
"""

import logging
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.models.trading import SupportTicket
from app.schemas.trading import (
    SupportTicketCreate,
    SupportTicketRead,
    SupportTicketUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/support", tags=["support"])


@router.post("/ticket", response_model=SupportTicketRead, status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    ticket_create: SupportTicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> SupportTicket:
    """Create a new support ticket."""
    logger.info(f"Support ticket create requested by user {current_user.id}")
    ticket = SupportTicket(
        user_id=current_user.id,
        subject=(ticket_create.subject or "Support Request").strip(),
        message=(ticket_create.message or "No details provided.").strip(),
        status="open",
        priority=ticket_create.priority or "medium",
        created_at=datetime.utcnow(),
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    logger.info(f"Support ticket {ticket.id} created by user {current_user.id}")
    return ticket


@router.get("/tickets", response_model=List[SupportTicketRead])
def list_user_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    status_filter: str = None,
) -> List[SupportTicket]:
    """Get all support tickets for current user."""
    logger.info(f"Support tickets requested by user {current_user.id}")
    query = db.query(SupportTicket).filter(
        SupportTicket.user_id == current_user.id
    )
    
    if status_filter:
        query = query.filter(SupportTicket.status == status_filter)
    
    tickets = query.order_by(SupportTicket.created_at.desc()).all()
    return tickets


@router.get("/ticket/{ticket_id}", response_model=SupportTicketRead)
def get_support_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> SupportTicket:
    """Get a specific support ticket."""
    logger.info(f"Support ticket {ticket_id} requested by user {current_user.id}")
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found",
        )
    
    return ticket


@router.put("/ticket/{ticket_id}", response_model=SupportTicketRead)
def update_support_ticket(
    ticket_id: int,
    ticket_update: SupportTicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> SupportTicket:
    """Update a support ticket."""
    logger.info(f"Support ticket update requested for {ticket_id} by user {current_user.id}")
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found",
        )
    
    update_data = ticket_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:
            setattr(ticket, field, value)
    
    ticket.updated_at = datetime.utcnow()
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    logger.info(f"Support ticket {ticket.id} updated by user {current_user.id}")
    return ticket


@router.delete("/ticket/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_support_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> None:
    """Delete a support ticket."""
    logger.info(f"Support ticket delete requested for {ticket_id} by user {current_user.id}")
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found",
        )
    
    db.delete(ticket)
    db.commit()
    
    logger.info(f"Support ticket {ticket.id} deleted by user {current_user.id}")
