from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_admin, get_usuario_atual
from app.database import get_db
from app.models.models import PrivateEventRequest, Usuario
from app.schemas.palace_schemas import PrivateEventCreate, PrivateEventResponse, PrivateEventUpdate
from app.routers.auth_router import frontend_role
router = APIRouter(prefix="/events", tags=["Private Events"])


def to_response(event: PrivateEventRequest) -> PrivateEventResponse:
    return PrivateEventResponse(
        id=str(event.id),
        code=event.code,
        type=event.type,
        clientId=str(event.client_id),
        clientName=event.client.nome if event.client else f"Cliente #{event.client_id}",
        date=event.date,
        guests=event.guests,
        status=event.status,
        notes=event.notes,
        budget=event.budget,
        depositPaid=event.deposit_paid,
        createdAt=event.created_at,
    )


@router.get("", response_model=list[PrivateEventResponse])
@router.get("/", response_model=list[PrivateEventResponse])
def list_events(
    status: str | None = None,
    type: str | None = None,
    search: str | None = None,
    clientId: str | None = None,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    is_admin = frontend_role(usuario_atual.role) == "admin"
    query = db.query(PrivateEventRequest)

    if is_admin:
        if clientId:
            query = query.filter(PrivateEventRequest.client_id == clientId)
    else:
        query = query.filter(PrivateEventRequest.client_id == usuario_atual.id)

    if status:
        query = query.filter(PrivateEventRequest.status == status)
    if type:
        query = query.filter(PrivateEventRequest.type == type)

    events = [to_response(event) for event in query.order_by(PrivateEventRequest.date.asc()).all()]
    if search:
        q = search.lower()
        events = [
            event for event in events
            if q in event.code.lower() or q in event.client_name.lower()
        ]
    return events

@router.get("/my", response_model=list[PrivateEventResponse])
def my_events(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_usuario_atual)):
    events = (
        db.query(PrivateEventRequest)
        .filter(PrivateEventRequest.client_id == usuario_atual.id)
        .order_by(PrivateEventRequest.date.asc())
        .all()
    )
    return [to_response(event) for event in events]


@router.get("/{event_id}", response_model=PrivateEventResponse)
def get_event(event_id: int, db: Session = Depends(get_db), _user: Usuario = Depends(get_usuario_atual)):
    event = db.query(PrivateEventRequest).filter(PrivateEventRequest.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento nao encontrado")
    return to_response(event)


@router.post("", response_model=PrivateEventResponse, status_code=201)
@router.post("/", response_model=PrivateEventResponse, status_code=201)
def create_event(
    payload: PrivateEventCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    client_id = payload.client_id or usuario_atual.id
    client = db.query(Usuario).filter(Usuario.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")

    next_number = db.query(PrivateEventRequest).count() + 1
    event = PrivateEventRequest(
        code=f"EVT-{next_number:03d}",
        client_id=client.id,
        type=payload.type,
        date=payload.date,
        guests=payload.guests,
        notes=payload.notes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return to_response(event)


@router.patch("/{event_id}", response_model=PrivateEventResponse)
def update_event(
    event_id: int,
    payload: PrivateEventUpdate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin),
):
    event = db.query(PrivateEventRequest).filter(PrivateEventRequest.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento nao encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return to_response(event)
