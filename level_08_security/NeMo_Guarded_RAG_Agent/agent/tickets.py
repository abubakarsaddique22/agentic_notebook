# SQLAlchemy DeclarativeBase maps ORM models; Session provides transactional DB operations.
# select(Ticket) makes typed SQL query; approved status is a DB decision, NOT an external action execution.
"""Human approval state machine; SQLAlchemy ORM + SQLite for local training persistence."""
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, DateTime, select  # ORM/db commands.
from sqlalchemy.orm import DeclarativeBase, Session  # ORM base + transactional sessions.
from settings import ROOT
from agent.identity import Principal, can_approve, can_request_ticket

class Base(DeclarativeBase):
    pass

class Ticket(Base):
    __tablename__ = 'pending_support_tickets'
    id = Column(Integer, primary_key=True)
    requested_by = Column(String(120), nullable=False)
    title = Column(String(120), nullable=False)
    description = Column(String(1200), nullable=False)
    status = Column(String(24), nullable=False, default='pending')
    reviewer = Column(String(120), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

DB_PATH = ROOT / 'state' / 'approval.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f'sqlite:///{DB_PATH.as_posix()}', future=True)

def init_db():
    Base.metadata.create_all(engine)

def request_ticket(principal: Principal, title: str, description: str) -> int:
    """Authorized operator may REQUEST ticket only, cannot approve/execute it."""
    if not can_request_ticket(principal): raise PermissionError('role cannot request tickets')
    init_db()
    with Session(engine) as db:
        record = Ticket(requested_by=principal.user_id, title=title, description=description, status='pending')
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.id

def list_tickets(principal: Principal):
    if not can_approve(principal): raise PermissionError('admin required')
    init_db()
    with Session(engine) as db:
        return [{'id': t.id, 'status':t.status, 'title':t.title,'requested_by':t.requested_by} for t in db.scalars(select(Ticket).order_by(Ticket.id)).all()]

def decide_ticket(principal: Principal, ticket_id: int, approve: bool) -> str:
    """Approve/reject a pending ticket only; no external mail/network execution."""
    if not can_approve(principal): raise PermissionError('admin required')
    init_db()
    with Session(engine) as db:
        ticket = db.get(Ticket, ticket_id)
        if ticket is None: raise LookupError('ticket not found')
        if ticket.status != 'pending': raise ValueError('ticket already reviewed')
        if ticket.requested_by == principal.user_id: raise PermissionError('four-eyes: cannot self-approve')
        ticket.status = 'approved' if approve else 'rejected'
        ticket.reviewer = principal.user_id
        ticket.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        return ticket.status
