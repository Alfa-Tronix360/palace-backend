from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_admin, get_usuario_atual
from app.models.models import PalaceReservation, StatusReserva, Usuario, VenueTable
from app.schemas.palace_schemas import (
    ReservationApiCreate,
    ReservationApiResponse,
    ReservationApiUpdate,
)
from app.routers.auth_router import frontend_role
router = APIRouter(prefix="/reservations", tags=["Reservations API"])


STATUS_TO_API = {
    StatusReserva.pendente: "pending",
    StatusReserva.confirmada: "confirmed",
    StatusReserva.in_service: "in_service",
    StatusReserva.completed: "completed",
    StatusReserva.cancelada: "cancelled",
}

STATUS_FROM_API = {
    "pending": StatusReserva.pendente,
    "confirmed": StatusReserva.confirmada,
    "in_service": StatusReserva.in_service,
    "completed": StatusReserva.completed,
    "cancelled": StatusReserva.cancelada,
}


def combine_date_time(date: datetime, time: str) -> datetime:
    hours, minutes = [int(part) for part in time.split(":")[:2]]
    return date.replace(hour=hours, minute=minutes, second=0, microsecond=0)


def to_response(reserva: PalaceReservation) -> ReservationApiResponse:
    client_name = reserva.client.nome if reserva.client else f"Cliente #{reserva.client_id}"
    table_number = reserva.table.number if reserva.table else reserva.table_id
    return ReservationApiResponse(
        id=str(reserva.id),
        code=f"RAO-{reserva.id:04d}",
        clientId=str(reserva.client_id),
        clientName=client_name,
        tableId=str(reserva.table_id),
        tableNumber=table_number,
        date=reserva.starts_at,
        time=reserva.starts_at.strftime("%H:%M"),
        guests=reserva.guests,
        status=STATUS_TO_API.get(reserva.status, "pending"),
        notes=reserva.notes,
        createdAt=reserva.created_at,
    )


def ensure_available(db: Session, table_id: int, starts_at: datetime, ends_at: datetime, ignore_id: int | None = None):
    table = db.query(VenueTable).filter(VenueTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Mesa nao encontrada")

    query = (
        db.query(PalaceReservation)
        .filter(PalaceReservation.table_id == table_id)
        .filter(PalaceReservation.status != StatusReserva.cancelada)
        .filter(PalaceReservation.starts_at < ends_at)
        .filter(PalaceReservation.ends_at > starts_at)
    )
    if ignore_id:
        query = query.filter(PalaceReservation.id != ignore_id)
    if query.first():
        raise HTTPException(status_code=409, detail="Mesa indisponivel neste horario")


@router.get("", response_model=list[ReservationApiResponse])
@router.get("/", response_model=list[ReservationApiResponse])
def list_reservations(
    clientId: str | None = None,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    is_admin = frontend_role(usuario_atual.role) == "admin"
    query = db.query(PalaceReservation)

    if is_admin:
        if clientId:
            query = query.filter(PalaceReservation.client_id == clientId)
    else:
        query = query.filter(PalaceReservation.client_id == usuario_atual.id)

    reservas = query.order_by(PalaceReservation.starts_at.desc()).all()
    return [to_response(reserva) for reserva in reservas]

@router.get("/my", response_model=list[ReservationApiResponse])
def my_reservations(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_usuario_atual)):
    reservas = (
        db.query(PalaceReservation)
        .filter(PalaceReservation.client_id == usuario_atual.id)
        .order_by(PalaceReservation.starts_at.desc())
        .all()
    )
    return [to_response(reserva) for reserva in reservas]


@router.get("/{reservation_id}", response_model=ReservationApiResponse)
def get_reservation(reservation_id: int, db: Session = Depends(get_db), _user: Usuario = Depends(get_usuario_atual)):
    reserva = db.query(PalaceReservation).filter(PalaceReservation.id == reservation_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva nao encontrada")
    return to_response(reserva)


@router.post("", response_model=ReservationApiResponse, status_code=201)
@router.post("/", response_model=ReservationApiResponse, status_code=201)
def create_reservation(
    payload: ReservationApiCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    starts_at = combine_date_time(payload.date, payload.time)
    ends_at = starts_at + timedelta(hours=2)
    ensure_available(db, payload.tableId, starts_at, ends_at)

    client = db.query(Usuario).filter(Usuario.id == (payload.clientId or usuario_atual.id)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")

    reserva = PalaceReservation(
        client_id=client.id,
        table_id=payload.tableId,
        starts_at=starts_at,
        ends_at=ends_at,
        guests=payload.guests,
        status=StatusReserva.pendente,
        notes=payload.notes,
    )
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return to_response(reserva)


@router.patch("/{reservation_id}", response_model=ReservationApiResponse)
def update_reservation(
    reservation_id: int,
    payload: ReservationApiUpdate,
    db: Session = Depends(get_db),
    _user: Usuario = Depends(get_usuario_atual),
):
    reserva = db.query(PalaceReservation).filter(PalaceReservation.id == reservation_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva nao encontrada")

    table_id = payload.tableId or reserva.table_id
    date = payload.date or reserva.starts_at
    time = payload.time or reserva.starts_at.strftime("%H:%M")
    starts_at = combine_date_time(date, time)
    ends_at = starts_at + timedelta(hours=2)
    ensure_available(db, table_id, starts_at, ends_at, ignore_id=reserva.id)

    reserva.table_id = table_id
    reserva.starts_at = starts_at
    reserva.ends_at = ends_at
    reserva.guests = payload.guests if payload.guests is not None else reserva.guests
    reserva.notes = payload.notes if payload.notes is not None else reserva.notes
    if payload.status:
        reserva.status = STATUS_FROM_API.get(payload.status, reserva.status)
    db.commit()
    db.refresh(reserva)
    return to_response(reserva)


@router.post("/{reservation_id}/cancel", response_model=ReservationApiResponse)
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db), _user: Usuario = Depends(get_usuario_atual)):
    reserva = db.query(PalaceReservation).filter(PalaceReservation.id == reservation_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva nao encontrada")
    reserva.status = StatusReserva.cancelada
    db.commit()
    db.refresh(reserva)
    return to_response(reserva)


@router.post("/{reservation_id}/confirm", response_model=ReservationApiResponse)
def confirm_reservation(reservation_id: int, db: Session = Depends(get_db), _admin: Usuario = Depends(get_admin)):
    reserva = db.query(PalaceReservation).filter(PalaceReservation.id == reservation_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva nao encontrada")
    reserva.status = StatusReserva.confirmada
    db.commit()
    db.refresh(reserva)
    return to_response(reserva)
