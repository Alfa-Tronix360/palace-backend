from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_admin, get_usuario_atual
from app.core.tenant import get_company_id
from app.models.models import PalaceReservation, StatusReserva, VenueArea, VenueTable, TableStatus
from app.schemas.palace_schemas import (
    VenueAreaCreate,
    VenueAreaResponse,
    VenueAreaUpdate,
    VenueTableCreate,
    VenueTableResponse,
    VenueTableUpdate,
)
from sqlalchemy import func

router = APIRouter(prefix="/venue", tags=["Venue"])


def apply_updates(model, data):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(model, field, value)
    return model


@router.get("/areas", response_model=list[VenueAreaResponse])
def list_areas(request: Request, db: Session = Depends(get_db)):
    company_id = get_company_id(request, db)
    return db.query(VenueArea).filter(VenueArea.company_id == company_id).order_by(VenueArea.id.asc()).all()


@router.post("/areas", response_model=VenueAreaResponse, status_code=201)
def create_area(
    payload: VenueAreaCreate,
    request: Request,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    company_id = get_company_id(request, db)
    area = VenueArea(**payload.model_dump(), company_id=company_id)
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
def list_tables(request: Request, db: Session = Depends(get_db)):
    company_id = get_company_id(request, db)
    return db.query(VenueTable).filter(VenueTable.company_id == company_id).order_by(VenueTable.number.asc()).all()


@router.post("/tables", response_model=VenueTableResponse, status_code=201)
def create_table(
    payload: VenueTableCreate,
    request: Request,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    company_id = get_company_id(request, db)
    max_number = db.query(func.max(VenueTable.number)).filter(VenueTable.company_id == company_id).scalar() or 0
    table_data = payload.model_dump(exclude={'number'})
    table_data['number'] = max_number + 1
    table = VenueTable(**table_data, company_id=company_id)
    db.add(table)
    db.commit()
    db.refresh(table)
    return table


PRICE_TIER_MAP = {
    "standard": 15000,
    "premium": 25000,
    "vip": 45000,
}


@router.get("/tables/availability", response_model=list[VenueTableResponse])
def table_availability(
    request: Request,
    date: str,
    time: str,
    guests: int,
    db: Session = Depends(get_db),
):
    company_id = get_company_id(request, db)
    starts_at = datetime.fromisoformat(f"{date}T{time}")
    ends_at = starts_at + timedelta(hours=2)
    busy_table_ids = (
        db.query(PalaceReservation.table_id)
        .filter(PalaceReservation.status != StatusReserva.cancelada)
        .filter(PalaceReservation.starts_at < ends_at)
        .filter(PalaceReservation.ends_at > starts_at)
        .filter(PalaceReservation.company_id == company_id)
        .subquery()
    )
    tables = (
        db.query(VenueTable)
        .filter(VenueTable.company_id == company_id)
        .filter(VenueTable.status == TableStatus.available)
        .filter(VenueTable.capacity >= guests)
        .filter(VenueTable.id.not_in(busy_table_ids))
        .order_by(VenueTable.capacity.asc(), VenueTable.number.asc())
        .all()
    )
    result = []
    for t in tables:
        t.__dict__['price'] = PRICE_TIER_MAP.get(t.price_tier or 'standard', 15000)
        result.append(t)
    return result


@router.patch("/tables/{table_id}", response_model=VenueTableResponse)
def update_table(
    table_id: int,
    payload: VenueTableUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_usuario_atual),
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