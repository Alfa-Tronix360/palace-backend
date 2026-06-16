from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import UsuarioCreate, UsuarioResponse
from app.services.usuario_service import (
    service_listar_usuarios,
    service_buscar_usuario,
    service_criar_usuario,
    service_atualizar_usuario,
    service_deletar_usuario
)

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.get("/", response_model=list[UsuarioResponse])
def listar(db: Session = Depends(get_db)):
    return service_listar_usuarios(db)

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def buscar(usuario_id: int, db: Session = Depends(get_db)):
    try:
        return service_buscar_usuario(db, usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/", response_model=UsuarioResponse, status_code=201)
def criar(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        return service_criar_usuario(db, usuario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def atualizar(usuario_id: int, usuario: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        return service_atualizar_usuario(db, usuario_id, usuario)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{usuario_id}")
def deletar(usuario_id: int, db: Session = Depends(get_db)):
    try:
        service_deletar_usuario(db, usuario_id)
        return {"mensagem": "Utilizador eliminado com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))