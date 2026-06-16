from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import ReservaCreate, ReservaResponse, ReservaUpdateStatus
from app.core.dependencies import get_usuario_atual, get_admin, get_parceiro, get_lingua
from app.models.models import Usuario
from app.services.reserva_service import (
    service_listar_reservas,
    service_buscar_reserva,
    service_listar_reservas_por_usuario,
    service_listar_reservas_por_parceiro,
    service_verificar_disponibilidade,
    service_criar_reserva,
    service_atualizar_reserva,
    service_atualizar_status_reserva,
    service_deletar_reserva
)
from app.services.parceiro_service import service_buscar_parceiro_por_usuario
from app.services.usuario_service import service_buscar_usuario
from app.core.i18n import traduzir
from app.integrations.email import (
    email_nova_reserva_parceiro,
    email_nova_reserva_cliente,
    email_confirmacao_reserva_cliente,
    email_cancelamento_reserva,
    email_cancelamento_parceiro
)
from app.integrations.whatsapp import (
    whatsapp_nova_reserva_cliente,
    whatsapp_nova_reserva_parceiro,
    whatsapp_confirmacao_reserva_cliente,
    whatsapp_cancelamento_cliente,
    whatsapp_cancelamento_parceiro
)

router = APIRouter(prefix="/reservas", tags=["Reservas"])

@router.get("/", response_model=list[ReservaResponse])
def listar(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin)):
    return service_listar_reservas(db)

@router.get("/minhas", response_model=list[ReservaResponse])
def listar_minhas(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_usuario_atual)):
    return service_listar_reservas_por_usuario(db, usuario_atual.id)

@router.get("/meu-negocio", response_model=list[ReservaResponse])
def listar_meu_negocio(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    try:
        parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
        return service_listar_reservas_por_parceiro(db, parceiro.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/disponibilidade")
def verificar_disponibilidade(
    servico_id: int,
    data_inicio: str,
    data_fim: str,
    db: Session = Depends(get_db)
):
    from datetime import datetime
    inicio = datetime.fromisoformat(data_inicio)
    fim = datetime.fromisoformat(data_fim)
    disponivel = service_verificar_disponibilidade(db, servico_id, inicio, fim)
    return {"disponivel": disponivel}

@router.get("/parceiro/{parceiro_id}", response_model=list[ReservaResponse])
def listar_por_parceiro(parceiro_id: int, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin)):
    return service_listar_reservas_por_parceiro(db, parceiro_id)

@router.get("/{reserva_id}", response_model=ReservaResponse)
def buscar(reserva_id: int, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_usuario_atual), lingua: str = Depends(get_lingua)):
    try:
        return service_buscar_reserva(db, reserva_id, lingua)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/", response_model=ReservaResponse, status_code=201)
