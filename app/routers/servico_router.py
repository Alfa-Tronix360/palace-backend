from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import ServicoCreate, ServicoResponse
from app.core.dependencies import get_usuario_atual, get_admin, get_parceiro
from app.models.models import Usuario
from app.services.servico_service import (
    service_listar_servicos,
    service_buscar_servico,
    service_listar_servicos_por_parceiro,
    service_criar_servico,
    service_atualizar_servico,
    service_deletar_servico
)
from app.services.parceiro_service import service_buscar_parceiro_por_usuario

router = APIRouter(prefix="/servicos", tags=["Servicos"])

# público — qualquer um pode ver serviços
@router.get("/", response_model=list[ServicoResponse])
def listar(db: Session = Depends(get_db)):
    return service_listar_servicos(db)

# público — ver serviços de um parceiro
@router.get("/parceiro/{parceiro_id}", response_model=list[ServicoResponse])
def listar_por_parceiro(parceiro_id: int, db: Session = Depends(get_db)):
    return service_listar_servicos_por_parceiro(db, parceiro_id)

# parceiro — ver os seus próprios serviços
@router.get("/meus", response_model=list[ServicoResponse])
def listar_meus(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    try:
        parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
        return service_listar_servicos_por_parceiro(db, parceiro.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# público — ver um serviço específico
@router.get("/{servico_id}", response_model=ServicoResponse)
def buscar(servico_id: int, db: Session = Depends(get_db)):
    try:
        return service_buscar_servico(db, servico_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# parceiro — criar serviço no seu negócio
@router.post("/", response_model=ServicoResponse, status_code=201)
def criar(servico: ServicoCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    try:
        parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
        if servico.parceiro_id != parceiro.id:
            raise HTTPException(status_code=403, detail="Não pode criar serviços para outro parceiro")
        return service_criar_servico(db, servico)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# parceiro — atualizar o seu serviço
@router.put("/{servico_id}", response_model=ServicoResponse)
def atualizar(servico_id: int, servico: ServicoCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    try:
        parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
        servico_existente = service_buscar_servico(db, servico_id)
        if servico_existente.parceiro_id != parceiro.id:
            raise HTTPException(status_code=403, detail="Não pode editar serviços de outro parceiro")
        return service_atualizar_servico(db, servico_id, servico)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# parceiro ou admin — desativar serviço
@router.delete("/{servico_id}")
def deletar(servico_id: int, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    try:
        parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
        servico_existente = service_buscar_servico(db, servico_id)
        if servico_existente.parceiro_id != parceiro.id:
            raise HTTPException(status_code=403, detail="Não pode eliminar serviços de outro parceiro")
        service_deletar_servico(db, servico_id)
        return {"mensagem": "Serviço desativado com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))