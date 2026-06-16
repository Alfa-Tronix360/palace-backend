from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import PagamentoCreate, PagamentoUpdateStatus
from app.core.dependencies import get_usuario_atual, get_admin, get_lingua
from app.models.models import Usuario
from app.core.i18n import traduzir
from app.services.pagamento_service import (
    service_listar_pagamentos,
    service_buscar_pagamento,
    service_buscar_pagamento_por_reserva,
    service_criar_pagamento,
    service_deletar_pagamento,
)

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])


@router.get("/")
def listar(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin)):
    return service_listar_pagamentos(db)


@router.get("/reserva/{reserva_id}")
def buscar_por_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    lingua: str = Depends(get_lingua),
):
    try:
        return service_buscar_pagamento_por_reserva(db, reserva_id, lingua)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{pagamento_id}")
def buscar(
    pagamento_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    lingua: str = Depends(get_lingua),
):
    try:
        return service_buscar_pagamento(db, pagamento_id, lingua)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", status_code=201)
def criar(
    pagamento: PagamentoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    lingua: str = Depends(get_lingua),
):
    try:
        return service_criar_pagamento(db, pagamento, lingua)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{pagamento_id}/status")
def atualizar_status(
    pagamento_id: int,
    dados: PagamentoUpdateStatus,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_admin),
    lingua: str = Depends(get_lingua),
):
    try:
        pagamento = service_buscar_pagamento(db, pagamento_id, lingua)
        pagamento.status = dados.status
        db.commit()
        db.refresh(pagamento)
        return pagamento
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{pagamento_id}")
def deletar(
    pagamento_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_admin),
    lingua: str = Depends(get_lingua),
):
    try:
        service_deletar_pagamento(db, pagamento_id, lingua)
        return {"mensagem": traduzir("pagamento_eliminado", lingua)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
