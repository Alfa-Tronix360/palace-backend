from app.core.i18n import pt, en, fr, ar

LINGUAS_DISPONIVEIS = ["pt", "en", "fr", "ar"]
LINGUA_PADRAO = "pt"

TRADUCOES = {
    "pt": pt.MESSAGES,
    "en": en.MESSAGES,
    "fr": fr.MESSAGES,
    "ar": ar.MESSAGES,
}

def traduzir(chave: str, lingua: str = LINGUA_PADRAO) -> str:
    if lingua not in LINGUAS_DISPONIVEIS:
        lingua = LINGUA_PADRAO
    return TRADUCOES[lingua].get(chave, TRADUCOES[LINGUA_PADRAO].get(chave, chave))