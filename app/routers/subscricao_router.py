from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import SubscricaoCreate, SubscricaoResponse, SubscricaoUpdateEstado, SolicitacaoPlanoCreate, SolicitacaoPlanoResponse
from app.core.dependencies import get_usuario_atual, get_admin, get_parceiro
from app.core.config import PRECOS_PLANOS, DESCRICAO_PLANOS
from app.models.models import Usuario, PlanoSubscricao
from app.services.subscricao_service import (
    service_criar_subscricao,
    service_buscar_subscricao_ativa,
    service_listar_subscricoes,
    service_listar_subscricoes_por_parceiro,
    service_atualizar_estado_subscricao,
    service_verificar_subscricao_ativa
)

router = APIRouter(prefix="/subscricoes", tags=["Subscricoes"])

# público — ver planos disponíveis
@router.get("/planos")
def listar_planos():
    return [
        {
            "plano": plano.value,
            "valor_mensal": PRECOS_PLANOS[plano],
            "descricao": DESCRICAO_PLANOS[plano]
        }
        for plano in PlanoSubscricao
        if plano.value != "trial"
    ]

# parceiro — solicitar upgrade de plano
@router.post("/solicitar-plano")
def solicitar_plano(
    dados: SolicitacaoPlanoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_parceiro)
):
    from app.services.parceiro_service import service_buscar_parceiro_por_usuario
    parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
    plano = dados.plano
    return {
        "mensagem": f"Solicitação de upgrade para o plano {plano.value} recebida. O admin irá contactá-lo em breve.",
        "parceiro": parceiro.nome,
        "plano": plano.value,
        "valor_mensal": PRECOS_PLANOS[plano],
        "descricao": DESCRICAO_PLANOS[plano]
    }

# admin — listar todas as subscrições
@router.get("/", response_model=list[SubscricaoResponse])
def listar(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin)):
    return service_listar_subscricoes(db)

# admin — criar subscrição paga manualmente
@router.post("/", response_model=SubscricaoResponse, status_code=201)
def criar(subscricao: SubscricaoCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin)):
    return service_criar_subscricao(db, subscricao)

# admin — atualizar estado da subscrição
@router.patch("/{subscricao_id}/estado", response_model=SubscricaoResponse)
def atualizar_estado(subscricao_id: int, dados: SubscricaoUpdateEstado, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin)):
    try:
        return service_atualizar_estado_subscricao(db, subscricao_id, dados)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# parceiro — ver a sua subscrição ativa
@router.get("/minha", response_model=SubscricaoResponse)
def minha_subscricao(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    try:
        from app.services.parceiro_service import service_buscar_parceiro_por_usuario
        parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
        return service_buscar_subscricao_ativa(db, parceiro.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# parceiro — ver histórico de subscrições
@router.get("/historico", response_model=list[SubscricaoResponse])
def historico(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_parceiro)):
    from app.services.parceiro_service import service_buscar_parceiro_por_usuario
    parceiro = service_buscar_parceiro_por_usuario(db, usuario_atual.id)
    return service_listar_subscricoes_por_parceiro(db, parceiro.id)

# admin — ver subscrições de um parceiro específico
@router.get("/parceiro/{parceiro_id}", response_model=list[SubscricaoResponse])
def listar_por_parceiro(parceiro_id: int, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_admin)):
    return service_listar_subscricoes_por_parceiro(db, parceiro_id)

# público — verificar se parceiro tem subscrição ativa
@router.get("/verificar/{parceiro_id}")
def verificar(parceiro_id: int, db: Session = Depends(get_db)):
    ativo = service_verificar_subscricao_ativa(db, parceiro_id)
    return {"ativo": ativo}