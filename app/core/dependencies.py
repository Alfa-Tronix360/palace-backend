from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.security import verificar_token
from app.models.models import Usuario, RoleUsuario
from app.core.i18n import traduzir

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_lingua(accept_language: Optional[str] = Header(default="pt")) -> str:
    if not accept_language:
        return "pt"
    lingua = accept_language.split(",")[0].strip()[:2]
    return lingua if lingua in ["pt", "en", "fr", "ar"] else "pt"

def get_usuario_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    lingua: str = Depends(get_lingua)
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=traduzir("token_invalido", lingua),
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verificar_token(token)
    if payload is None:
        raise credentials_exception

    usuario_id: int = payload.get("sub")
    if usuario_id is None:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    if usuario is None:
        raise credentials_exception

    return usuario

def get_admin(
    usuario_atual: Usuario = Depends(get_usuario_atual),
    lingua: str = Depends(get_lingua)
) -> Usuario:
    if usuario_atual.role not in [RoleUsuario.admin, RoleUsuario.parceiro]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=traduzir("acesso_negado_admin", lingua)
        )
    return usuario_atual

def get_parceiro(
    usuario_atual: Usuario = Depends(get_usuario_atual),
    lingua: str = Depends(get_lingua)
) -> Usuario:
    if usuario_atual.role not in [RoleUsuario.parceiro, RoleUsuario.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=traduzir("acesso_negado_parceiro", lingua)
        )
    return usuario_atual

def get_staff(
    usuario_atual: Usuario = Depends(get_usuario_atual),
    lingua: str = Depends(get_lingua)
) -> Usuario:
    if usuario_atual.role not in [RoleUsuario.staff, RoleUsuario.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=traduzir("acesso_negado_staff", lingua)
        )
    return usuario_atual
