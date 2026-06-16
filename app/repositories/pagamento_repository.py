from sqlalchemy.orm import Session
from app.models.models import Pagamento
from app.schemas.schemas import PagamentoCreate

def listar_pagamentos(db: Session):
    return db.query(Pagamento).all()

def buscar_pagamento(db: Session, pagamento_id: int):
    return db.query(Pagamento).filter(Pagamento.id == pagamento_id).first()

def buscar_pagamento_por_reserva(db: Session, reserva_id: int):
    return db.query(Pagamento).filter(Pagamento.reserva_id == reserva_id).first()

def criar_pagamento(db: Session, pagamento: PagamentoCreate):
    novo_pagamento = Pagamento(**pagamento.model_dump())
    db.add(novo_pagamento)
    db.commit()
    db.refresh(novo_pagamento)
    return novo_pagamento

def atualizar_pagamento(db: Session, pagamento_id: int, dados: PagamentoCreate):
    pagamento = buscar_pagamento(db, pagamento_id)
    if not pagamento:
        return None
    for campo, valor in dados.model_dump().items():
        setattr(pagamento, campo, valor)
    db.commit()
    db.refresh(pagamento)
    return pagamento

def deletar_pagamento(db: Session, pagamento_id: int):
    pagamento = buscar_pagamento(db, pagamento_id)
    if not pagamento:
        return None
    db.delete(pagamento)
    db.commit()
    return pagamento