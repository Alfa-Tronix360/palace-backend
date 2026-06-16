from sqlalchemy.orm import Session
from app.models.models import Servico
from app.schemas.schemas import ServicoCreate

def listar_servicos(db: Session):
    return db.query(Servico).filter(Servico.ativo == True).all()

def buscar_servico(db: Session, servico_id: int):
    return db.query(Servico).filter(Servico.id == servico_id).first()

def listar_servicos_por_parceiro(db: Session, parceiro_id: int):
    return db.query(Servico).filter(
        Servico.parceiro_id == parceiro_id,
        Servico.ativo == True
    ).all()

def criar_servico(db: Session, servico: ServicoCreate):
    novo_servico = Servico(**servico.model_dump())
    db.add(novo_servico)
    db.commit()
    db.refresh(novo_servico)
    return novo_servico

def atualizar_servico(db: Session, servico_id: int, dados: ServicoCreate):
    servico = buscar_servico(db, servico_id)
    if not servico:
        return None
    for campo, valor in dados.model_dump().items():
        setattr(servico, campo, valor)
    db.commit()
    db.refresh(servico)
    return 


def pesquisar_servicos(
    db: Session,
    parceiro_id: int = None,
    preco_min: float = None,
    preco_max: float = None,
    capacidade: int = None,
):
    query = db.query(Servico).filter(Servico.ativo == True)

    if parceiro_id:
        query = query.filter(Servico.parceiro_id == parceiro_id)

    if preco_min:
        query = query.filter(Servico.preco >= preco_min)

    if preco_max:
        query = query.filter(Servico.preco <= preco_max)

    if capacidade:
        query = query.filter(Servico.capacidade >= capacidade)

    return query.all()

def deletar_servico(db: Session, servico_id: int):
    servico = buscar_servico(db, servico_id)
    if not servico:
        return None
    servico.ativo = False
    db.commit()
    return servico