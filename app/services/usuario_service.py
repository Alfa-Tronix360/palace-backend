from sqlalchemy.orm import Session
from app.repositories.usuario_repository import (
    listar_usuarios,
    buscar_usuario,
    buscar_usuario_por_email,
    criar_usuario_com_hash,
    atualizar_usuario,
    deletar_usuario
)
from app.schemas.schemas import UsuarioCreate
from app.core.security import hash_senha
from app.core.i18n import traduzir

def service_listar_usuarios(db: Session):
    return listar_usuarios(db)

def service_buscar_usuario(db: Session, usuario_id: int, lingua: str = "pt"):
    usuario = buscar_usuario(db, usuario_id)
    if not usuario:
        raise ValueError(traduzir("utilizador_nao_encontrado", lingua))
    return usuario

def service_criar_usuario(db: Session, usuario: UsuarioCreate, lingua: str = "pt"):
    existente = buscar_usuario_por_email(db, usuario.email)
    if existente:
        raise ValueError(traduzir("email_ja_registado", lingua))
    senha_hash = hash_senha(usuario.senha)
    return criar_usuario_com_hash(db, usuario, senha_hash)

def service_atualizar_usuario(db: Session, usuario_id: int, dados: UsuarioCreate, lingua: str = "pt"):
    if dados.senha:
        dados.senha = hash_senha(dados.senha)
    atualizado = atualizar_usuario(db, usuario_id, dados)
    if not atualizado:
        raise ValueError(traduzir("utilizador_nao_encontrado", lingua))
    return atualizado

def service_deletar_usuario(db: Session, usuario_id: int, lingua: str = "pt"):
    deletado = deletar_usuario(db, usuario_id)
    if not deletado:
        raise ValueError(traduzir("utilizador_nao_encontrado", lingua))
    return deletado
