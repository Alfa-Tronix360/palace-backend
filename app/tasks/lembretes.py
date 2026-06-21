from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import PalaceReservation, StatusReserva, Usuario
from app.integrations.email import email_lembrete_reserva
from app.tasks.palace_tasks import marcar_noshows, enviar_lembretes_palace, cancelar_reservas_expiradas


try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except ModuleNotFoundError:
    AsyncIOScheduler = None
    IntervalTrigger = None

scheduler = AsyncIOScheduler() if AsyncIOScheduler else None

async def verificar_lembretes():
    db: Session = SessionLocal()
    try:
        agora = datetime.utcnow()
        amanha = agora + timedelta(hours=24)

        reservas = db.query(PalaceReservation).filter(
            PalaceReservation.status == StatusReserva.confirmada,
            PalaceReservation.starts_at >= agora,
            PalaceReservation.starts_at <= amanha
        ).all()

        for reserva in reservas:
            cliente = db.query(Usuario).filter(Usuario.id == reserva.client_id).first()
            if cliente and cliente.email:
                await email_lembrete_reserva(
                    cliente_email=cliente.email,
                    cliente_nome=cliente.nome,
                    nome_negocio="Palace Lounge",
                    servico=f"Mesa {reserva.table.number}" if reserva.table else "Mesa",
                    data_inicio=str(reserva.starts_at)
                )
                print(f"[Lembretes] Email enviado para {cliente.email}")

        print(f"[Lembretes] {len(reservas)} lembretes enviados às {agora}")

    except Exception as e:
        print(f"[Lembretes] Erro: {e}")
    finally:
        db.close()

async def verificar_subscricoes_expiradas():
    db: Session = SessionLocal()
    try:
        from app.services.subscricao_service import service_expirar_subscricoes
        total = service_expirar_subscricoes(db)
        print(f"[Subscrições] {total} subscrições expiradas às {datetime.utcnow()}")
    except Exception as e:
        print(f"[Subscrições] Erro: {e}")
    finally:
        db.close()

def iniciar_scheduler():
    if not scheduler or not IntervalTrigger:
        print("[Scheduler] Desativado: apscheduler nao instalado")
        return

    scheduler.add_job(
        enviar_lembretes_palace,
        IntervalTrigger(hours=1),
        id="lembretes_palace",
        replace_existing=True
    )

    scheduler.add_job(
        marcar_noshows,
        IntervalTrigger(minutes=15),
        id="noshows",
        replace_existing=True
    )

    scheduler.add_job(
        cancelar_reservas_expiradas,
        IntervalTrigger(hours=1),
        id="cancelamentos_palace",
        replace_existing=True
    )

    scheduler.start()
    print("[Scheduler] Iniciado — lembretes, no-shows e cancelamentos activos")