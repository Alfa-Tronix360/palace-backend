from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_admin, get_usuario_atual
from app.database import get_db
from app.models.models import Pagamento, StatusPagamento, Usuario
from app.schemas.palace_schemas import PaymentResponse

router = APIRouter(prefix="/payments", tags=["Payments API"])


STATUS_TO_API = {
    StatusPagamento.pendente: "pending",
    StatusPagamento.pago: "confirmed",
    StatusPagamento.cancelado: "failed",
}


def to_payment_response(payment: Pagamento) -> PaymentResponse:
    reserva = payment.reserva
    usuario = reserva.usuario if reserva else None
    return PaymentResponse(
        id=str(payment.id),
        reservationId=str(payment.reserva_id) if payment.reserva_id else None,
        eventId=None,
        clientId=str(usuario.id) if usuario else "",
        clientName=usuario.nome if usuario else "Cliente",
        amount=payment.valor,
        method=payment.metodo or "multicaixa",
        status=STATUS_TO_API.get(payment.status, "pending"),
        reference=f"PAY-{payment.id:04d}",
        date=payment.criado_em,
    )


@router.get("", response_model=list[PaymentResponse])
@router.get("/", response_model=list[PaymentResponse])
def list_payments(
    status: str | None = None,
    method: str | None = None,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin),
):
    payments = db.query(Pagamento).order_by(Pagamento.criado_em.desc()).all()
    data = [to_payment_response(payment) for payment in payments]
    if status:
        data = [payment for payment in data if payment.status == status]
    if method:
        data = [payment for payment in data if payment.method == method]
    return data


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db), _user: Usuario = Depends(get_usuario_atual)):
    payment = db.query(Pagamento).filter(Pagamento.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento nao encontrado")
    return to_payment_response(payment)


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(payment_id: int, db: Session = Depends(get_db), _admin: Usuario = Depends(get_admin)):
    payment = db.query(Pagamento).filter(Pagamento.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento nao encontrado")
    payment.status = StatusPagamento.pago
    db.commit()
    db.refresh(payment)
    return to_payment_response(payment)
