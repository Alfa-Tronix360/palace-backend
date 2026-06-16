from sqlalchemy.orm import Session
from app.models.models import Subscricao, PlanoSubscricao, EstadoSubscricao
from app.schemas.schemas import SubscricaoCreate
from datetime import datetime, timedelta

def criar_subscricao_trial(db: Session, parceiro_id: int):
    trial = Subscricao(
        parceiro_id=parceiro_id,
        plano=PlanoSubscricao.trial,
        valor_mensal=0.0,
        data_inicio=datetime.utcnow(),
        data_fim=datetime.utcnow() + timedelta(days=30),
        estado=EstadoSubscricao.ativa
    )
    db.add(trial)
    db.commit()
    db.refresh(trial)
    return trial

def criar_subscricao(db: Session, subscricao: SubscricaoCreate):
    nova = Subscricao(**subscricao.model_dump())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova

def buscar_subscricao_ativa(db: Session, parceiro_id: int):
    return db.query(Subscricao).filter(
        Subscricao.parceiro_id == parceiro_id,
        Subscricao.estado == EstadoSubscricao.ativa
    ).first()

def listar_subscricoes(db: Session):
    return db.query(Subscricao).all()

def listar_subscricoes_por_parceiro(db: Session, parceiro_id: int):
    return db.query(Subscricao).filter(
        Subscricao.parceiro_id == parceiro_id
    ).all()

def atualizar_estado_subscricao(db: Session, subscricao_id: int, estado: EstadoSubscricao):
    subscricao = db.query(Subscricao).filter(Subscricao.id == subscricao_id).first()
    if not subscricao:
        return None
    subscricao.estado = estado
    db.commit()
    db.refresh(subscricao)
    return subscricao

def listar_subscricoes_expiradas(db: Session):
    return db.query(Subscricao).filter(
        Subscricao.data_fim < datetime.utcnow(),
        Subscricao.estado == EstadoSubscricao.ativa
    ).all()