from datetime import datetime
from urllib.parse import quote
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_usuario_atual, get_staff
from app.models.models import (
    DigitalTicket,
    EventSeat,
    PublishedEvent,
    TicketScan,
    TicketSeatStatus,
    TicketStatus,
    Usuario,
)
from app.schemas.palace_schemas import (
    DigitalTicketResponse,
    TicketPurchaseCreate,
    TicketScanResponse,
    TicketValidateCreate,
    TicketValidationResponse,
    TicketWhatsAppSendCreate,
    TicketWhatsAppSendResponse,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def make_qr_code() -> str:
    return f"PL-{uuid4().hex}"


def build_whatsapp_url(ticket: DigitalTicket, phone: str | None = None) -> str | None:
    digits = "".join(ch for ch in (phone or ticket.client.telefone or "") if ch.isdigit())
    if not digits:
        return None
    message = "\n".join(
        [
            "Convite digital Palace Lounge",
            f"Evento: {ticket.event.title if ticket.event else ticket.event_id}",
            f"Mesa: {ticket.seat.table_number if ticket.seat else ticket.seat_id}",
            f"Codigo QR: {ticket.qr_code}",
        ]
    )
    return f"https://wa.me/{digits}?text={quote(message)}"


def ticket_to_response(ticket: DigitalTicket, delivery_status: str = "pending", phone: str | None = None) -> dict:
    return {
        "id": ticket.id,
        "event_id": ticket.event_id,
        "client_id": ticket.client_id,
        "client_name": ticket.client.nome if ticket.client else f"Cliente #{ticket.client_id}",
        "client_phone": phone or (ticket.client.telefone if ticket.client else None),
        "seat_id": ticket.seat_id,
        "table_number": ticket.seat.table_number if ticket.seat else ticket.seat_id,
        "price": ticket.price,
        "qr_code": ticket.qr_code,
        "whatsapp_url": build_whatsapp_url(ticket, phone),
        "delivery_status": delivery_status,
        "status": ticket.status,
        "used_at": ticket.used_at,
        "purchased_at": ticket.purchased_at,
    }


@router.post("/purchase", response_model=DigitalTicketResponse, status_code=201)
def purchase_ticket(
    payload: TicketPurchaseCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    event = db.query(PublishedEvent).filter(PublishedEvent.id == payload.event_id).first()
    if not event or not event.published:
        raise HTTPException(status_code=404, detail="Evento publicado nao encontrado")

    seat = (
        db.query(EventSeat)
        .filter(EventSeat.id == payload.seat_id)
        .filter(EventSeat.event_id == payload.event_id)
        .first()
    )
    if not seat:
        raise HTTPException(status_code=404, detail="Lugar nao encontrado")
    if seat.status != TicketSeatStatus.available:
        raise HTTPException(status_code=400, detail="Lugar indisponivel")

    ticket = DigitalTicket(
        event_id=event.id,
        client_id=usuario_atual.id,
        seat_id=seat.id,
        price=seat.price,
        qr_code=make_qr_code(),
        status=TicketStatus.valid,
    )
    seat.status = TicketSeatStatus.sold
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket_to_response(ticket)

@router.get("/all", response_model=list[DigitalTicketResponse])
def all_tickets(
    db: Session = Depends(get_db),
    _staff: Usuario = Depends(get_staff),
):
    tickets = (
        db.query(DigitalTicket)
        .order_by(DigitalTicket.purchased_at.desc())
        .all()
    )
    return [ticket_to_response(ticket) for ticket in tickets]


@router.get("/my", response_model=list[DigitalTicketResponse])
def my_tickets(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    tickets = (
        db.query(DigitalTicket)
        .filter(DigitalTicket.client_id == usuario_atual.id)
        .order_by(DigitalTicket.purchased_at.desc())
        .all()
    )
    return [ticket_to_response(ticket) for ticket in tickets]


@router.post("/{ticket_id}/send-whatsapp", response_model=TicketWhatsAppSendResponse)
def send_ticket_whatsapp(
    ticket_id: int,
    payload: TicketWhatsAppSendCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    ticket = db.query(DigitalTicket).filter(DigitalTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket nao encontrado")
    if ticket.client_id != usuario_atual.id:
        raise HTTPException(status_code=403, detail="Sem permissao para enviar este ticket")

    digits = "".join(ch for ch in payload.phone if ch.isdigit())
    if not digits:
        raise HTTPException(status_code=400, detail="Telefone invalido")

    return ticket_to_response(ticket, delivery_status="sent", phone=payload.phone)


@router.post("/validate", response_model=TicketValidationResponse)
def validate_ticket(
    payload: TicketValidateCreate,
    db: Session = Depends(get_db),
    staff: Usuario = Depends(get_staff),
):
    ticket = db.query(DigitalTicket).filter(DigitalTicket.qr_code == payload.qr_code).first()
    if not ticket:
        scan = TicketScan(ticket_id=0, staff_id=staff.id, event_id=0, result="not_found")
        # Cannot persist ticket_id=0 because of FK. Return without scan row.
        return TicketValidationResponse(valid=False, message="Ticket nao encontrado")

    if ticket.status != TicketStatus.valid:
        scan = TicketScan(
            ticket_id=ticket.id,
            staff_id=staff.id,
            event_id=ticket.event_id,
            result=ticket.status.value,
        )
        db.add(scan)
        db.commit()
        return TicketValidationResponse(valid=False, message="Ticket ja utilizado ou cancelado", ticket=ticket_to_response(ticket))

    ticket.status = TicketStatus.used
    ticket.used_at = datetime.utcnow()
    scan = TicketScan(
        ticket_id=ticket.id,
        staff_id=staff.id,
        event_id=ticket.event_id,
        result="valid",
    )
    db.add(scan)
    db.commit()
    db.refresh(ticket)
    return TicketValidationResponse(valid=True, message="Ticket validado com sucesso", ticket=ticket_to_response(ticket))


@router.get("/scan-history", response_model=list[TicketScanResponse])
def scan_history(
    eventId: int | None = None,
    db: Session = Depends(get_db),
    _staff: Usuario = Depends(get_staff),
):
    query = db.query(TicketScan)
    if eventId:
        query = query.filter(TicketScan.event_id == eventId)
    return query.order_by(TicketScan.scanned_at.desc()).all()
