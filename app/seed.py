from sqlalchemy.orm import Session
from app.core.security import hash_senha
from app.models.models import (
    Company,
    Employee,
    EmployeeRole,
    MenuCategory,
    MenuItem,
    RoleUsuario,
    TableLocation,
    TableStatus,
    Usuario,
    VenueArea,
    VenueTable,
)


def seed_initial_data(db: Session) -> None:
    seed_companies(db)
    seed_users(db)
    seed_venue(db)
    seed_menu(db)
    seed_employees(db)
    db.commit()


def seed_companies(db: Session) -> None:
    companies = [
        ("Palace Lounge", "palace", "palace-frontend.vercel.app"),
        ("NOA Beach", "noa", "noa-frontend-xamv.vercel.app"),
    ]
    for name, slug, domain in companies:
        exists = db.query(Company).filter(Company.slug == slug).first()
        if not exists:
            db.add(Company(name=name, slug=slug, domain=domain))
    db.commit()


def seed_users(db: Session) -> None:
    palace = db.query(Company).filter(Company.slug == "palace").first()
    noa = db.query(Company).filter(Company.slug == "noa").first()

    users = [
        ("Administrador", "admin@reservaao.local", "+244900000001", RoleUsuario.admin, palace),
        ("Cliente Demo", "cliente@reservaao.local", "+244900000002", RoleUsuario.client, palace),
        ("Leitor QR", "staff@reservaao.local", "+244900000003", RoleUsuario.staff, palace),
        ("Chefe de Sala", "chefe.sala@reservaao.local", "+244900000004", RoleUsuario.chefe_sala, palace),
        ("Chefe de Cozinha", "chefe.cozinha@reservaao.local", "+244900000005", RoleUsuario.chefe_cozinha, palace),
        ("Bartender", "bar@reservaao.local", "+244900000006", RoleUsuario.bar, palace),
        ("Administrador NOA", "admin@noa.local", "+244900000007", RoleUsuario.admin, noa),
        ("Cliente NOA", "cliente@noa.local", "+244900000008", RoleUsuario.client, noa),
        ("Rececionista", "rececionista@reservaao.local", "+244900000007", RoleUsuario.rececionista, palace),
    ]
    for name, email, phone, role, company in users:
        exists = db.query(Usuario).filter(Usuario.email == email).first()
        if exists:
            continue
        db.add(Usuario(
            nome=name,
            email=email,
            telefone=phone,
            senha=hash_senha("123456"),
            role=role,
            company_id=company.id if company else None,
        ))
    db.commit()


def seed_venue(db: Session) -> None:
    if db.query(VenueArea).count() == 0:
        areas = [
            VenueArea(name="VIP Gold", x=8, y=12, width=28, height=30, color="#B89A67", ticket_price=35000, description="Zona premium junto ao palco"),
            VenueArea(name="Lounge", x=42, y=16, width=34, height=26, color="#2F6F73", ticket_price=22000, description="Mesas confortaveis no salao principal"),
            VenueArea(name="Bar", x=18, y=58, width=46, height=22, color="#7B3F61", ticket_price=15000, description="Zona dinamica perto do bar"),
        ]
        db.add_all(areas)
        db.flush()

    if db.query(VenueTable).count() == 0:
        areas = db.query(VenueArea).order_by(VenueArea.id.asc()).all()
        specs = [
            (1, 4, areas[0], 18, 24, TableLocation.vip),
            (2, 6, areas[0], 28, 30, TableLocation.vip),
            (3, 4, areas[1], 48, 24, TableLocation.indoor),
            (4, 4, areas[1], 62, 30, TableLocation.indoor),
            (5, 8, areas[1], 72, 34, TableLocation.indoor),
            (6, 4, areas[2], 26, 66, TableLocation.indoor),
            (7, 6, areas[2], 42, 68, TableLocation.indoor),
            (8, 4, areas[2], 58, 66, TableLocation.indoor),
        ]
        for number, capacity, area, x, y, location in specs:
            db.add(
                VenueTable(
                    number=number,
                    capacity=capacity,
                    location=location,
                    status=TableStatus.available,
                    area_id=area.id,
                    x=x,
                    y=y,
                    price_tier="vip" if location == TableLocation.vip else "standard",
                    description=f"Mesa {number} - {area.name}",
                )
            )


def seed_menu(db: Session) -> None:
    if db.query(MenuItem).count() > 0:
        return
    items = [
        ("Bruschetta Palace", "Entrada crocante com tomate fresco e ervas", MenuCategory.starters, 6500, True),
        ("Picanha Premium", "Picanha grelhada com acompanhamentos da casa", MenuCategory.mains, 18500, True),
        ("Risotto de Camarao", "Arroz cremoso com camarao e perfume citrico", MenuCategory.mains, 16500, False),
        ("Cheesecake Tropical", "Sobremesa fria com calda de maracuja", MenuCategory.desserts, 5500, False),
        ("Signature Palace", "Cocktail da casa com notas tropicais", MenuCategory.cocktails, 7000, True),
        ("Vinho Tinto Reserva", "Garrafa selecionada para jantar e lounge", MenuCategory.wines, 24000, False),
    ]
    for name, description, category, price, featured in items:
        db.add(
            MenuItem(
                name=name,
                description=description,
                category=category,
                price=price,
                available=True,
                featured=featured,
                allergens_json="[]",
            )
        )


def seed_employees(db: Session) -> None:
    if db.query(Employee).count() > 0:
        return
    table = db.query(VenueTable).order_by(VenueTable.number.asc()).first()
    db.add(Employee(name="Atendente Demo", phone="+244900000004", role=EmployeeRole.attendant, table_id=table.id if table else None))
