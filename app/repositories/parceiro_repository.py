from sqlalchemy.orm import Session
from app.models.models import Parceiro, EstadoParceiro
from app.schemas.schemas import ParceiroCreate

def listar_parceiros(db: Session):
    return db.query(Parceiro).filter(
        Parceiro.ativo == True,
        Parceiro.estado == EstadoParceiro.aprovado
    ).all()

def listar_parceiros_pendentes(db: Session):
    return db.query(Parceiro).filter(
        Parceiro.estado == EstadoParceiro.pendente
    ).all()

def buscar_parceiro(db: Session, parceiro_id: int):
    return db.query(Parceiro).filter(Parceiro.id == parceiro_id).first()

def buscar_parceiro_por_usuario(db: Session, usuario_id: int):
    return db.query(Parceiro).filter(Parceiro.usuario_id == usuario_id).first()

def listar_parceiros_por_tipo(db: Session, tipo: str):
    return db.query(Parceiro).filter(
        Parceiro.tipo == tipo,
        Parceiro.ativo == True,
        Parceiro.estado == EstadoParceiro.aprovado
    ).all()

def criar_parceiro(db: Session, parceiro: ParceiroCreate, usuario_id: int):
    novo_parceiro = Parceiro(
        usuario_id=usuario_id,
        nome=parceiro.nome,
        tipo=parceiro.tipo,
        descricao=parceiro.descricao,
        localizacao=parceiro.localizacao,
        telefone=parceiro.telefone,
        email=parceiro.email,
        website=parceiro.website if hasattr(parceiro, 'website') else None,
        nif=parceiro.nif,
    )
    db.add(novo_parceiro)
    db.commit()
    db.refresh(novo_parceiro)
    return novo_parceiro

def aprovar_parceiro(db: Session, parceiro_id: int, estado: EstadoParceiro):
    parceiro = buscar_parceiro(db, parceiro_id)
    if not parceiro:
        return None
    parceiro.estado = estado
    db.commit()
    db.refresh(parceiro)
    return parceiro

def atualizar_parceiro(db: Session, parceiro_id: int, dados: ParceiroCreate):
    parceiro = buscar_parceiro(db, parceiro_id)
    if not parceiro:
        return None
    for campo, valor in dados.model_dump().items():
        setattr(parceiro, campo, valor)
    db.commit()
    db.refresh(parceiro)
    return parceiro

def pesquisar_parceiros(
    db: Session,
    tipo: str = None,
    localizacao: str = None,
):
    query = db.query(Parceiro).filter(
        Parceiro.ativo == True,
        Parceiro.estado == EstadoParceiro.aprovado
    )

    if tipo:
        query = query.filter(Parceiro.tipo == tipo)

    if localizacao:
        query = query.filter(
            Parceiro.localizacao.ilike(f"%{localizacao}%")
        )

    return query.all()

def deletar_parceiro(db: Session, parceiro_id: int):
    parceiro = buscar_parceiro(db, parceiro_id)
    if not parceiro:
        return None
    parceiro.ativo = False
    db.commit()
    return parceiro