from sqlalchemy.orm import Session
from app.models.models import Usuario
from app.schemas.schemas import UsuarioCreate

def listar_usuarios(db: Session):
    return db.query(Usuario).all()

def buscar_usuario(db: Session, usuario_id: int):
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()

def buscar_usuario_por_email(db: Session, email: str):
    return db.query(Usuario).filter(Usuario.email == email).first()

def criar_usuario(db: Session, usuario: UsuarioCreate):
    novo_usuario = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        telefone=usuario.telefone,
        senha=usuario.senha
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

def criar_usuario_com_hash(db: Session, usuario: UsuarioCreate, senha_hash: str):
    novo_usuario = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        telefone=usuario.telefone,
        senha=senha_hash,
        role=usuario.role  # ← adicionar esta linha
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

def atualizar_usuario(db: Session, usuario_id: int, dados: UsuarioCreate):
    usuario = buscar_usuario(db, usuario_id)
    if not usuario:
        return None
    usuario.nome = dados.nome
    usuario.email = dados.email
    usuario.telefone = dados.telefone
    if dados.senha:
        usuario.senha = dados.senha
    if dados.role:
        usuario.role = dados.role
    db.commit()
    db.refresh(usuario)
    return usuario

def deletar_usuario(db: Session, usuario_id: int):
    usuario = buscar_usuario(db, usuario_id)
    if not usuario:
        return None
    db.delete(usuario)
    db.commit()
    return usuario
