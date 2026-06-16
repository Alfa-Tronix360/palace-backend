from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_admin
from app.models.models import (
    DigitalTicket,
    Employee,
    EmployeeOrder,
    EventSeat,
    Pagamento,
    Reserva,
    TicketScan,
    TicketStatus,
    Usuario,
    VenueArea,
    VenueTable,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


def parse_date(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value)


def apply_date_range(query, column, from_: str | None, to: str | None):
    start = parse_date(from_)
    end = parse_date(to)
    if start:
        query = query.filter(column >= start)
    if end:
        query = query.filter(column <= end)
    return query


@router.get("/revenue")
def revenue(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    payments = db.query(func.coalesce(func.sum(Pagamento.valor), 0.0))
    payments = apply_date_range(payments, Pagamento.criado_em, from_, to)
    ticket_sales = db.query(func.coalesce(func.sum(DigitalTicket.price), 0.0))
    ticket_sales = apply_date_range(ticket_sales, DigitalTicket.purchased_at, from_, to)
    reservations_revenue = float(payments.scalar() or 0)
    tickets_revenue = float(ticket_sales.scalar() or 0)
    return {"reservations": reservations_revenue, "tickets": tickets_revenue, "total": reservations_revenue + tickets_revenue}


@router.get("/top-clients")
def top_clients(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    query = (
        db.query(Usuario.id, Usuario.nome, func.count(Reserva.id).label("reservations"))
        .join(Reserva, Reserva.usuario_id == Usuario.id)
        .group_by(Usuario.id, Usuario.nome)
        .order_by(func.count(Reserva.id).desc())
    )
    query = apply_date_range(query, Reserva.criado_em, from_, to)
    return [{"client_id": row.id, "client_name": row.nome, "reservations": row.reservations} for row in query.limit(20).all()]


@router.get("/employees/sales")
def employee_sales(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    query = (
        db.query(
            Employee.id,
            Employee.name,
            func.count(EmployeeOrder.id).label("orders"),
            func.coalesce(func.sum(EmployeeOrder.total), 0.0).label("revenue"),
        )
        .join(EmployeeOrder, EmployeeOrder.employee_id == Employee.id)
        .group_by(Employee.id, Employee.name)
        .order_by(func.sum(EmployeeOrder.total).desc())
    )
    query = apply_date_range(query, EmployeeOrder.created_at, from_, to)
    return [
        {
            "employee_id": row.id,
            "employee_name": row.name,
            "orders": row.orders,
            "revenue": float(row.revenue or 0),
        }
        for row in query.limit(20).all()
    ]


@router.get("/tables/reservations")
def table_reservations(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    # Legacy reservations still point to servico_id; expose that id as a table-like bucket
    # until reservations are migrated to venue_table_id.
    query = (
        db.query(Reserva.servico_id, func.count(Reserva.id).label("count"))
        .group_by(Reserva.servico_id)
        .order_by(func.count(Reserva.id).desc())
    )
    query = apply_date_range(query, Reserva.criado_em, from_, to)
    return [{"table_id": row.servico_id, "reservations": row.count} for row in query.all()]


@router.get("/tables/ticket-sales")
def table_ticket_sales(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    query = (
        db.query(EventSeat.table_number, func.count(DigitalTicket.id).label("sold"), func.coalesce(func.sum(DigitalTicket.price), 0.0).label("revenue"))
        .join(DigitalTicket, DigitalTicket.seat_id == EventSeat.id)
        .group_by(EventSeat.table_number)
        .order_by(func.count(DigitalTicket.id).desc())
    )
    query = apply_date_range(query, DigitalTicket.purchased_at, from_, to)
    return [{"table_number": row.table_number, "sold": row.sold, "revenue": float(row.revenue or 0)} for row in query.all()]


@router.get("/tables/order-revenue")
def table_order_revenue(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    query = (
        db.query(
            VenueTable.id,
            VenueTable.number,
            func.count(EmployeeOrder.id).label("orders"),
            func.coalesce(func.sum(EmployeeOrder.total), 0.0).label("revenue"),
        )
        .join(EmployeeOrder, EmployeeOrder.table_id == VenueTable.id)
        .group_by(VenueTable.id, VenueTable.number)
        .order_by(func.sum(EmployeeOrder.total).desc())
    )
    query = apply_date_range(query, EmployeeOrder.created_at, from_, to)
    return [
        {
            "table_id": row.id,
            "table_number": row.number,
            "orders": row.orders,
            "revenue": float(row.revenue or 0),
        }
        for row in query.all()
    ]


@router.get("/areas/occupancy")
def area_occupancy(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    query = (
        db.query(VenueArea.id, VenueArea.name, func.count(VenueTable.id).label("tables"))
        .outerjoin(VenueTable, VenueTable.area_id == VenueArea.id)
        .group_by(VenueArea.id, VenueArea.name)
        .order_by(VenueArea.name.asc())
    )
    return [{"area_id": row.id, "area_name": row.name, "tables": row.tables} for row in query.all()]


@router.get("/events/sales")
def event_sales(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    query = (
        db.query(DigitalTicket.event_id, func.count(DigitalTicket.id).label("sold"), func.coalesce(func.sum(DigitalTicket.price), 0.0).label("revenue"))
        .group_by(DigitalTicket.event_id)
        .order_by(func.sum(DigitalTicket.price).desc())
    )
    query = apply_date_range(query, DigitalTicket.purchased_at, from_, to)
    return [{"event_id": row.event_id, "sold": row.sold, "revenue": float(row.revenue or 0)} for row in query.all()]


@router.get("/tickets/validation")
def ticket_validation(eventId: int | None = None, db: Session = Depends(get_db), _admin=Depends(get_admin)):
    query = db.query(TicketScan.result, func.count(TicketScan.id).label("count")).group_by(TicketScan.result)
    if eventId:
        query = query.filter(TicketScan.event_id == eventId)
    rows = query.all()
    used = db.query(func.count(DigitalTicket.id)).filter(DigitalTicket.status == TicketStatus.used)
    if eventId:
        used = used.filter(DigitalTicket.event_id == eventId)
    return {
        "used_tickets": used.scalar() or 0,
        "scan_results": [{"result": row.result, "count": row.count} for row in rows],
    }
