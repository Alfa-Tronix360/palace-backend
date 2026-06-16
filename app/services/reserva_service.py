from sqlalchemy.orm import Session
from app.repositories.reserva_repository import (
    listar_reservas,
    buscar_reserva,
    listar_reservas_por_usuario,
    listar_reservas_por_parceiro,
    verificar_disponibilidade,
    criar_reserva,
    atualizar_reserva,
    atualizar_status_reserva,
    deletar_reserva
)
from app.repositories.servico_repository import buscar_servico
from app.schemas.schemas import ReservaCreate
from app.models.models import TipoPreco
from app.core.i18n import traduzir

def service_listar_reservas(db: Session):
    return listar_reservas(db)

def service_buscar_reserva(db: Session, reserva_id: int, lingua: str = "pt"):
    reserva = buscar_reserva(db, reserva_id)
    if not reserva:
        raise ValueError(traduzir("reserva_nao_encontrada", lingua))
    return reserva

def service_listar_reservas_por_usuario(db: Session, usuario_id: int):
    return listar_reservas_por_usuario(db, usuario_id)

def service_listar_reservas_por_parceiro(db: Session, parceiro_id: int):
    return listar_reservas_por_parceiro(db, parceiro_id)

def service_verificar_disponibilidade(db: Session, servico_id: int, data_inicio, data_fim):
    return verificar_disponibilidade(db, servico_id, data_inicio, data_fim)

def service_criar_reserva(db: Session, reserva: ReservaCreate, usuario_id: int, lingua: str = "pt"):
    servico = buscar_servico(db, reserva.servico_id)
    if not servico:
        raise ValueError(traduzir("servico_nao_encontrado", lingua))

    disponivel = verificar_disponibilidade(db, reserva.servico_id, reserva.data_inicio, reserva.data_fim)
    if not disponivel:
        raise ValueError(traduzir("servico_indisponivel", lingua))

    diferenca = reserva.data_fim - reserva.data_inicio

    if servico.tipo_preco == TipoPreco.por_hora:
        duracao_horas = diferenca.total_seconds() / 3600
        total_preco = servico.preco * duracao_horas
    elif servico.tipo_preco == TipoPreco.por_noite:
        noites = diferenca.days
        total_preco = servico.preco * noites if noites > 0 else servico.preco
    else:
        total_preco = servico.preco

    return criar_reserva(db, reserva, usuario_id, total_preco)

def service_atualizar_reserva(db: Session, reserva_id: int, dados: ReservaCreate, lingua: str = "pt"):
    atualizado = atualizar_reserva(db, reserva_id, dados)
    if not atualizado:
        raise ValueError(traduzir("reserva_nao_encontrada", lingua))
    return atualizado

def service_atualizar_status_reserva(db: Session, reserva_id: int, status, lingua: str = "pt"):
    reserva = atualizar_status_reserva(db, reserva_id, status)
    if not reserva:
        raise ValueError(traduzir("reserva_nao_encontrada", lingua))
    return reserva

def service_deletar_reserva(db: Session, reserva_id: int, lingua: str = "pt"):
    deletado = deletar_reserva(db, reserva_id)
    if not deletado:
        raise ValueError(traduzir("reserva_nao_encontrada", lingua))
    return deletado