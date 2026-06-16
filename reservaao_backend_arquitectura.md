# ReservaAO — Arquitectura Backend (FastAPI + Python)

## Stack tecnológico

| Componente | Tecnologia | Justificação |
|---|---|---|
| Framework | FastAPI 0.111+ | Async nativo, OpenAPI automático, validação Pydantic |
| Base de dados | PostgreSQL 16 | Multi-tenant, JSONB, full-text search |
| ORM | SQLAlchemy 2.0 + Alembic | Async sessions, migrações |
| Cache / Filas | Redis 7 | Sessions, rate limiting, Celery broker |
| Workers | Celery + Celery Beat | Lembretes, relatórios agendados |
| Auth | JWT (python-jose) + OAuth2 | Multi-tenant com roles |
| Pagamentos | Multicaixa Express SDK | Nativo angolano |
| Notificações | Meta WhatsApp Business API + Africa's Talking (SMS) | WhatsApp preferido em Angola |
| Facturação | AGT e-Factura API | Obrigatório legalmente |
| Monitorização | Sentry + Prometheus + Grafana | Erros e métricas |
| Deploy | Docker + Docker Compose | Portabilidade |

---

## Estrutura de ficheiros

```
reservaao-backend/
├── app/
│   ├── main.py                  # Entrada FastAPI, middleware, lifespan
│   ├── config.py                # Settings via pydantic-settings (.env)
│   ├── database.py              # Engine async SQLAlchemy, sessões
│   ├── dependencies.py          # get_db, get_current_user, get_tenant
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── tenant.py            # Negócio / estabelecimento
│   │   ├── user.py              # Utilizadores + roles
│   │   ├── customer.py          # Clientes finais (CRM)
│   │   ├── reservation.py       # Reservas
│   │   ├── resource.py          # Mesas / quartos / camarotes
│   │   ├── payment.py           # Pagamentos e transacções
│   │   ├── notification.py      # Log de notificações enviadas
│   │   └── audit.py             # Auditoria de acções
│   │
│   ├── schemas/                 # Pydantic v2 schemas (request/response)
│   │   ├── reservation.py
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── customer.py
│   │   ├── payment.py
│   │   └── analytics.py
│   │
│   ├── routers/                 # FastAPI APIRouter por módulo
│   │   ├── auth.py              # /auth/login, /auth/refresh, /auth/logout
│   │   ├── reservations.py      # /reservations CRUD + disponibilidade
│   │   ├── tenants.py           # /tenants gestão de negócios
│   │   ├── customers.py         # /customers CRM
│   │   ├── payments.py          # /payments + webhooks Multicaixa
│   │   ├── notifications.py     # /notifications configuração + log
│   │   ├── analytics.py         # /analytics dashboards + BI
│   │   ├── resources.py         # /resources mesas, quartos, slots
│   │   └── webhooks.py          # /webhooks WhatsApp, Multicaixa
│   │
│   ├── services/                # Lógica de negócio (sem acesso directo à BD)
│   │   ├── reservation_service.py
│   │   ├── availability_service.py
│   │   ├── payment_service.py
│   │   ├── notification_service.py
│   │   ├── whatsapp_service.py
│   │   ├── sms_service.py
│   │   ├── agt_service.py       # Facturação AGT
│   │   └── analytics_service.py
│   │
│   ├── tasks/                   # Celery tasks
│   │   ├── celery_app.py
│   │   ├── reminder_tasks.py    # Lembretes 24h e 1h antes
│   │   ├── report_tasks.py      # Relatórios diários/mensais
│   │   ├── cleanup_tasks.py     # Limpeza de reservas expiradas
│   │   └── sync_tasks.py        # Sync offline → online
│   │
│   ├── integrations/            # Clientes externos
│   │   ├── multicaixa.py        # Multicaixa Express
│   │   ├── whatsapp.py          # Meta Business API
│   │   ├── africas_talking.py   # SMS (Unitel / CLARO)
│   │   └── agt.py               # AGT e-Factura
│   │
│   └── core/
│       ├── security.py          # JWT, hashing passwords
│       ├── exceptions.py        # HTTP exceptions customizadas
│       ├── middleware.py        # Tenant isolation, logging
│       └── pagination.py        # Cursor-based pagination
│
├── migrations/                  # Alembic
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── conftest.py
│   ├── test_reservations.py
│   ├── test_payments.py
│   └── test_availability.py
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
│
├── .env.example
├── requirements.txt
└── alembic.ini
```

---

## Modelos principais (PostgreSQL)

