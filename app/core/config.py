from app.models.models import PlanoSubscricao

PRECOS_PLANOS = {
    PlanoSubscricao.trial: 0.0,
    PlanoSubscricao.basic: 15000.0,
    PlanoSubscricao.pro: 35000.0,
    PlanoSubscricao.enterprise: 0.0  # negociado
}

DESCRICAO_PLANOS = {
    PlanoSubscricao.trial: "30 dias gratuito — todas as funcionalidades",
    PlanoSubscricao.basic: "1 unidade, reservas ilimitadas — 15.000 Kz/mês",
    PlanoSubscricao.pro: "1 unidade, relatórios avançados — 35.000 Kz/mês",
    PlanoSubscricao.enterprise: "Múltiplas unidades, API dedicada — preço negociado"
}