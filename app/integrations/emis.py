import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# ====================================
# CONFIGURAÇÃO EMIS/MULTICAIXA EXPRESS
# ====================================
# Preencher quando tiver a certificação da API

EMIS_API_URL = os.environ.get("EMIS_API_URL", "")
EMIS_API_KEY = os.environ.get("EMIS_API_KEY", "")
EMIS_MERCHANT_ID = os.environ.get("EMIS_MERCHANT_ID", "")
EMIS_TERMINAL_ID = os.environ.get("EMIS_TERMINAL_ID", "")

# ====================================
# FUNÇÕES PRINCIPAIS
# ====================================

async def iniciar_pagamento(
    referencia: str,
    valor: float,
    descricao: str,
    telefone: str = None
) -> dict:
    """
    Inicia um pagamento via Multicaixa Express.
    Retorna a referência de pagamento e o link/código para o cliente pagar.
    """
    if not EMIS_API_KEY:
        print("[EMIS] API não configurada — pagamento simulado")
        return {
            "sucesso": False,
            "mensagem": "API EMIS não configurada",
            "referencia": referencia
        }

    # TODO: implementar quando tiver certificação
    # headers = {
    #     "Authorization": f"Bearer {EMIS_API_KEY}",
    #     "Content-Type": "application/json"
    # }
    # payload = {
    #     "merchant_id": EMIS_MERCHANT_ID,
    #     "terminal_id": EMIS_TERMINAL_ID,
    #     "referencia": referencia,
    #     "valor": valor,
    #     "descricao": descricao,
    #     "telefone": telefone
    # }
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(f"{EMIS_API_URL}/pagamentos", json=payload, headers=headers)
    #     return response.json()

    pass

async def verificar_pagamento(referencia: str) -> dict:
    """
    Verifica se um pagamento foi efectuado.
    """
    if not EMIS_API_KEY:
        print("[EMIS] API não configurada — verificação simulada")
        return {
            "sucesso": False,
            "mensagem": "API EMIS não configurada",
            "referencia": referencia,
            "pago": False
        }

    # TODO: implementar quando tiver certificação
    pass

async def reembolsar_pagamento(referencia: str, valor: float) -> dict:
    """
    Reembolsa um pagamento efectuado.
    """
    if not EMIS_API_KEY:
        print("[EMIS] API não configurada — reembolso simulado")
        return {
            "sucesso": False,
            "mensagem": "API EMIS não configurada",
            "referencia": referencia
        }

    # TODO: implementar quando tiver certificação
    pass