from sqlalchemy.orm import Session
from app.repositories.servico_repository import (
    listar_servicos,
    buscar_servico,
    listar_servicos_por_parceiro,
    criar_servico,
    atualizar_servico,
    pesquisar_servicos,
    deletar_servico
)
from app.schemas.schemas import ServicoCreate
from app.core.i18n import traduzir

def service_listar_servicos(db: Session):
    return listar_servicos(db)

def service_buscar_servico(db: Session, servico_id: int, lingua: str = "pt"):
    servico = buscar_servico(db, servico_id)
    if not servico:
        raise ValueError(traduzir("servico_nao_encontrado", lingua))
    return servico

def service_listar_servicos_por_parceiro(db: Session, parceiro_id: int):
    return listar_servicos_por_parceiro(db, parceiro_id)

def service_criar_servico(db: Session, servico: ServicoCreate):
    return criar_servico(db, servico)

def service_atualizar_servico(db: Session, servico_id: int, dados: ServicoCreate, lingua: str = "pt"):
    atualizado = atualizar_servico(db, servico_id, dados)
    if not atualizado:
        raise ValueError(traduzir("servico_nao_encontrado", lingua))
    return atualizado

def service_deletar_servico(db: Session, servico_id: int, lingua: str = "pt"):
    deletado = deletar_servico(db, servico_id)
    if not deletado:
        raise ValueError(traduzir("servico_nao_encontrado", lingua))
    return deletado