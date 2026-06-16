from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_admin, get_usuario_atual
from app.models.models import PalaceReservation, StatusReserva, VenueArea, VenueTable, TableStatus
from app.schemas.palace_schemas import (
    VenueAreaCreate,
    VenueAreaResponse,
    VenueAreaUpdate,
    VenueTableCreate,
    VenueTableResponse,
    VenueTableUpdate,
)

router = APIRouter(prefix="/venue", tags=["Venue"])


def apply_updates(model, data):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(model, field, value)
    return model


@router.get("/areas", response_model=list[VenueAreaResponse])
def list_areas(db: Session = Depends(get_db)):
    return db.query(VenueArea).order_by(VenueArea.id.asc()).all()


@router.post("/areas", response_model=VenueAreaResponse, status_code=201)
def create_area(
    payload: VenueAreaCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    area = VenueArea(**payload.model_dump())
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


@router.patch("/areas/{area_id}", response_model=VenueAreaResponse)
def update_area(
    area_id: int,
    payload: VenueAreaUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    area = db.query(VenueArea).filter(VenueArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area nao encontrada")
    apply_updates(area, payload)
    db.commit()
    db.refresh(area)
    return area


@router.delete("/areas/{area_id}")
def delete_area(area_id: int, db: Session = Depends(get_db), _admin=Depends(get_admin)):
    area = db.query(VenueArea).filter(VenueArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area nao encontrada")
    db.delete(area)
    db.commit()
    return {"message": "Area removida com sucesso"}


@router.get("/tables", response_model=list[VenueTableResponse])
def list_tables(db: Session = Depends(get_db)):
    return db.query(VenueTable).order_by(VenueTable.number.asc()).all()


@router.post("/tables", response_model=VenueTableResponse, status_code=201)
def create_table(
    payload: VenueTableCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    exists = db.query(VenueTable).filter(VenueTable.number == payload.number).first()
    if exists:
        raise HTTPException(status_code=400, detail="Numero de mesa ja existe")
    table = VenueTable(**payload.model_dump())
    db.add(table)
    db.commit()
    db.refresh(table)
    return table


@router.get("/tables/availability", response_model=list[VenueTableResponse])
def table_availability(
    date: str,
    time: str,
    guests: int,
    db: Session = Depends(get_db),
):
    starts_at = datetime.fromisoformat(f"{date}T{time}")
    ends_at = starts_at + timedelta(hours=2)
    busy_table_ids = (
        db.query(PalaceReservation.table_id)
        .filter(PalaceReservation.status != StatusReserva.cancelada)
        .filter(PalaceReservation.starts_at < ends_at)
        .filter(PalaceReservation.ends_at > starts_at)
        .subquery()
    )
    return (
        db.query(VenueTable)
        .filter(VenueTable.status == TableStatus.available)
        .filter(VenueTable.capacity >= guests)
        .filter(VenueTable.id.not_in(busy_table_ids))
        .order_by(VenueTable.capacity.asc(), VenueTable.number.asc())
        .all()
    )


@router.patch("/tables/{table_id}", response_model=VenueTableResponse)
def update_table(
    table_id: int,
    payload: VenueTableUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_usuario_atual),  # ← muda aqui
):
    table = db.query(VenueTable).filter(VenueTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Mesa nao encontrada")
    apply_updates(table, payload)
    db.commit()
    db.refresh(table)
    return table


@router.delete("/tables/{table_id}")
def delete_table(table_id: int, db: Session = Depends(get_db), _admin=Depends(get_admin)):
    table = db.query(VenueTable).filter(VenueTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Mesa nao encontrada")
    db.delete(table)
    db.commit()
    return {"message": "Mesa removida com sucesso"}
