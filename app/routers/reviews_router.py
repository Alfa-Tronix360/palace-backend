from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import Review, PalaceReservation
from app.core.dependencies import get_usuario_atual, get_admin
from app.models.models import Usuario
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/reviews", tags=["Reviews"])

# ── Schema simples inline ─────────────────────────────────────────────────
class ReviewCreate(BaseModel):
    reservationId: str
    rating: int
    comment: Optional[str] = None
    service: int
    atmosphere: int
    food: int
    drinks: int

class ReviewResponse(BaseModel):
    id: int
    clientId: str
    clientName: str
    reservationId: str
    rating: int
    comment: Optional[str]
    service: int
    atmosphere: int
    food: int
    drinks: int
    createdAt: datetime

    class Config:
        from_attributes = True


@router.post("", status_code=201)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    reserva = db.query(PalaceReservation).filter(
        PalaceReservation.id == int(payload.reservationId),
        PalaceReservation.client_id == usuario_atual.id,
    ).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva nao encontrada")

    existing = db.query(Review).filter(
        Review.reservation_id == int(payload.reservationId)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ja avaliou esta reserva")

    review = Review(
        client_id=usuario_atual.id,
        reservation_id=int(payload.reservationId),
        rating=payload.rating,
        comment=payload.comment,
        service=payload.service,
        atmosphere=payload.atmosphere,
        food=payload.food,
        drinks=payload.drinks,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {
        "id": review.id,
        "clientId": str(review.client_id),
        "clientName": usuario_atual.nome,
        "reservationId": str(review.reservation_id),
        "rating": review.rating,
        "comment": review.comment,
        "service": review.service,
        "atmosphere": review.atmosphere,
        "food": review.food,
        "drinks": review.drinks,
        "createdAt": review.created_at,
    }


@router.get("")
def list_reviews(db: Session = Depends(get_db), _admin=Depends(get_admin)):
    reviews = db.query(Review).order_by(Review.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "clientId": str(r.client_id),
            "clientName": r.client.nome if r.client else "",
            "reservationId": str(r.reservation_id),
            "rating": r.rating,
            "comment": r.comment,
            "service": r.service,
            "atmosphere": r.atmosphere,
            "food": r.food,
            "drinks": r.drinks,
            "createdAt": r.created_at,
        }
        for r in reviews
    ]


@router.get("/summary")
def reviews_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(Review.id)).scalar() or 0
    if total == 0:
        return {"total": 0, "average": 0, "service": 0, "atmosphere": 0, "food": 0, "drinks": 0}
    avg = db.query(func.avg(Review.rating)).scalar() or 0
    service = db.query(func.avg(Review.service)).scalar() or 0
    atmosphere = db.query(func.avg(Review.atmosphere)).scalar() or 0
    food = db.query(func.avg(Review.food)).scalar() or 0
    drinks = db.query(func.avg(Review.drinks)).scalar() or 0
    return {
        "total": total,
        "average": round(float(avg), 1),
        "service": round(float(service), 1),
        "atmosphere": round(float(atmosphere), 1),
        "food": round(float(food), 1),
        "drinks": round(float(drinks), 1),
    }        