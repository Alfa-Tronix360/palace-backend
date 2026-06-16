from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.schemas.schemas import HorarioFuncionamentoCreate, HorarioFuncionamentoResponse, BloqueioCreate, BloqueioResponse
from app.core.dependencies import get_usuario_atual, get_parceiro, get_lingua
from app.models.models import Usuario
from app.repositories.disponibilidade_repository import (
    criar_horario,
    listar_horarios,
    deletar_horario,
    criar_bloqueio,
    listar_bloqueios,
    deletar_bloqueio,
    gerar_calendario
)
from app.services.parceiro_service import service_buscar_parceiro_por_usuario

router = APIRouter(prefix="/disponibilidade", tags=["Disponibilidade"])

# ====================================
# HORÁRIOS
# ====================================

# parceiro — definir horário de funcionamento
@router.post("/horarios", response_model=HorarioFuncionamentoResponse, status_code=201)
def criar(horario: HorarioFuncionamentoCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    try:
        parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
        return criar_horario(db, parceiro.id, horario)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# público — ver horários de um parceiro
@router.get("/horarios/{parceiro_id}", response_model=list[HorarioFuncionamentoResponse])
def listar(parceiro_id: int, db: Session = Depends(get_db)):
    return listar_horarios(db, parceiro_id)

# parceiro — eliminar horário
@router.delete("/horarios/{horario_id}")
def deletar(horario_id: int, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    resultado = deletar_horario(db, horario_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Horário não encontrado")
    return {"mensagem": "Horário eliminado com sucesso"}

# ====================================
# BLOQUEIOS
# ====================================

# parceiro — bloquear período
@router.post("/bloqueios", response_model=BloqueioResponse, status_code=201)
def criar_bloqueio_endpoint(bloqueio: BloqueioCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    try:
        parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
        return criar_bloqueio(db, parceiro.id, bloqueio)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# público — ver bloqueios de um parceiro
@router.get("/bloqueios/{parceiro_id}", response_model=list[BloqueioResponse])
def listar_bloqueios_endpoint(parceiro_id: int, db: Session = Depends(get_db)):
    return listar_bloqueios(db, parceiro_id)

# parceiro — eliminar bloqueio
@router.delete("/bloqueios/{bloqueio_id}")
def deletar_bloqueio_endpoint(bloqueio_id: int, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    resultado = deletar_bloqueio(db, bloqueio_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Bloqueio não encontrado")
    return {"mensagem": "Bloqueio eliminado com sucesso"}

# ====================================
# CALENDÁRIO
# ====================================

# público — ver calendário de disponibilidade
@router.get("/calendario")
def ver_calendario(
    parceiro_id: int,
    servico_id: int,
    data_inicio: str,
    data_fim: str,
    db: Session = Depends(get_db)
):
    try:
        inicio = datetime.fromisoformat(data_inicio)
        fim = datetime.fromisoformat(data_fim)
        return gerar_calendario(db, parceiro_id, servico_id, inicio, fim)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))