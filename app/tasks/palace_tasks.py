from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import PalaceReservation, StatusReserva, Usuario
from app.integrations.email import email_lembrete_reserva, email_cancelamento_reserva
from app.integrations.whatsapp import enviar_whatsapp

async def marcar_noshows():
    """Marca como cancelada reservas confirmadas há mais de 15min sem check-in"""
    db: Session = SessionLocal()
    try:
        agora = datetime.utcnow()
        limite = agora - timedelta(minutes=15)
        reservas = db.query(PalaceReservation).filter(
            PalaceReservation.status == StatusReserva.confirmada,
            PalaceReservation.starts_at <= limite,
        ).all()
        for r in reservas:
            r.status = StatusReserva.cancelada
            db.commit()
            cliente = db.query(Usuario).filter(Usuario.id == r.client_id).first()
            if cliente and cliente.email:
                await email_cancelamento_reserva(
                    email=cliente.email,
                    nome=cliente.nome,
                    nome_negocio="Palace Lounge",
                    data_inicio=str(r.starts_at)
                )
        print(f"[No-show] {len(reservas)} reservas marcadas às {agora}")
    except Exception as e:
        print(f"[No-show] Erro: {e}")
    finally:
        db.close()


async def enviar_lembretes_palace():
    """Envia lembretes para reservas confirmadas nas próximas 24h"""
    db: Session = SessionLocal()
    try:
        agora = datetime.utcnow()
        amanha = agora + timedelta(hours=24)
        reservas = db.query(PalaceReservation).filter(
            PalaceReservation.status == StatusReserva.confirmada,
            PalaceReservation.starts_at >= agora,
            PalaceReservation.starts_at <= amanha,
        ).all()
        for r in reservas:
            cliente = db.query(Usuario).filter(Usuario.id == r.client_id).first()
            if cliente and cliente.email:
                await email_lembrete_reserva(
                    cliente_email=cliente.email,
                    cliente_nome=cliente.nome,
                    nome_negocio="Palace Lounge",
                    servico=f"Mesa {r.table.number}" if r.table else "Mesa",
                    data_inicio=str(r.starts_at)
                )
            if cliente and cliente.telefone:
                await enviar_whatsapp(
                    cliente.telefone,
                    f"Olá {cliente.nome}! Lembrete: tem uma reserva no Palace Lounge amanhã às {r.starts_at.strftime('%H:%M')}. Até já! 🍽️"
                )
        print(f"[Lembretes Palace] {len(reservas)} lembretes enviados às {agora}")
    except Exception as e:
        print(f"[Lembretes Palace] Erro: {e}")
    finally:
        db.close()


async def cancelar_reservas_expiradas():
    """Cancela reservas pendentes há mais de 2 horas"""
    db: Session = SessionLocal()
    try:
        agora = datetime.utcnow()
        limite = agora - timedelta(hours=2)
        reservas = db.query(PalaceReservation).filter(
            PalaceReservation.status == StatusReserva.pendente,
            PalaceReservation.created_at <= limite,
        ).all()
        for r in reservas:
            r.status = StatusReserva.cancelada
            db.commit()
            cliente = db.query(Usuario).filter(Usuario.id == r.client_id).first()
            if cliente and cliente.email:
                await email_cancelamento_reserva(
                    email=cliente.email,
                    nome=cliente.nome,
                    nome_negocio="Palace Lounge",
                    data_inicio=str(r.starts_at)
                )
        print(f"[Cancelamentos] {len(reservas)} reservas canceladas às {agora}")
    except Exception as e:
        print(f"[Cancelamentos] Erro: {e}")
    finally:
        db.close()