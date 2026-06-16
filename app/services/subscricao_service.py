from sqlalchemy.orm import Session
from app.repositories.subscricao_repository import (
    criar_subscricao_trial,
    criar_subscricao,
    buscar_subscricao_ativa,
    listar_subscricoes,
    listar_subscricoes_por_parceiro,
    atualizar_estado_subscricao,
    listar_subscricoes_expiradas
)
from app.schemas.schemas import SubscricaoCreate, SubscricaoUpdateEstado
from app.models.models import EstadoSubscricao
from app.core.i18n import traduzir

def service_criar_subscricao_trial(db: Session, parceiro_id: int):
    return criar_subscricao_trial(db, parceiro_id)

def service_criar_subscricao(db: Session, subscricao: SubscricaoCreate):
    return criar_subscricao(db, subscricao)

def service_buscar_subscricao_ativa(db: Session, parceiro_id: int, lingua: str = "pt"):
    subscricao = buscar_subscricao_ativa(db, parceiro_id)
    if not subscricao:
        raise ValueError(traduzir("subscricao_sem_ativa", lingua))
    return subscricao

def service_listar_subscricoes(db: Session):
    return listar_subscricoes(db)

def service_listar_subscricoes_por_parceiro(db: Session, parceiro_id: int):
    return listar_subscricoes_por_parceiro(db, parceiro_id)

def service_atualizar_estado_subscricao(db: Session, subscricao_id: int, dados: SubscricaoUpdateEstado, lingua: str = "pt"):
    subscricao = atualizar_estado_subscricao(db, subscricao_id, dados.estado)
    if not subscricao:
        raise ValueError(traduzir("subscricao_nao_encontrada", lingua))
    return subscricao

def service_verificar_subscricao_ativa(db: Session, parceiro_id: int) -> bool:
    subscricao = buscar_subscricao_ativa(db, parceiro_id)
    if not subscricao:
        return False
    from datetime import datetime
    if subscricao.data_fim < datetime.utcnow():
        atualizar_estado_subscricao(db, subscricao.id, EstadoSubscricao.expirada)
        return False
    return True

def service_expirar_subscricoes(db: Session):
    expiradas = listar_subscricoes_expiradas(db)
    for subscricao in expiradas:
        atualizar_estado_subscricao(db, subscricao.id, EstadoSubscricao.expirada)
    return len(expiradas)