### Tenant (Negócio)
```python
class Tenant(Base):
    __tablename__ = "tenants"
    id: UUID (PK)
    slug: str (unique)           # ex: "restaurante-solar-luanda"
    name: str
    niche: str                   # restaurant | hotel | nightclub | spa | club | event | agency
    plan: str                    # starter | professional | enterprise
    phone: str                   # +244...
    address: str
    city: str
    country: str = "AO"
    timezone: str = "Africa/Luanda"
    settings: JSONB              # configs específicas do nicho
    is_active: bool
    created_at: timestamp
```

### Resource (Mesa / Quarto / Camarote)
```python
class Resource(Base):
    __tablename__ = "resources"
    id: UUID (PK)
    tenant_id: UUID (FK)
    name: str                    # "Mesa 4", "Suite Presidencial"
    type: str                    # table | room | vip_table | cabin | lane | hall
    capacity: int
    min_capacity: int
    is_active: bool
    metadata: JSONB              # posição no mapa, características
```

### Reservation
```python
class Reservation(Base):
    __tablename__ = "reservations"
    id: UUID (PK)
    tenant_id: UUID (FK)
    resource_id: UUID (FK, nullable)
    customer_id: UUID (FK)
    status: str                  # pending | confirmed | arrived | completed | cancelled | no_show
    start_time: timestamp
    end_time: timestamp
    party_size: int
    source: str                  # online | whatsapp | phone | walk_in
    notes: text
    deposit_amount: Decimal
    deposit_paid: bool
    reminder_sent_24h: bool
    reminder_sent_1h: bool
    cancelled_at: timestamp
    cancellation_reason: str
    metadata: JSONB
    created_at: timestamp
```

### Customer (CRM)
```python
class Customer(Base):
    __tablename__ = "customers"
    id: UUID (PK)
    tenant_id: UUID (FK)
    name: str
    phone: str                   # +244...
    email: str (nullable)
    birthday: date (nullable)
    total_reservations: int
    total_spent: Decimal
    no_show_count: int
    preferences: JSONB           # mesas preferidas, alergias, etc.
    loyalty_points: int
    whatsapp_opted_in: bool
    created_at: timestamp
```

### Payment
```python
class Payment(Base):
    __tablename__ = "payments"
    id: UUID (PK)
    reservation_id: UUID (FK)
    tenant_id: UUID (FK)
    amount: Decimal
    currency: str = "AOA"
    method: str                  # multicaixa_express | bank_transfer | cash
    status: str                  # pending | processing | completed | failed | refunded
    multicaixa_reference: str
    multicaixa_transaction_id: str
    agt_invoice_number: str
    paid_at: timestamp
    created_at: timestamp
```

---

## API endpoints principais

### Auth
```
POST   /auth/login               → {access_token, refresh_token}
POST   /auth/refresh             → {access_token}
POST   /auth/logout
GET    /auth/me                  → UserResponse
```

### Reservations
```
GET    /reservations             → ReservationListResponse (filtros: date, status, resource)
POST   /reservations             → ReservationResponse
GET    /reservations/{id}        → ReservationResponse
PATCH  /reservations/{id}        → ReservationResponse
DELETE /reservations/{id}        → 204

POST   /reservations/{id}/confirm
POST   /reservations/{id}/cancel
POST   /reservations/{id}/check-in
POST   /reservations/{id}/no-show

GET    /availability             → slots disponíveis por data/recurso
```

### Customers
```
GET    /customers                → CustomerListResponse
POST   /customers                → CustomerResponse
GET    /customers/{id}           → CustomerResponse (com histórico)
PATCH  /customers/{id}
GET    /customers/{id}/reservations
GET    /customers/search?phone=+244...
```

### Payments
```
POST   /payments/initiate        → {multicaixa_reference, amount}
GET    /payments/{id}
POST   /webhooks/multicaixa      → callback Multicaixa Express
GET    /payments/report          → relatório por período
```

### Analytics
```
GET    /analytics/dashboard      → KPIs do dia (reservas, receita, ocupação)
GET    /analytics/occupancy      → taxa de ocupação por período
GET    /analytics/revenue        → receita por canal, nicho, período
GET    /analytics/no-shows       → análise de no-shows
GET    /analytics/customers      → clientes recorrentes, LTV
```

### WhatsApp Webhook
```
GET    /webhooks/whatsapp        → verificação Meta (challenge)
POST   /webhooks/whatsapp        → mensagens recebidas → interpretação de reservas
```

---

## Multi-tenancy

Isolamento por `tenant_id` em todas as tabelas. Middleware extrai tenant do JWT e injeta em todas as queries:

