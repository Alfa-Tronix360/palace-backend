from sqlalchemy.orm import Session
from app.models.models import Reserva, StatusReserva
from app.schemas.schemas import ReservaCreate
from datetime import datetime

def listar_reservas(db: Session):
    return db.query(Reserva).all()

def buscar_reserva(db: Session, reserva_id: int):
    return db.query(Reserva).filter(Reserva.id == reserva_id).first()

def listar_reservas_por_usuario(db: Session, usuario_id: int):
    return db.query(Reserva).filter(Reserva.usuario_id == usuario_id).all()

def listar_reservas_por_parceiro(db: Session, parceiro_id: int):
    return db.query(Reserva).filter(Reserva.parceiro_id == parceiro_id).all()

def verificar_disponibilidade(db: Session, servico_id: int, data_inicio: datetime, data_fim: datetime):
    conflito = db.query(Reserva).filter(
        Reserva.servico_id == servico_id,
        Reserva.status != "cancelada",
        Reserva.data_inicio < data_fim,
        Reserva.data_fim > data_inicio
    ).first()
    return conflito is None

def criar_reserva(db: Session, reserva: ReservaCreate, usuario_id: int, total_preco: float):
    nova_reserva = Reserva(
        usuario_id=usuario_id,
        parceiro_id=reserva.parceiro_id,
        servico_id=reserva.servico_id,
        data_inicio=reserva.data_inicio,
        data_fim=reserva.data_fim,
        descricao=reserva.descricao,
        total_preco=total_preco
    )
    db.add(nova_reserva)
    db.commit()
    db.refresh(nova_reserva)
    return nova_reserva

def atualizar_reserva(db: Session, reserva_id: int, dados: ReservaCreate):
    reserva = buscar_reserva(db, reserva_id)
    if not reserva:
        return None
    for campo, valor in dados.model_dump().items():
        setattr(reserva, campo, valor)
    db.commit()
    db.refresh(reserva)
    return reserva


def atualizar_status_reserva(db: Session, reserva_id: int, status: StatusReserva):
    reserva = buscar_reserva(db, reserva_id)
    if not reserva:
        return None
    reserva.status = status
    db.commit()
    db.refresh(reserva)
    return reserva



def deletar_reserva(db: Session, reserva_id: int):
    reserva = buscar_reserva(db, reserva_id)
    if not reserva:
        return None
    db.delete(reserva)
    db.commit()
    return reserva