async def criar(
    reserva: ReservaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    lingua: str = Depends(get_lingua)
):
    try:
        nova_reserva = service_criar_reserva(db, reserva, usuario_atual.id, lingua)

        # buscar dados para notificação
        from app.repositories.parceiro_repository import buscar_parceiro
        from app.repositories.servico_repository import buscar_servico
        parceiro = buscar_parceiro(db, reserva.parceiro_id)
        servico = buscar_servico(db, reserva.servico_id)

        # ── EMAIL: notificar parceiro ──
        if parceiro and parceiro.email:
            await email_nova_reserva_parceiro(
                parceiro_email=parceiro.email,
                nome_negocio=parceiro.nome,
                cliente_nome=usuario_atual.nome,
                data_inicio=str(reserva.data_inicio),
                data_fim=str(reserva.data_fim),
                servico=servico.nome if servico else "—"
            )

        # ── EMAIL: notificar cliente ──
        if usuario_atual.email:
            await email_nova_reserva_cliente(
                cliente_email=usuario_atual.email,
                cliente_nome=usuario_atual.nome,
                nome_negocio=parceiro.nome if parceiro else "—",
                servico=servico.nome if servico else "—",
                data_inicio=str(reserva.data_inicio),
                data_fim=str(reserva.data_fim),
                total_preco=nova_reserva.total_preco
            )

        # ── WHATSAPP: notificar cliente ──
        if usuario_atual.telefone:
            await whatsapp_nova_reserva_cliente(
                telefone=usuario_atual.telefone,
                cliente_nome=usuario_atual.nome,
                nome_negocio=parceiro.nome if parceiro else "—",
                servico=servico.nome if servico else "—",
                data_inicio=str(reserva.data_inicio),
                data_fim=str(reserva.data_fim),
                total_preco=nova_reserva.total_preco
            )

        # ── WHATSAPP: notificar parceiro ──
        if parceiro and parceiro.telefone:
            await whatsapp_nova_reserva_parceiro(
                telefone=parceiro.telefone,
                nome_negocio=parceiro.nome,
                cliente_nome=usuario_atual.nome,
                servico=servico.nome if servico else "—",
                data_inicio=str(reserva.data_inicio),
                data_fim=str(reserva.data_fim)
            )

        return nova_reserva
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{reserva_id}/status", response_model=ReservaResponse)
async def atualizar_status(
    reserva_id: int,
    dados: ReservaUpdateStatus,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_parceiro),
    lingua: str = Depends(get_lingua)
):
    try:
        parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
        reserva = service_buscar_reserva(db, reserva_id, lingua)
        if reserva.parceiro_id != parceiro.id:
            raise HTTPException(status_code=403, detail="Não pode gerir reservas de outro parceiro")

        reserva_atualizada = service_atualizar_status_reserva(db, reserva_id, dados.status, lingua)

        # buscar cliente e parceiro
        from app.repositories.usuario_repository import buscar_usuario
        from app.repositories.parceiro_repository import buscar_parceiro
        cliente = buscar_usuario(db, reserva.usuario_id)
        parceiro_dados = buscar_parceiro(db, reserva.parceiro_id)

        # ── EMAIL + WHATSAPP: notificar cliente conforme status ──
        if cliente:
            if dados.status.value == "confirmada":
                if cliente.email:
                    await email_confirmacao_reserva_cliente(
                        cliente_email=cliente.email,
                        cliente_nome=cliente.nome,
                        nome_negocio=parceiro_dados.nome if parceiro_dados else "—",
                        data_inicio=str(reserva.data_inicio)
                    )
                if cliente.telefone:
                    await whatsapp_confirmacao_reserva_cliente(
                        telefone=cliente.telefone,
                        cliente_nome=cliente.nome,
                        nome_negocio=parceiro_dados.nome if parceiro_dados else "—",
                        data_inicio=str(reserva.data_inicio)
                    )

            elif dados.status.value == "cancelada":
                if cliente.email:
                    await email_cancelamento_reserva(
                        email=cliente.email,
                        nome=cliente.nome,
                        nome_negocio=parceiro_dados.nome if parceiro_dados else "—",
                        data_inicio=str(reserva.data_inicio)
                    )
                if cliente.telefone:
                    await whatsapp_cancelamento_cliente(
                        telefone=cliente.telefone,
                        cliente_nome=cliente.nome,
                        nome_negocio=parceiro_dados.nome if parceiro_dados else "—",
                        data_inicio=str(reserva.data_inicio)
                    )

        return reserva_atualizada
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{reserva_id}", response_model=ReservaResponse)
def atualizar(reserva_id: int, reserva: ReservaCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro), lingua: str = Depends(get_lingua)):
    try:
        return service_atualizar_reserva(db, reserva_id, reserva, lingua)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{reserva_id}")
def deletar(reserva_id: int, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin), lingua: str = Depends(get_lingua)):
    try:
        service_deletar_reserva(db, reserva_id, lingua)
        return {"mensagem": traduzir("reserva_eliminada", lingua)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))