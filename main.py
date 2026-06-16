from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.routers.usuario_router import router as usuario_router
from app.routers.reserva_router import router as reserva_router
from app.routers.pagamento_router import router as pagamento_router
from app.routers.auth_router import router as auth_router
from app.routers.parceiro_router import router as parceiro_router
from app.routers.servico_router import router as servico_router
from app.routers.subscricao_router import router as subscricao_router
from app.routers.disponibilidade_router import router as disponibilidade_router
from app.routers.reservations_api_router import router as reservations_api_router
from app.routers.venue_router import router as venue_router
from app.routers.published_events_router import router as published_events_router
from app.routers.tickets_router import router as tickets_router
from app.routers.reports_router import router as reports_router
from app.routers.employees_router import router as employees_router
from app.routers.menu_router import router as menu_router
from app.routers.clients_router import router as clients_router
from app.routers.payments_api_router import router as payments_api_router
from app.routers.events_router import router as events_router
from app.database import SessionLocal
from app.seed import seed_initial_data
from app.tasks.lembretes import iniciar_scheduler

Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "Frontend" / "ReservaAO" / "ReservaAO" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"

app = FastAPI(
    title="Sistema de Reservas.ao",
    description="API para gestão de reservas",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://palace-lounge.vercel.app",
    ],
    allow_origin_regex=r"https://palace-lounge(-[a-z0-9]+)?\.vercel\.app|http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(usuario_router)
app.include_router(parceiro_router)
app.include_router(servico_router)
app.include_router(reserva_router)
app.include_router(pagamento_router)
app.include_router(subscricao_router)
app.include_router(disponibilidade_router)
app.include_router(reservations_api_router)
app.include_router(venue_router)
app.include_router(published_events_router)
app.include_router(tickets_router)
app.include_router(reports_router)
app.include_router(employees_router)
app.include_router(menu_router)
app.include_router(clients_router)
app.include_router(payments_api_router)
app.include_router(events_router)

if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")

@app.on_event("startup")
async def startup():
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
    iniciar_scheduler()

@app.get("/")
def root():
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return {"mensagem": "Sistema de Reservas.ao API funcionando!"}


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=404, detail="Frontend build nao encontrado")

    requested_file = FRONTEND_DIST / full_path
    if requested_file.is_file():
        return FileResponse(requested_file)
    return FileResponse(FRONTEND_INDEX)
