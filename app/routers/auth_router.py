from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import FrontendUserResponse, TokenResponse, UsuarioCreate
from app.core.security import hash_senha, verificar_senha, criar_token, criar_refresh_token, verificar_token
from app.repositories.usuario_repository import buscar_usuario_por_email, criar_usuario_com_hash
from app.core.dependencies import get_usuario_atual
from app.core.tenant import get_company_id
from app.models.models import PalaceReservation, RoleUsuario, Usuario
from app.integrations.email import email_boas_vindas_cliente
import asyncio

router = APIRouter(prefix="/auth", tags=["Auth"])


def frontend_role(role: RoleUsuario) -> str:
    if role in [RoleUsuario.admin, RoleUsuario.parceiro]:
        return "admin"
    if role == RoleUsuario.staff:
        return "staff"
    if role in [RoleUsuario.chefe_sala, RoleUsuario.chefe_cozinha, RoleUsuario.bar]:
        return role.value
    return "client"


def to_frontend_user(usuario: Usuario, db: Session) -> FrontendUserResponse:
    palace_count = db.query(PalaceReservation).filter(PalaceReservation.client_id == usuario.id).count()
    legacy_count = len(usuario.reservas or [])
    return FrontendUserResponse(
        id=str(usuario.id),
        name=usuario.nome,
        email=usuario.email,
        phone=usuario.telefone or "",
        role=frontend_role(usuario.role),
        vip=False,
        totalSpent=0,
        reservationCount=palace_count + legacy_count,
        createdAt=usuario.criado_em,
    )


async def read_login_payload(request: Request) -> tuple[str, str]:
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        return str(form.get("username") or form.get("email") or ""), str(form.get("password") or form.get("senha") or "")
    data = await request.json()
    return str(data.get("email") or data.get("username") or ""), str(data.get("senha") or data.get("password") or "")


@router.post("/register", response_model=FrontendUserResponse, status_code=201)
async def register(usuario: UsuarioCreate, request: Request, db: Session = Depends(get_db)):
    existente = buscar_usuario_por_email(db, usuario.email)
    if existente:
        raise HTTPException(status_code=400, detail="Email já registado")
    senha_hash = hash_senha(usuario.senha)
    novo_usuario = criar_usuario_com_hash(db, usuario, senha_hash)

    # Associa à empresa
    try:
        company_id = get_company_id(request, db)
        novo_usuario.company_id = company_id
        db.commit()
    except Exception:
        pass

    asyncio.create_task(email_boas_vindas_cliente(novo_usuario.email, novo_usuario.nome))
    return to_frontend_user(novo_usuario, db)


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    email, senha = await read_login_payload(request)
    usuario = buscar_usuario_por_email(db, email)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")
    if not verificar_senha(senha, usuario.senha):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")
    access_token = criar_token({"sub": str(usuario.id)})
    refresh_token = criar_refresh_token({"sub": str(usuario.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": to_frontend_user(usuario, db),
    }


@router.post("/logout")
def logout():
    return {"message": "Sessao terminada com sucesso"}


@router.get("/me", response_model=FrontendUserResponse)
def me(usuario_atual: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    return to_frontend_user(usuario_atual, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, refresh_token: str | None = None, db: Session = Depends(get_db)):
    if refresh_token is None:
        try:
            data = await request.json()
            refresh_token = data.get("refresh_token") or data.get("refreshToken")
        except Exception:
            refresh_token = None
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalido ou expirado")
    payload = verificar_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado")
    usuario_id = payload.get("sub")
    novo_access_token = criar_token({"sub": usuario_id})
    novo_refresh_token = criar_refresh_token({"sub": usuario_id})
    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    return {
        "access_token": novo_access_token,
        "refresh_token": novo_refresh_token,
        "token_type": "bearer",
        "user": to_frontend_user(usuario, db) if usuario else None,
    }