from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    domain = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TipoPreco(enum.Enum):
    por_hora = "por_hora"
    por_noite = "por_noite"
    preco_fixo = "preco_fixo"

class RoleUsuario(enum.Enum):
    admin = "admin"
    cliente = "cliente"
    client = "client"
    staff = "staff"
    parceiro = "parceiro"
    chefe_sala = "chefe_sala"
    chefe_cozinha = "chefe_cozinha"
    bar = "bar"


class EstadoParceiro(enum.Enum):
    pendente = "pendente"
    aprovado = "aprovado"
    rejeitado = "rejeitado"

class StatusReserva(enum.Enum):
    pendente = "pendente"
    confirmada = "confirmada"
    in_service = "in_service"
    completed = "completed"
    cancelada = "cancelada"

class StatusPagamento(enum.Enum):
    pendente = "pendente"
    pago = "pago"
    cancelado = "cancelado"


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    reservation_id = Column(Integer, ForeignKey("palace_reservations.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    service = Column(Integer, nullable=False)
    atmosphere = Column(Integer, nullable=False)
    food = Column(Integer, nullable=False)
    drinks = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Usuario")
    reservation = relationship("PalaceReservation")
    
class TableStatus(enum.Enum):
    available = "available"
    reserved = "reserved"
    occupied = "occupied"
    maintenance = "maintenance"

class TableLocation(enum.Enum):
    indoor = "indoor"
    outdoor = "outdoor"
    vip = "vip"

class VenueAreaShape(enum.Enum):
    rectangle = "rectangle"
    circle = "circle"

class TicketSeatStatus(enum.Enum):
    available = "available"
    sold = "sold"
    blocked = "blocked"

class TicketStatus(enum.Enum):
    valid = "valid"
    used = "used"
    cancelled = "cancelled"

class EventType(enum.Enum):
    birthday = "birthday"
    wedding = "wedding"
    corporate = "corporate"
    private_dinner = "private_dinner"
    themed = "themed"

class EventStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"

class EmployeeRole(enum.Enum):
    attendant = "attendant"
    seller = "seller"
    operator = "operator"

class MenuCategory(enum.Enum):
    starters = "starters"
    mains = "mains"
    desserts = "desserts"
    drinks = "drinks"
    cocktails = "cocktails"
    wines = "wines"

class TipoParceiro(enum.Enum):
    hotel = "hotel"
    salao_festa = "salao_festa"
    barbearia = "barbearia"
    clinica = "clinica"
    restaurante = "restaurante"
    campo_futebol = "campo_futebol"
    sala_reuniao = "sala_reuniao"
    outro = "outro"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefone = Column(String, nullable=True)
    senha = Column(String, nullable=False)
    role = Column(Enum(RoleUsuario), default=RoleUsuario.cliente)
    criado_em = Column(DateTime, default=datetime.utcnow)

    reservas = relationship("Reserva", back_populates="usuario")

class VenueArea(Base):
    __tablename__ = "venue_areas"
    
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    shape = Column(Enum(VenueAreaShape), default=VenueAreaShape.rectangle, nullable=False)
    x = Column(Float, default=0.0, nullable=False)
    y = Column(Float, default=0.0, nullable=False)
    width = Column(Float, default=20.0, nullable=False)
    height = Column(Float, default=20.0, nullable=False)
    color = Column(String, default="#B89A67", nullable=False)
    ticket_price = Column(Float, default=0.0, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    tables = relationship("VenueTable", back_populates="area")

class VenueTable(Base):
    __tablename__ = "venue_tables"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    number = Column(Integer, unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    location = Column(Enum(TableLocation), default=TableLocation.indoor, nullable=False)
    status = Column(Enum(TableStatus), default=TableStatus.available, nullable=False)
    description = Column(Text, nullable=True)
    x = Column(Float, default=0.0)
    y = Column(Float, default=0.0)
    area_id = Column(Integer, ForeignKey("venue_areas.id"), nullable=True)
    price_tier = Column(String, default="standard")
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    area = relationship("VenueArea", back_populates="tables")

class PalaceReservation(Base):
    __tablename__ = "palace_reservations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    table_id = Column(Integer, ForeignKey("venue_tables.id"), nullable=False)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    guests = Column(Integer, default=2, nullable=False)
    status = Column(Enum(StatusReserva), default=StatusReserva.pendente, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Usuario")
    table = relationship("VenueTable")

class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(MenuCategory), nullable=False)
    price = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)
    available = Column(Boolean, default=True, nullable=False)
    featured = Column(Boolean, default=False, nullable=False)
    allergens_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SiteImage(Base):
    __tablename__ = "site_images"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    image_url = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)   

class TransferRequest(Base):
    __tablename__ = "transfer_requests"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    vehicle_type = Column(String, nullable=False)
    vehicle_model = Column(String, nullable=True)
    date = Column(DateTime, nullable=False)
    time = Column(String, nullable=False)
    pickup_location = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Usuario")     

class PublishedEvent(Base):
    __tablename__ = "published_events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    title = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    time = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    stage_label = Column(String, default="Palco")
    banner_url = Column(String, nullable=True)
    base_price = Column(Float, default=0.0, nullable=False)
    published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    seats = relationship("EventSeat", back_populates="event", cascade="all, delete-orphan")
    tickets = relationship("DigitalTicket", back_populates="event")

class EventSeat(Base):
    __tablename__ = "event_seats"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("published_events.id"), nullable=False)
    table_id = Column(Integer, ForeignKey("venue_tables.id"), nullable=True)
    table_number = Column(Integer, nullable=False)
    x = Column(Float, default=0.0)
    y = Column(Float, default=0.0)
    capacity = Column(Integer, nullable=False)
    location = Column(Enum(TableLocation), default=TableLocation.indoor, nullable=False)
    price = Column(Float, default=0.0, nullable=False)
    status = Column(Enum(TicketSeatStatus), default=TicketSeatStatus.available, nullable=False)

    event = relationship("PublishedEvent", back_populates="seats")
    table = relationship("VenueTable")
    tickets = relationship("DigitalTicket", back_populates="seat")

class DigitalTicket(Base):
    __tablename__ = "digital_tickets"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("published_events.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("event_seats.id"), nullable=False)
    price = Column(Float, nullable=False)
    qr_code = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.valid, nullable=False)
    used_at = Column(DateTime, nullable=True)
    purchased_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("PublishedEvent", back_populates="tickets")
    client = relationship("Usuario")
    seat = relationship("EventSeat", back_populates="tickets")
    scans = relationship("TicketScan", back_populates="ticket")

class PrivateEventRequest(Base):
    __tablename__ = "private_event_requests"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    code = Column(String, unique=True, nullable=False)
    type = Column(Enum(EventType), nullable=False)
    date = Column(DateTime, nullable=False)
    guests = Column(Integer, nullable=False)
    status = Column(Enum(EventStatus), default=EventStatus.pending, nullable=False)
    notes = Column(Text, nullable=True)
    budget = Column(Float, nullable=True)
    deposit_paid = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    client = relationship("Usuario")

class TicketScan(Base):
    __tablename__ = "ticket_scans"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("digital_tickets.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("published_events.id"), nullable=False)
    result = Column(String, nullable=False)
    scanned_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("DigitalTicket", back_populates="scans")
    staff = relationship("Usuario")

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    role = Column(Enum(EmployeeRole), default=EmployeeRole.attendant, nullable=False)
    table_id = Column(Integer, ForeignKey("venue_tables.id"), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    table = relationship("VenueTable")
    orders = relationship("EmployeeOrder", back_populates="employee")
    assigned_tables = relationship("EmployeeTable", back_populates="employee", cascade="all, delete-orphan")

class EmployeeTable(Base):
    __tablename__ = "employee_tables"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    table_id = Column(Integer, ForeignKey("venue_tables.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="assigned_tables")
    table = relationship("VenueTable")    

class EmployeeOrder(Base):
    __tablename__ = "employee_orders"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    table_id = Column(Integer, ForeignKey("venue_tables.id"), nullable=False)
    items_json = Column(Text, nullable=False)
    total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="orders")
    table = relationship("VenueTable")

class Parceiro(Base):
    __tablename__ = "parceiros"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    nome = Column(String, nullable=False)
    tipo = Column(Enum(TipoParceiro), nullable=False)
    descricao = Column(String, nullable=True)
    localizacao = Column(String, nullable=True)
    telefone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    nif = Column(String, nullable=True)
    estado = Column(Enum(EstadoParceiro), default=EstadoParceiro.pendente)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", backref="parceiro")
    servicos = relationship("Servico", back_populates="parceiro")
    reservas = relationship("Reserva", back_populates="parceiro")
    
class Servico(Base):
    __tablename__ = "servicos"

    id = Column(Integer, primary_key=True, index=True)
    parceiro_id = Column(Integer, ForeignKey("parceiros.id"), nullable=False)
    nome = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    tipo_preco = Column(Enum(TipoPreco), default=TipoPreco.preco_fixo)
    preco = Column(Float, nullable=False)
    duracao_minutos = Column(Integer, nullable=True)
    capacidade = Column(Integer, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    parceiro = relationship("Parceiro", back_populates="servicos")
    reservas = relationship("Reserva", back_populates="servico")

class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    parceiro_id = Column(Integer, ForeignKey("parceiros.id"), nullable=False)
    servico_id = Column(Integer, ForeignKey("servicos.id"), nullable=False)
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=False)
    status = Column(Enum(StatusReserva), default=StatusReserva.pendente)
    total_preco = Column(Float, nullable=True)
    descricao = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="reservas")
    parceiro = relationship("Parceiro", back_populates="reservas")
    servico = relationship("Servico", back_populates="reservas")
    pagamento = relationship("Pagamento", back_populates="reserva", uselist=False)

class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    valor = Column(Float, nullable=False)
    metodo = Column(String, nullable=True)
    status = Column(Enum(StatusPagamento), default=StatusPagamento.pendente)
    criado_em = Column(DateTime, default=datetime.utcnow)

    reserva = relationship("Reserva", back_populates="pagamento")

class PlanoSubscricao(enum.Enum):
    trial = "trial"        # 30 dias gratuito
    basic = "basic"
    pro = "pro"
    enterprise = "enterprise"

class EstadoSubscricao(enum.Enum):
    ativa = "ativa"
    expirada = "expirada"
    cancelada = "cancelada"

class Subscricao(Base):
    __tablename__ = "subscricoes"

    id = Column(Integer, primary_key=True, index=True)
    parceiro_id = Column(Integer, ForeignKey("parceiros.id"), nullable=False)
    plano = Column(Enum(PlanoSubscricao), nullable=False, default=PlanoSubscricao.trial)
    valor_mensal = Column(Float, nullable=False, default=0.0)
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=False)
    estado = Column(Enum(EstadoSubscricao), default=EstadoSubscricao.ativa)
    observacoes = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    parceiro = relationship("Parceiro", backref="subscricoes")    



class DiaSemana(enum.Enum):
    segunda = 0
    terca = 1
    quarta = 2
    quinta = 3
    sexta = 4
    sabado = 5
    domingo = 6

class MotivoBloqueio(enum.Enum):
    manutencao = "manutencao"
    feriado = "feriado"
    outro = "outro"

class HorarioFuncionamento(Base):
    __tablename__ = "horarios_funcionamento"

    id = Column(Integer, primary_key=True, index=True)
    parceiro_id = Column(Integer, ForeignKey("parceiros.id"), nullable=False)
    dia_semana = Column(Enum(DiaSemana), nullable=False)
    hora_abertura = Column(String, nullable=False)
    hora_fecho = Column(String, nullable=False)
    ativo = Column(Boolean, default=True)

    parceiro = relationship("Parceiro", backref="horarios")

class BloqueioDisponibilidade(Base):
    __tablename__ = "bloqueios_disponibilidade"

    id = Column(Integer, primary_key=True, index=True)
    parceiro_id = Column(Integer, ForeignKey("parceiros.id"), nullable=False)
    servico_id = Column(Integer, ForeignKey("servicos.id"), nullable=True)
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=False)
    motivo = Column(Enum(MotivoBloqueio), default=MotivoBloqueio.outro)
    descricao = Column(String, nullable=True)

    parceiro = relationship("Parceiro", backref="bloqueios")
    servico = relationship("Servico", backref="bloqueios")    
