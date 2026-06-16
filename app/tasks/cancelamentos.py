from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Reserva, StatusReserva
from app.integrations.email import email_cancelamento_reserva
from app.integrations.whatsapp import whatsapp_cancelamento_cliente

async def cancelar_reservas_pendentes():
    db: Session = SessionLocal()
    try:
        agora = datetime.utcnow()
        limite = agora - timedelta(hours=2)

        # reservas pendentes há mais de 2 horas
        reservas = db.query(Reserva).filter(
            Reserva.status == StatusReserva.pendente,
            Reserva.criado_em <= limite
        ).all()

        for reserva in reservas:
            # cancelar automaticamente
            reserva.status = StatusReserva.cancelada
            db.commit()

            # buscar cliente e parceiro
            from app.repositories.usuario_repository import buscar_usuario
            from app.repositories.parceiro_repository import buscar_parceiro

            cliente = buscar_usuario(db, reserva.usuario_id)
            parceiro = buscar_parceiro(db, reserva.parceiro_id)

            # notificar cliente
            if cliente and cliente.email:
                await email_cancelamento_reserva(
                    email=cliente.email,
                    nome=cliente.nome,
                    nome_negocio=parceiro.nome if parceiro else "—",
                    data_inicio=str(reserva.data_inicio)
                )

            if cliente and cliente.telefone:
                await whatsapp_cancelamento_cliente(
                    telefone=cliente.telefone,
                    cliente_nome=cliente.nome,
                    nome_negocio=parceiro.nome if parceiro else "—",
                    data_inicio=str(reserva.data_inicio)
                )

        print(f"[Cancelamentos] {len(reservas)} reservas canceladas às {agora}")

    except Exception as e:
        print(f"[Cancelamentos] Erro: {e}")
    finally:
        db.close()