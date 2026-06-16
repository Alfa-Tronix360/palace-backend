from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional
from app.models.models import StatusReserva, StatusPagamento, RoleUsuario, TipoParceiro, TipoPreco, EstadoParceiro, PlanoSubscricao, EstadoSubscricao



# ====================================
# USUARIO
# ====================================

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    telefone: str
    senha: str
    role: Optional[RoleUsuario] = RoleUsuario.cliente

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    telefone: Optional[str]
    role: RoleUsuario
    criado_em: datetime

    class Config:
        from_attributes = True

# ====================================
# PARCEIRO
# ====================================

class ParceiroCreate(BaseModel):
    nome: str
    tipo: TipoParceiro
    descricao: Optional[str] = None
    localizacao: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    nif: Optional[str] = None


class ParceiroResponse(BaseModel):
    id: int
    nome: str
    tipo: TipoParceiro
    descricao: Optional[str]
    localizacao: Optional[str]
    telefone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    nif: Optional[str]
    estado: EstadoParceiro
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class ParceiroRegistoCreate(BaseModel):
    nome_responsavel: str
    email: str
    senha: str
    nome_negocio: str
    tipo: TipoParceiro
    telefone: str
    localizacao: Optional[str] = None
    nif: Optional[str] = None
    aceitou_termos: bool = False

class ParceiroAprovar(BaseModel):
    estado: EstadoParceiro
# ====================================
# SERVICO
# ====================================

class ServicoCreate(BaseModel):
    parceiro_id: int
    nome: str
    descricao: Optional[str] = None
    preco: float
    duracao_minutos: Optional[int] = None
    capacidade: Optional[int] = None
    tipo_preco: Optional[TipoPreco] = TipoPreco.preco_fixo

class ServicoResponse(BaseModel):
    id: int
    parceiro_id: int
    nome: str
    descricao: Optional[str]
    preco: float
    duracao_minutos: Optional[int]
    capacidade: Optional[int]
    tipo_preco: TipoPreco
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True

# ====================================
# RESERVA
# ====================================

class ReservaCreate(BaseModel):
    parceiro_id: int
    servico_id: int
    data_inicio: datetime
    data_fim: datetime
    descricao: Optional[str] = None

class ReservaResponse(BaseModel):
    id: int
    usuario_id: int
    parceiro_id: int
    servico_id: int
    data_inicio: datetime
    data_fim: datetime
    status: StatusReserva
    total_preco: Optional[float]
    descricao: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True

# ====================================
# PAGAMENTO
# ====================================

class PagamentoCreate(BaseModel):
    reserva_id: int
    valor: float
    metodo: Optional[str] = None

class PagamentoUpdateStatus(BaseModel):
    status: StatusPagamento

# ====================================
# AUTENTICAÇÃO
# ====================================

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class FrontendUserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    role: str
    vip: bool = False
    totalSpent: float = 0
    reservationCount: int = 0
    avatarUrl: Optional[str] = None
    createdAt: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[FrontendUserResponse] = None


# ====================================
# PESQUISA
# ====================================

class PesquisaParams(BaseModel):
    tipo: Optional[TipoParceiro] = None
    localizacao: Optional[str] = None
    preco_min: Optional[float] = None
    preco_max: Optional[float] = None
    capacidade: Optional[int] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None    


# ====================================
# RESERVA UPDATE STATUS
# ====================================

class ReservaUpdateStatus(BaseModel):
    status: StatusReserva    


# ====================================
# SOLICITACAO DE PLANO
# ====================================

class SolicitacaoPlanoCreate(BaseModel):
    plano: PlanoSubscricao

class SolicitacaoPlanoResponse(BaseModel):
    plano: PlanoSubscricao
    valor_mensal: float
    descricao: str
    
# ====================================
# SUBSCRICAO
# ====================================

class SubscricaoCreate(BaseModel):
    parceiro_id: int
    plano: PlanoSubscricao
    valor_mensal: float
    data_inicio: datetime
    data_fim: datetime
    observacoes: Optional[str] = None

class SubscricaoResponse(BaseModel):
    id: int
    parceiro_id: int
    plano: PlanoSubscricao
    valor_mensal: float
    data_inicio: datetime
    data_fim: datetime
    estado: EstadoSubscricao
    observacoes: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True

class SubscricaoUpdateEstado(BaseModel):
    estado: EstadoSubscricao    


# ====================================
# HORARIO FUNCIONAMENTO
# ====================================

from app.models.models import DiaSemana, MotivoBloqueio

class HorarioFuncionamentoCreate(BaseModel):
    dia_semana: DiaSemana
    hora_abertura: str
    hora_fecho: str
    ativo: Optional[bool] = True

class HorarioFuncionamentoResponse(BaseModel):
    id: int
    parceiro_id: int
    dia_semana: DiaSemana
    hora_abertura: str
    hora_fecho: str
    ativo: bool

    class Config:
        from_attributes = True

# ====================================
# BLOQUEIO DISPONIBILIDADE
# ====================================

class BloqueioCreate(BaseModel):
    servico_id: Optional[int] = None
    data_inicio: datetime
    data_fim: datetime
    motivo: Optional[MotivoBloqueio] = MotivoBloqueio.outro
    descricao: Optional[str] = None

class BloqueioResponse(BaseModel):
    id: int
    parceiro_id: int
    servico_id: Optional[int]
    data_inicio: datetime
    data_fim: datetime
    motivo: MotivoBloqueio
    descricao: Optional[str]

    class Config:
        from_attributes = True

# ====================================
# CALENDARIO
# ====================================

class SlotCalendario(BaseModel):
    data: str
    estado: str
    motivo: Optional[str] = None
    reserva_id: Optional[int] = None    