```python
# middleware.py
async def tenant_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    tenant_id = extract_tenant_from_jwt(token)
    request.state.tenant_id = tenant_id
    return await call_next(request)

# dependencies.py
async def get_tenant(request: Request, db: AsyncSession = Depends(get_db)) -> Tenant:
    return await db.get(Tenant, request.state.tenant_id)
```

---

## Celery tasks agendadas

```python
# Lembra clientes 24h antes
@app.task
def send_24h_reminders():
    # Busca reservas para amanhã, não canceladas, lembrete não enviado
    # Envia WhatsApp via Meta API
    # Marca reminder_sent_24h = True

# Lembra clientes 1h antes
@app.task
def send_1h_reminders():
    # Mesmo padrão, 1 hora

# Marca no-shows automaticamente (15 min após hora da reserva)
@app.task
def auto_mark_no_shows():
    # reservas confirmed, start_time + 15min passados, não chegaram

# Relatório diário para gestores (via WhatsApp ou email)
@app.task
def daily_report():
    # Resumo: reservas, receita, no-shows, ocupação

# Beat schedule
CELERY_BEAT_SCHEDULE = {
    "24h-reminders": {"task": "send_24h_reminders", "schedule": crontab(hour=9, minute=0)},
    "1h-reminders":  {"task": "send_1h_reminders",  "schedule": crontab(minute="*/15")},
    "no-shows":      {"task": "auto_mark_no_shows", "schedule": crontab(minute="*/15")},
    "daily-report":  {"task": "daily_report",       "schedule": crontab(hour=8, minute=0)},
}
```

---

## Integração Multicaixa Express

```python
# integrations/multicaixa.py
class MulticaixaExpressClient:
    BASE_URL = "https://api.multicaixaexpress.ao/v1"

    async def initiate_payment(self, amount: Decimal, reference: str, 
                                phone: str) -> dict:
        # Gera referência de pagamento
        # Cliente paga pelo app Multicaixa Express
        # Webhook confirma pagamento

    async def check_payment_status(self, transaction_id: str) -> str:
        # pending | completed | failed

    async def verify_webhook_signature(self, payload: bytes, 
                                        signature: str) -> bool:
        # HMAC-SHA256 com chave secreta
```

---

## Modo offline

```python
# Sync queue em Redis para operações feitas offline
# Quando ligação restabelecida, worker processa fila
class OfflineSyncService:
    async def queue_operation(self, operation: dict):
        await redis.lpush("offline_queue", json.dumps(operation))

    async def sync(self):
        while operation := await redis.rpop("offline_queue"):
            await self.replay_operation(json.loads(operation))
```

---

## Variáveis de ambiente (.env)

```env
# Base de dados
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/reservaao
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=<chave-256-bits>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Multicaixa Express
MULTICAIXA_API_KEY=
MULTICAIXA_MERCHANT_ID=
MULTICAIXA_WEBHOOK_SECRET=

# Meta WhatsApp Business
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=

# SMS (Africa's Talking)
AT_API_KEY=
AT_USERNAME=
AT_SENDER_ID=ReservaAO

# AGT e-Factura
AGT_NIF=
AGT_API_KEY=
AGT_ENVIRONMENT=production

# Sentry
SENTRY_DSN=
```

---

## Docker Compose

```yaml
version: "3.9"
services:
  api:
    build: .
    ports: ["8000:8000"]
    depends_on: [db, redis]
    env_file: .env
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

  worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info
    depends_on: [db, redis]
    env_file: .env

  beat:
    build: .
    command: celery -A app.tasks.celery_app beat --loglevel=info
    depends_on: [redis]
    env_file: .env

  db:
    image: postgres:16
    volumes: ["pgdata:/var/lib/postgresql/data"]
    environment:
      POSTGRES_DB: reservaao
      POSTGRES_USER: reservaao
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    volumes: ["redisdata:/data"]

volumes:
  pgdata:
  redisdata:
```

---

## Próximos passos recomendados

1. **Iniciar projecto** — `fastapi-utils` + `cookiecutter` ou estrutura manual acima
2. **Criar modelos e migrações Alembic** — começar por Tenant → Resource → Reservation → Customer
3. **Implementar auth JWT** com multi-tenant
4. **Criar router de reservas** com lógica de disponibilidade
5. **Integrar Multicaixa** (sandbox primeiro)
6. **Configurar WhatsApp Business API** (Meta Developer Account)
7. **Celery + lembretes automáticos**
8. **Deploy Docker** em VPS angolana ou Hetzner (baixa latência)
