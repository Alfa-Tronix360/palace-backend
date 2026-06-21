from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.core.dependencies import get_admin
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


def sync_event_seats(db: Session, event: PublishedEvent):
    if event.seats:
        return

    tables = db.query(VenueTable).order_by(VenueTable.number.asc()).all()
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
def list_events(db: Session = Depends(get_db)):
    return (
        db.query(PublishedEvent)
        .options(joinedload(PublishedEvent.seats))
        .order_by(PublishedEvent.date.desc())
        .all()
    )


@router.post("", response_model=PublishedEventResponse, status_code=201)
@router.post("/", response_model=PublishedEventResponse, status_code=201)
def create_event(
    payload: PublishedEventCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    event = PublishedEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
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