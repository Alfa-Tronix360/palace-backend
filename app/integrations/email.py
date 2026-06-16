from pydantic import EmailStr
import os
from dotenv import load_dotenv

try:
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
except ModuleNotFoundError:
    FastMail = None
    MessageSchema = None
    ConnectionConfig = None

load_dotenv()

conf = None
fastmail = None

if ConnectionConfig and FastMail:
    conf = ConnectionConfig(
        MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
        MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
        MAIL_FROM=os.environ.get("MAIL_FROM"),
        MAIL_PORT=587,
        MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True
    )
    fastmail = FastMail(conf)

async def enviar_email(destinatario: str, assunto: str, corpo: str):
    if not fastmail or not MessageSchema:
        return {
            "simulado": True,
            "destinatario": destinatario,
            "assunto": assunto,
        }

    mensagem = MessageSchema(
        subject=assunto,
        recipients=[destinatario],
        body=corpo,
        subtype="html"
    )
    await fastmail.send_message(mensagem)


async def email_boas_vindas_parceiro(parceiro_email: str, nome_negocio: str, nome_responsavel: str):
    await enviar_email(
        destinatario=parceiro_email,
        assunto="Bem-vindo ao ReservaAO!",
        corpo=f"""
        <h2>Bem-vindo ao ReservaAO, {nome_responsavel}!</h2>
        <p>O <strong>{nome_negocio}</strong> foi registado com sucesso na nossa plataforma.</p>
        <p>Tem <strong>30 dias gratuitos</strong> para explorar todas as funcionalidades.</p>
        <br>
        <p>O que pode fazer agora:</p>
        <ul>
            <li>Configurar o perfil do seu negócio</li>
            <li>Adicionar os seus serviços</li>
            <li>Começar a receber reservas</li>
        </ul>
        <br>
        <p>Obrigado por escolher o ReservaAO!</p>
        <p><strong>Equipa ReservaAO</strong></p>
        """
    )    

# ====================================
# TEMPLATES DE EMAIL
# ====================================

async def email_registo_parceiro_admin(admin_email: str, nome_negocio: str, nome_responsavel: str):
    await enviar_email(
        destinatario=admin_email,
        assunto="Novo parceiro registado na plataforma",
        corpo=f"""
        <h2>Novo Parceiro Registado</h2>
        <p>O negócio <strong>{nome_negocio}</strong> registou-se na plataforma.</p>
        <p><strong>Responsável:</strong> {nome_responsavel}</p>
        <p>O parceiro aceitou os termos e condições e já tem acesso à plataforma com 30 dias de trial.</p>
        """
    )

async def email_estado_parceiro(parceiro_email: str, nome_negocio: str, aprovado: bool):
    status = "reativado" if aprovado else "suspenso"
    mensagem = "Já pode voltar a receber reservas." if aprovado else "Entre em contacto connosco para mais informações."
    await enviar_email(
        destinatario=parceiro_email,
        assunto=f"A sua conta foi {status}",
        corpo=f"""
        <h2>{nome_negocio} — {status.capitalize()}</h2>
        <p>{mensagem}</p>
        <p><strong>Equipa ReservaAO</strong></p>
        """
    )

async def email_nova_reserva_parceiro(parceiro_email: str, nome_negocio: str, cliente_nome: str, data_inicio: str, data_fim: str, servico: str):
    await enviar_email(
        destinatario=parceiro_email,
        assunto="Nova reserva recebida",
        corpo=f"""
        <h2>Nova Reserva — {nome_negocio}</h2>
        <p><strong>Cliente:</strong> {cliente_nome}</p>
        <p><strong>Serviço:</strong> {servico}</p>
        <p><strong>Check-in:</strong> {data_inicio}</p>
        <p><strong>Check-out:</strong> {data_fim}</p>
        <p>Aceda ao painel para confirmar ou rejeitar.</p>
        """
    )

