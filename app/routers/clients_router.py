from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_admin, get_usuario_atual
from app.core.tenant import get_company_id
from app.database import get_db
from app.models.models import PalaceReservation, RoleUsuario, Usuario
from app.schemas.schemas import FrontendUserResponse

router = APIRouter(prefix="/clients", tags=["Clients"])


def frontend_role(role: RoleUsuario) -> str:
    if role in [RoleUsuario.admin, RoleUsuario.parceiro]:
        return "admin"
    if role == RoleUsuario.staff:
        return "staff"
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


@router.get("", response_model=list[FrontendUserResponse])
@router.get("/", response_model=list[FrontendUserResponse])
def list_clients(
    request: Request,
    vip: bool | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin),
):
    company_id = get_company_id(request, db)
    query = db.query(Usuario).filter(
        Usuario.role.in_([RoleUsuario.cliente, RoleUsuario.client]),
        Usuario.company_id == company_id,
    )
    if search:
        like = f"%{search}%"
        query = query.filter(
            Usuario.nome.ilike(like) | Usuario.email.ilike(like) | Usuario.telefone.ilike(like)
        )

    clients = [to_frontend_user(usuario, db) for usuario in query.order_by(Usuario.criado_em.desc()).all()]
    if vip is not None:
        clients = [client for client in clients if client.vip == vip]
    return clients


@router.get("/me", response_model=FrontendUserResponse)
def my_client_profile(usuario_atual: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    return to_frontend_user(usuario_atual, db)


@router.get("/{client_id}", response_model=FrontendUserResponse)
def get_client(client_id: int, db: Session = Depends(get_db), _admin: Usuario = Depends(get_admin)):
    usuario = db.query(Usuario).filter(Usuario.id == client_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")
    return to_frontend_user(usuario, db)


@router.patch("/{client_id}", response_model=FrontendUserResponse)
def update_client(
    client_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin),
):
    usuario = db.query(Usuario).filter(Usuario.id == client_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")

    if "name" in payload:
        usuario.nome = payload["name"]
    if "phone" in payload:
        usuario.telefone = payload["phone"]
    if "email" in payload:
        usuario.email = payload["email"]

    db.commit()
    db.refresh(usuario)
    return to_frontend_user(usuario, db)


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin),
):
    usuario = db.query(Usuario).filter(Usuario.id == client_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")
    
    from app.models.models import PalaceReservation
    db.query(PalaceReservation).filter(PalaceReservation.client_id == client_id).delete()
    
    db.delete(usuario)
    db.commit()
    return {"message": "Cliente eliminado com sucesso"}


@router.post("/find-or-create", response_model=FrontendUserResponse)
def find_or_create_client(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    _user: Usuario = Depends(get_usuario_atual),
):
    from app.core.security import hash_senha
    name = payload.get("name", "").strip()
    phone = payload.get("phone", "").strip()
    
    if not name or not phone:
        raise HTTPException(status_code=400, detail="Nome e telefone obrigatorios")

    # Procura por telefone
    existing = db.query(Usuario).filter(Usuario.telefone == phone).first()
    if existing:
        return to_frontend_user(existing, db)

    # Cria novo cliente
    company_id = get_company_id(request, db)
    email = f"tel.{phone.replace('+', '').replace(' ', '')}@reservaao.local"
    novo = Usuario(
        nome=name,
        email=email,
        telefone=phone,
        senha=hash_senha("123456"),
        role=RoleUsuario.client,
        company_id=company_id,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return to_frontend_user(novo, db)