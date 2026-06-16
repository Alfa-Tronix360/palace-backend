from sqlalchemy.orm import Session
from app.repositories.parceiro_repository import (
    listar_parceiros,
    listar_parceiros_pendentes,
    buscar_parceiro,
    buscar_parceiro_por_usuario,
    listar_parceiros_por_tipo,
    criar_parceiro,
    aprovar_parceiro,
    atualizar_parceiro,
    pesquisar_parceiros,
    deletar_parceiro
)
from app.repositories.servico_repository import pesquisar_servicos
from app.repositories.usuario_repository import buscar_usuario_por_email, criar_usuario_com_hash
from app.schemas.schemas import ParceiroCreate, ParceiroRegistoCreate, ParceiroAprovar
from app.core.security import hash_senha
from app.models.models import RoleUsuario, EstadoParceiro

def service_listar_parceiros(db: Session):
    return listar_parceiros(db)

def service_listar_parceiros_pendentes(db: Session):
    return listar_parceiros_pendentes(db)

def service_buscar_parceiro(db: Session, parceiro_id: int):
    parceiro = buscar_parceiro(db, parceiro_id)
    if not parceiro:
        raise ValueError("Parceiro não encontrado")
    return parceiro

def service_buscar_parceiro_por_usuario(db: Session, usuario_id: int):
    parceiro = buscar_parceiro_por_usuario(db, usuario_id)
    if not parceiro:
        raise ValueError("Parceiro não encontrado")
    return parceiro

def service_listar_parceiros_por_tipo(db: Session, tipo: str):
    return listar_parceiros_por_tipo(db, tipo)

def service_registar_parceiro(db: Session, dados: ParceiroRegistoCreate, lingua: str = "pt"):
    # verificar se aceitou os termos
    if not dados.aceitou_termos:
        raise ValueError("Deve aceitar os termos e condições para se registar")

    # verificar se o email já existe
    existente = buscar_usuario_por_email(db, dados.email)
    if existente:
        raise ValueError("Email já registado")

    # criar utilizador com role parceiro
    from app.schemas.schemas import UsuarioCreate
    usuario_data = UsuarioCreate(
        nome=dados.nome_responsavel,
        email=dados.email,
        senha=dados.senha,
         telefone=dados.telefone,
        role=RoleUsuario.parceiro
    )
    senha_hash = hash_senha(dados.senha)
    usuario = criar_usuario_com_hash(db, usuario_data, senha_hash)

    # criar parceiro com estado aprovado automaticamente
    parceiro_data = ParceiroCreate(
        nome=dados.nome_negocio,
        tipo=dados.tipo,
        telefone=dados.telefone,
        localizacao=dados.localizacao,
        nif=dados.nif,
        email=dados.email
    )
    parceiro = criar_parceiro(db, parceiro_data, usuario.id)

    # aprovar automaticamente
    parceiro.estado = EstadoParceiro.aprovado
    db.commit()
    db.refresh(parceiro)

    # criar trial de 30 dias automaticamente
    from app.repositories.subscricao_repository import criar_subscricao_trial
    criar_subscricao_trial(db, parceiro.id)

    return parceiro

def service_aprovar_parceiro(db: Session, parceiro_id: int, dados: ParceiroAprovar):
    parceiro = aprovar_parceiro(db, parceiro_id, dados.estado)
    if not parceiro:
        raise ValueError("Parceiro não encontrado")
    if dados.estado.value == "aprovado":
        from app.repositories.subscricao_repository import criar_subscricao_trial
        criar_subscricao_trial(db, parceiro.id)
    return parceiro

def service_atualizar_parceiro(db: Session, parceiro_id: int, dados: ParceiroCreate):
    atualizado = atualizar_parceiro(db, parceiro_id, dados)
    if not atualizado:
        raise ValueError("Parceiro não encontrado")
    return atualizado

def service_pesquisar(
    db: Session,
    tipo: str = None,
    localizacao: str = None,
    preco_min: float = None,
    preco_max: float = None,
    capacidade: int = None,
    data_inicio=None,
    data_fim=None
):
    parceiros = pesquisar_parceiros(db, tipo=tipo, localizacao=localizacao)
    resultado = []
    for parceiro in parceiros:
        servicos = pesquisar_servicos(
            db,
            parceiro_id=parceiro.id,
            preco_min=preco_min,
            preco_max=preco_max,
            capacidade=capacidade
        )
        if data_inicio and data_fim and servicos:
            from app.repositories.reserva_repository import verificar_disponibilidade
            servicos = [
                s for s in servicos
                if verificar_disponibilidade(db, s.id, data_inicio, data_fim)
            ]
        if servicos:
            resultado.append({
                "parceiro": parceiro,
                "servicos": servicos
            })
    return resultado

def service_deletar_parceiro(db: Session, parceiro_id: int):
    deletado = deletar_parceiro(db, parceiro_id)
    if not deletado:
        raise ValueError("Parceiro não encontrado")
    return deletado