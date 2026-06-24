from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.core.dependencies import get_admin
from app.core.tenant import get_company_id
from typing import Optional
from app.models.models import EventSeat, PublishedEvent, TicketSeatStatus, VenueTable
from app.schemas.palace_schemas import (
    PublishedEventCreate,
    PublishedEventResponse,
    PublishedEventUpdate,
    TicketSeatResponse,
)

router = APIRouter(prefix="/published-events", tags=["Published Events"])


def get_event_or_404(db: Session, event_id: int) -> PublishedEvent:
    event = (
        db.query(PublishedEvent)
        .options(joinedload(PublishedEvent.seats))
        .filter(PublishedEvent.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Evento nao encontrado")
    return event


def sync_event_seats(db: Session, event: PublishedEvent, table_ids: Optional[list[int]] = None):
    if event.seats:
        return
    if table_ids:
        tables = db.query(VenueTable).filter(VenueTable.id.in_(table_ids)).order_by(VenueTable.number.asc()).all()
    else:
        tables = db.query(VenueTable).filter(VenueTable.company_id == event.company_id).order_by(VenueTable.number.asc()).all()
    for table in tables:
        seat = EventSeat(
            event_id=event.id,
            table_id=table.id,
            table_number=table.number,
            x=table.x,
            y=table.y,
            capacity=table.capacity,
            location=table.location,
            price=table.area.ticket_price if table.area else event.base_price,
            status=TicketSeatStatus.available,
        )
        db.add(seat)


@router.get("", response_model=list[PublishedEventResponse])
@router.get("/", response_model=list[PublishedEventResponse])
def list_events(request: Request, db: Session = Depends(get_db)):
    company_id = get_company_id(request, db)
    return (
        db.query(PublishedEvent)
        .options(joinedload(PublishedEvent.seats))
        .filter(PublishedEvent.company_id == company_id)
        .order_by(PublishedEvent.date.desc())
        .all()
    )


@router.post("", response_model=PublishedEventResponse, status_code=201)
@router.post("/", response_model=PublishedEventResponse, status_code=201)
def create_event(
    payload: PublishedEventCreate,
    request: Request,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    company_id = get_company_id(request, db)
    table_ids = payload.table_ids
    event_data = payload.model_dump(exclude={'table_ids'})
    event = PublishedEvent(**event_data, company_id=company_id)
    db.add(event)
    db.commit()
    db.refresh(event)
    sync_event_seats(db, event, table_ids)
    db.commit()
    return get_event_or_404(db, event.id)


@router.patch("/{event_id}", response_model=PublishedEventResponse)
def update_event(
    event_id: int,
    payload: PublishedEventUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    event = get_event_or_404(db, event_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    return get_event_or_404(db, event.id)


@router.post("/{event_id}/publish", response_model=PublishedEventResponse)
def publish_event(event_id: int, db: Session = Depends(get_db), _admin=Depends(get_admin)):
    event = get_event_or_404(db, event_id)
    event.published = True
    sync_event_seats(db, event)
    db.commit()
    return get_event_or_404(db, event.id)


@router.post("/{event_id}/unpublish", response_model=PublishedEventResponse)
def unpublish_event(event_id: int, db: Session = Depends(get_db), _admin=Depends(get_admin)):
    event = get_event_or_404(db, event_id)
    event.published = False
    db.commit()
    return get_event_or_404(db, event.id)


@router.get("/{event_id}/seats", response_model=list[TicketSeatResponse])
def list_event_seats(event_id: int, db: Session = Depends(get_db)):
    event = get_event_or_404(db, event_id)
    return event.seats


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db), _admin=Depends(get_admin)):
    event = get_event_or_404(db, event_id)
    db.delete(event)
    db.commit()
    return {"message": "Evento eliminado com sucesso"}

@router.patch("/{event_id}/seats/{seat_id}")
def update_event_seat(
    event_id: int,
    seat_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    seat = db.query(EventSeat).filter(
        EventSeat.id == seat_id,
        EventSeat.event_id == event_id,
    ).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat nao encontrada")
    if 'x' in payload:
        seat.x = payload['x']
    if 'y' in payload:
        seat.y = payload['y']
    db.commit()
    return {"id": seat.id, "x": seat.x, "y": seat.y}