async def email_nova_reserva_cliente(cliente_email: str, cliente_nome: str, nome_negocio: str, servico: str, data_inicio: str, data_fim: str, total_preco: float):
    await enviar_email(
        destinatario=cliente_email,
        assunto="Reserva recebida — aguarda confirmação",
        corpo=f"""
        <h2>Olá, {cliente_nome}!</h2>
        <p>A sua reserva foi recebida e aguarda confirmação.</p>
        <p><strong>Negócio:</strong> {nome_negocio}</p>
        <p><strong>Serviço:</strong> {servico}</p>
        <p><strong>Check-in:</strong> {data_inicio}</p>
        <p><strong>Check-out:</strong> {data_fim}</p>
        <p><strong>Total:</strong> {total_preco} Kz</p>
        """
    )

async def email_confirmacao_reserva_cliente(cliente_email: str, cliente_nome: str, nome_negocio: str, data_inicio: str):
    await enviar_email(
        destinatario=cliente_email,
        assunto="Reserva confirmada!",
        corpo=f"""
        <h2>Reserva Confirmada!</h2>
        <p>Olá, {cliente_nome}! A sua reserva em <strong>{nome_negocio}</strong> foi confirmada.</p>
        <p><strong>Data:</strong> {data_inicio}</p>
        <p>Obrigado por usar o ReservaAO!</p>
        """
    )

async def email_cancelamento_reserva(email: str, nome: str, nome_negocio: str, data_inicio: str):
    await enviar_email(
        destinatario=email,
        assunto="Reserva cancelada",
        corpo=f"""
        <h2>Reserva Cancelada</h2>
        <p>Olá, {nome}! A reserva em <strong>{nome_negocio}</strong> foi cancelada.</p>
        <p><strong>Data:</strong> {data_inicio}</p>
        <p>Entre em contacto connosco para mais informações.</p>
        """
    )


async def email_cancelamento_parceiro(parceiro_email: str, nome_negocio: str, cliente_nome: str, servico: str, data_inicio: str):
    await enviar_email(
        destinatario=parceiro_email,
        assunto="Reserva cancelada pelo cliente",
        corpo=f"""
        <h2>Reserva Cancelada — {nome_negocio}</h2>
        <p><strong>Cliente:</strong> {cliente_nome}</p>
        <p><strong>Serviço:</strong> {servico}</p>
        <p><strong>Data:</strong> {data_inicio}</p>
        <p>A reserva foi cancelada pelo cliente.</p>
        <p><strong>Equipa ReservaAO</strong></p>
        """
    )    
    
async def email_lembrete_reserva(cliente_email: str, cliente_nome: str, nome_negocio: str, servico: str, data_inicio: str):
    await enviar_email(
        destinatario=cliente_email,
        assunto="Lembrete — A sua reserva é amanhã!",
        corpo=f"""
        <h2>Lembrete de Reserva 🔔</h2>
        <p>Olá {cliente_nome}! A sua reserva é amanhã.</p>
        <p><strong>Negócio:</strong> {nome_negocio}</p>
        <p><strong>Serviço:</strong> {servico}</p>
        <p><strong>Data:</strong> {data_inicio}</p>
        <p>Obrigado por usar o ReservaAO! 🇦🇴</p>
        """
    )

async def email_boas_vindas_cliente(cliente_email: str, cliente_nome: str, nome_negocio: str = "Palace Lounge"):
    await enviar_email(
        destinatario=cliente_email,
        assunto=f"Bem-vindo ao {nome_negocio}!",
        corpo=f"""
        <h2>Bem-vindo, {cliente_nome}!</h2>
        <p>A sua conta no <strong>{nome_negocio}</strong> foi criada com sucesso.</p>
        <p>Já pode fazer login e começar a reservar mesas e eventos.</p>
        <br>
        <p>Obrigado por se juntar a nós!</p>
        <p><strong>Equipa {nome_negocio}</strong></p>
        <br>
        <p>Para mais servicos contacte clacstecnologia.com</p>
        """
    )