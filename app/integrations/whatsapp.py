import os
import httpx
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

async def enviar_whatsapp(telefone: str, mensagem: str):
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print(f"[WhatsApp] Token ou Phone Number ID não configurado — mensagem não enviada para {telefone}")
        return


    telefone_limpo = telefone.replace("+", "").replace(" ", "").replace("-", "")
    

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
    "messaging_product": "whatsapp",
    "to": telefone_limpo,
    "type": "template",
    "template": {
        "name": "hello_world",
        "language": {
            "code": "en_US"
             }
       }
    }


    async with httpx.AsyncClient() as client:
        response = await client.post(WHATSAPP_API_URL, json=payload, headers=headers)
        print(f"[WhatsApp] Status: {response.status_code} — {response.text}")

# ====================================
# TEMPLATES DE WHATSAPP
# ====================================

async def whatsapp_nova_reserva_cliente(telefone: str, cliente_nome: str, nome_negocio: str, servico: str, data_inicio: str, data_fim: str, total_preco: float):
    mensagem = (
        f"Olá {cliente_nome}! 👋\n\n"
        f"A sua reserva foi recebida e aguarda confirmação.\n\n"
        f"🏨 *Negócio:* {nome_negocio}\n"
        f"🛎 *Serviço:* {servico}\n"
        f"📅 *Check-in:* {data_inicio}\n"
        f"📅 *Check-out:* {data_fim}\n"
        f"💰 *Total:* {total_preco} Kz\n\n"
        f"Obrigado por usar o ReservaAO! 🇦🇴"
    )
    await enviar_whatsapp(telefone, mensagem)

async def whatsapp_confirmacao_reserva_cliente(telefone: str, cliente_nome: str, nome_negocio: str, data_inicio: str):
    mensagem = (
        f"✅ Olá {cliente_nome}!\n\n"
        f"A sua reserva em *{nome_negocio}* foi *confirmada*!\n\n"
        f"📅 *Data:* {data_inicio}\n\n"
        f"Obrigado por usar o ReservaAO! 🇦🇴"
    )
    await enviar_whatsapp(telefone, mensagem)

async def whatsapp_cancelamento_cliente(telefone: str, cliente_nome: str, nome_negocio: str, data_inicio: str):
    mensagem = (
        f"❌ Olá {cliente_nome}!\n\n"
        f"A sua reserva em *{nome_negocio}* foi *cancelada*.\n\n"
        f"📅 *Data:* {data_inicio}\n\n"
        f"Entre em contacto connosco para mais informações."
    )
    await enviar_whatsapp(telefone, mensagem)

async def whatsapp_nova_reserva_parceiro(telefone: str, nome_negocio: str, cliente_nome: str, servico: str, data_inicio: str, data_fim: str):
    mensagem = (
        f"🔔 Nova Reserva — *{nome_negocio}*\n\n"
        f"👤 *Cliente:* {cliente_nome}\n"
        f"🛎 *Serviço:* {servico}\n"
        f"📅 *Check-in:* {data_inicio}\n"
        f"📅 *Check-out:* {data_fim}\n\n"
        f"Aceda ao painel para confirmar ou rejeitar."
    )
    await enviar_whatsapp(telefone, mensagem)

async def whatsapp_cancelamento_parceiro(telefone: str, nome_negocio: str, cliente_nome: str, servico: str, data_inicio: str):
    mensagem = (
        f"❌ Reserva Cancelada — *{nome_negocio}*\n\n"
        f"👤 *Cliente:* {cliente_nome}\n"
        f"🛎 *Serviço:* {servico}\n"
        f"📅 *Data:* {data_inicio}\n\n"
        f"A reserva foi cancelada pelo cliente."
    )
    await enviar_whatsapp(telefone, mensagem)

async def whatsapp_boas_vindas_parceiro(telefone: str, nome_responsavel: str, nome_negocio: str):
    mensagem = (
        f" Bem-vindo ao ReservaAO, {nome_responsavel}!\n\n"
        f"O *{nome_negocio}* foi registado com sucesso.\n\n"
        f"Tem *30 dias gratuitos* para explorar todas as funcionalidades.\n\n"
        f"Obrigado por escolher o ReservaAO! 🇦🇴"
    )
    await enviar_whatsapp(telefone, mensagem)


async def whatsapp_lembrete_reserva(telefone: str, cliente_nome: str, nome_negocio: str, servico: str, data_inicio: str):
    mensagem = (
        f"🔔 Lembrete de Reserva!\n\n"
        f"Olá {cliente_nome}! A sua reserva é amanhã.\n\n"
        f"🏨 *Negócio:* {nome_negocio}\n"
        f"🛎 *Serviço:* {servico}\n"
        f"📅 *Data:* {data_inicio}\n\n"
        f"Obrigado por usar o ReservaAO! 🇦🇴"
    )
    await enviar_whatsapp(telefone, mensagem)    