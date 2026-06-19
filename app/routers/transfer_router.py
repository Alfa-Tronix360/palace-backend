from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_admin, get_usuario_atual
from app.models.models import TransferRequest
from app.schemas.palace_schemas import TransferRequestCreate, TransferRequestResponse

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post("", response_model=TransferRequestResponse, status_code=201)
@router.post("/", response_model=TransferRequestResponse, status_code=201)
def create_transfer(
    payload: TransferRequestCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_usuario_atual),
):
    transfer = TransferRequest(
        client_id=payload.client_id,
        vehicle_type=payload.vehicle_type,
        vehicle_model=payload.vehicle_model,
        date=payload.date,
        time=payload.time,
        pickup_location=payload.pickup_location,
        notes=payload.notes,
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer


@router.get("", response_model=list[TransferRequestResponse])
@router.get("/", response_model=list[TransferRequestResponse])
def list_transfers(
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    return db.query(TransferRequest).order_by(TransferRequest.created_at.desc()).all()


@router.get("/me/{client_id}", response_model=list[TransferRequestResponse])
def list_my_transfers(
    client_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_usuario_atual),
):
    return db.query(TransferRequest).filter(
        TransferRequest.client_id == client_id
    ).order_by(TransferRequest.created_at.desc()).all()


@router.patch("/{transfer_id}/status", response_model=TransferRequestResponse)
def update_transfer_status(
    transfer_id: int,
    status: str,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    transfer = db.query(TransferRequest).filter(TransferRequest.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Pedido de transfer nao encontrado")
    transfer.status = status
    db.commit()
    db.refresh(transfer)
    return transfer