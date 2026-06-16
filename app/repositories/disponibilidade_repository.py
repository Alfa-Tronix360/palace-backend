from sqlalchemy.orm import Session
from app.models.models import HorarioFuncionamento, BloqueioDisponibilidade, Reserva, StatusReserva, DiaSemana
from app.schemas.schemas import HorarioFuncionamentoCreate, BloqueioCreate
from datetime import datetime, timedelta

# ====================================
# HORÁRIOS
# ====================================

def criar_horario(db: Session, parceiro_id: int, horario: HorarioFuncionamentoCreate):
    novo = HorarioFuncionamento(
        parceiro_id=parceiro_id,
        dia_semana=horario.dia_semana,
        hora_abertura=horario.hora_abertura,
        hora_fecho=horario.hora_fecho,
        ativo=horario.ativo
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

def listar_horarios(db: Session, parceiro_id: int):
    return db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.parceiro_id == parceiro_id
    ).all()

def deletar_horario(db: Session, horario_id: int):
    horario = db.query(HorarioFuncionamento).filter(HorarioFuncionamento.id == horario_id).first()
    if not horario:
        return None
    db.delete(horario)
    db.commit()
    return horario

# ====================================
# BLOQUEIOS
# ====================================

def criar_bloqueio(db: Session, parceiro_id: int, bloqueio: BloqueioCreate):
    novo = BloqueioDisponibilidade(
        parceiro_id=parceiro_id,
        servico_id=bloqueio.servico_id,
        data_inicio=bloqueio.data_inicio,
        data_fim=bloqueio.data_fim,
        motivo=bloqueio.motivo,
        descricao=bloqueio.descricao
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

def listar_bloqueios(db: Session, parceiro_id: int):
    return db.query(BloqueioDisponibilidade).filter(
        BloqueioDisponibilidade.parceiro_id == parceiro_id
    ).all()

def deletar_bloqueio(db: Session, bloqueio_id: int):
    bloqueio = db.query(BloqueioDisponibilidade).filter(BloqueioDisponibilidade.id == bloqueio_id).first()
    if not bloqueio:
        return None
    db.delete(bloqueio)
    db.commit()
    return bloqueio

# ====================================
# CALENDÁRIO
# ====================================

def gerar_calendario(db: Session, parceiro_id: int, servico_id: int, data_inicio: datetime, data_fim: datetime):
    calendario = []
    dia_atual = data_inicio

    # buscar horários, bloqueios e reservas
    horarios = listar_horarios(db, parceiro_id)
    bloqueios = listar_bloqueios(db, parceiro_id)
    reservas = db.query(Reserva).filter(
        Reserva.parceiro_id == parceiro_id,
        Reserva.servico_id == servico_id,
        Reserva.data_inicio >= data_inicio,
        Reserva.data_fim <= data_fim,
        Reserva.status != StatusReserva.cancelada
    ).all()

    while dia_atual <= data_fim:
        dia_semana = dia_atual.weekday()

        # verificar se está fechado
        horario_dia = next(
            (h for h in horarios if h.dia_semana.value == dia_semana and h.ativo),
            None
        )

        if not horario_dia:
            calendario.append({
                "data": dia_atual.strftime("%Y-%m-%d"),
                "estado": "fechado",
                "motivo": "Fora do horário de funcionamento"
            })
            dia_atual += timedelta(days=1)
            continue

        # verificar bloqueios
        bloqueio = next(
            (b for b in bloqueios
             if b.data_inicio <= dia_atual <= b.data_fim
             and (b.servico_id is None or b.servico_id == servico_id)),
            None
        )

        if bloqueio:
            calendario.append({
                "data": dia_atual.strftime("%Y-%m-%d"),
                "estado": "bloqueado",
                "motivo": bloqueio.descricao or bloqueio.motivo.value
            })
            dia_atual += timedelta(days=1)
            continue

        # verificar reservas
        reserva = next(
            (r for r in reservas
             if r.data_inicio.date() <= dia_atual.date() <= r.data_fim.date()),
            None
        )

        if reserva:
            estado = "ocupado" if reserva.status == StatusReserva.confirmada else "pendente"
            calendario.append({
                "data": dia_atual.strftime("%Y-%m-%d"),
                "estado": estado,
                "motivo": None,
                "reserva_id": reserva.id
            })
        else:
            calendario.append({
                "data": dia_atual.strftime("%Y-%m-%d"),
                "estado": "disponivel",
                "motivo": None
            })

        dia_atual += timedelta(days=1)

    return calendario