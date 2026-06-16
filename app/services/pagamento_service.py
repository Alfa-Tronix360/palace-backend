from sqlalchemy.orm import Session
from app.repositories.pagamento_repository import (
    listar_pagamentos,
    buscar_pagamento,
    buscar_pagamento_por_reserva,
    criar_pagamento,
    atualizar_pagamento,
    deletar_pagamento
)
from app.schemas.schemas import PagamentoCreate
from app.core.i18n import traduzir

def service_listar_pagamentos(db: Session):
    return listar_pagamentos(db)

def service_buscar_pagamento(db: Session, pagamento_id: int, lingua: str = "pt"):
    pagamento = buscar_pagamento(db, pagamento_id)
    if not pagamento:
        raise ValueError(traduzir("pagamento_nao_encontrado", lingua))
    return pagamento

def service_buscar_pagamento_por_reserva(db: Session, reserva_id: int, lingua: str = "pt"):
    pagamento = buscar_pagamento_por_reserva(db, reserva_id)
    if not pagamento:
        raise ValueError(traduzir("pagamento_nao_encontrado", lingua))
    return pagamento

def service_criar_pagamento(db: Session, pagamento: PagamentoCreate, lingua: str = "pt"):
    existente = buscar_pagamento_por_reserva(db, pagamento.reserva_id)
    if existente:
        raise ValueError(traduzir("pagamento_ja_existe", lingua))
    return criar_pagamento(db, pagamento)

def service_atualizar_pagamento(db: Session, pagamento_id: int, dados: PagamentoCreate, lingua: str = "pt"):
    atualizado = atualizar_pagamento(db, pagamento_id, dados)
    if not atualizado:
        raise ValueError(traduzir("pagamento_nao_encontrado", lingua))
    return atualizado

def service_deletar_pagamento(db: Session, pagamento_id: int, lingua: str = "pt"):
    deletado = deletar_pagamento(db, pagamento_id)
    if not deletado:
        raise ValueError(traduzir("pagamento_nao_encontrado", lingua))
    return deletado