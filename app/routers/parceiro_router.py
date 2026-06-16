from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import ParceiroCreate, ParceiroResponse, ParceiroRegistoCreate, ParceiroAprovar
from app.core.dependencies import get_usuario_atual, get_admin, get_lingua
from app.models.models import Usuario
from app.services.parceiro_service import (
    service_listar_parceiros,
    service_listar_parceiros_pendentes,
    service_buscar_parceiro,
    service_buscar_parceiro_por_usuario,
    service_listar_parceiros_por_tipo,
    service_registar_parceiro,
    service_aprovar_parceiro,
    service_atualizar_parceiro,
    service_deletar_parceiro
)
from app.integrations.email import email_registo_parceiro_admin, email_boas_vindas_parceiro, email_estado_parceiro
from app.core.i18n import traduzir
from app.integrations.whatsapp import whatsapp_boas_vindas_parceiro

router = APIRouter(prefix="/parceiros", tags=["Parceiros"])

@router.get("/", response_model=list[ParceiroResponse])
def listar(db: Session = Depends(get_db)):
    return service_listar_parceiros(db)

@router.get("/tipo/{tipo}", response_model=list[ParceiroResponse])
def listar_por_tipo(tipo: str, db: Session = Depends(get_db)):
    return service_listar_parceiros_por_tipo(db, tipo)

@router.get("/pesquisar")
def pesquisar(
    tipo: str = None,
    localizacao: str = None,
    preco_min: float = None,
    preco_max: float = None,
    capacidade: int = None,
    data_inicio: str = None,
    data_fim: str = None,
    db: Session = Depends(get_db)
):
    from datetime import datetime
    from app.services.parceiro_service import service_pesquisar
    inicio = datetime.fromisoformat(data_inicio) if data_inicio else None
    fim = datetime.fromisoformat(data_fim) if data_fim else None
    return service_pesquisar(
        db,
        tipo=tipo,
        localizacao=localizacao,
        preco_min=preco_min,
        preco_max=preco_max,
        capacidade=capacidade,
        data_inicio=inicio,
        data_fim=fim
    )

@router.post("/registar", response_model=ParceiroResponse, status_code=201)
async def registar(dados: ParceiroRegistoCreate, db: Session = Depends(get_db), lingua: str = Depends(get_lingua)):
    try:
        parceiro = service_registar_parceiro(db, dados, lingua)
        await email_registo_parceiro_admin(
            admin_email="afonsorogerio255@gmail.com",
            nome_negocio=dados.nome_negocio,
            nome_responsavel=dados.nome_responsavel
        )
        await email_boas_vindas_parceiro(
            parceiro_email=dados.email,
            nome_negocio=dados.nome_negocio,
            nome_responsavel=dados.nome_responsavel)

        if dados.telefone:
            await whatsapp_boas_vindas_parceiro(
                telefone=dados.telefone,
                nome_responsavel=dados.nome_responsavel,
                nome_negocio=dados.nome_negocio
            )    
        
        
        
        return parceiro
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pendentes", response_model=list[ParceiroResponse])
def listar_pendentes(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin)):
    return service_listar_parceiros_pendentes(db)

@router.put("/{parceiro_id}/aprovar", response_model=ParceiroResponse)
async def aprovar(parceiro_id: int, dados: ParceiroAprovar, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin), lingua: str = Depends(get_lingua)):
    try:
        parceiro = service_aprovar_parceiro(db, parceiro_id, dados, lingua)
        if parceiro.email:
            await email_estado_parceiro(
                parceiro_email=parceiro.email,
                nome_negocio=parceiro.nome,
                aprovado=dados.estado.value == "aprovado"
            )
        return parceiro
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/meu-perfil", response_model=ParceiroResponse)
def meu_perfil(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_usuario_atual), lingua: str = Depends(get_lingua)):
    try:
        return service_buscar_parceiro_por_usuario(db, usuario_atual.id, lingua)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{parceiro_id}", response_model=ParceiroResponse)
def buscar(parceiro_id: int, db: Session = Depends(get_db), lingua: str = Depends(get_lingua)):
    try:
        return service_buscar_parceiro(db, parceiro_id, lingua)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{parceiro_id}", response_model=ParceiroResponse)
def atualizar(parceiro_id: int, parceiro: ParceiroCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin), lingua: str = Depends(get_lingua)):
    try:
        return service_atualizar_parceiro(db, parceiro_id, parceiro, lingua)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{parceiro_id}")
def deletar(parceiro_id: int, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin), lingua: str = Depends(get_lingua)):
    try:
        service_deletar_parceiro(db, parceiro_id, lingua)
        return {"mensagem": traduzir("parceiro_eliminado", lingua)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))