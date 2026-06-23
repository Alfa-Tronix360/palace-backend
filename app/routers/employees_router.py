import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.core.dependencies import get_admin
from app.models.models import Employee, EmployeeOrder, EmployeeTable, VenueTable
from app.schemas.palace_schemas import (
    EmployeeAssignTable,
    EmployeeCreate,
    EmployeeOrderCreate,
    EmployeeOrderItem,
    EmployeeOrderResponse,
    EmployeeResponse,
    EmployeeUpdate,
)

router = APIRouter(tags=["Employees"])


def get_employee_or_404(db: Session, employee_id: int) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Funcionario nao encontrado")
    return employee


def get_table_or_404(db: Session, table_id: int) -> VenueTable:
    table = db.query(VenueTable).filter(VenueTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Mesa nao encontrada")
    return table


def to_employee_response(employee: Employee) -> dict:
    return {
        "id": employee.id,
        "name": employee.name,
        "phone": employee.phone,
        "role": employee.role,
        "table_id": employee.table_id,
        "active": employee.active,
        "created_at": employee.created_at,
        "assigned_tables": [
            {
                "id": at.id,
                "table_id": at.table_id,
                "table_number": at.table.number if at.table else 0,
            }
            for at in employee.assigned_tables
        ],
    }


def order_to_response(order: EmployeeOrder) -> EmployeeOrderResponse:
    items = [EmployeeOrderItem(**item) for item in json.loads(order.items_json)]
    return EmployeeOrderResponse(
        id=order.id,
        code=order.code,
        employee_id=order.employee_id,
        employee_name=order.employee.name if order.employee else f"Funcionario #{order.employee_id}",
        table_id=order.table_id,
        table_number=order.table.number if order.table else order.table_id,
        items=items,
        total=order.total,
        created_at=order.created_at,
    )


@router.get("/employees", response_model=list[EmployeeResponse])
def list_employees(db: Session = Depends(get_db), _admin=Depends(get_admin)):
    employees = db.query(Employee).options(
        joinedload(Employee.assigned_tables).joinedload(EmployeeTable.table)
    ).order_by(Employee.created_at.desc()).all()
    return [to_employee_response(e) for e in employees]


@router.post("/employees", response_model=EmployeeResponse, status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db), _admin=Depends(get_admin)):
    if payload.table_id is not None:
        get_table_or_404(db, payload.table_id)
    employee = Employee(**payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return to_employee_response(employee)


@router.patch("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    employee = get_employee_or_404(db, employee_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("table_id") is not None:
        get_table_or_404(db, data["table_id"])
    for field, value in data.items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return to_employee_response(employee)


@router.post("/employees/{employee_id}/assign-table", response_model=EmployeeResponse)
def assign_employee_table(
    employee_id: int,
    payload: EmployeeAssignTable,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    employee = get_employee_or_404(db, employee_id)
    if payload.table_id is not None:
        get_table_or_404(db, payload.table_id)
    employee.table_id = payload.table_id
    db.commit()
    db.refresh(employee)
    return to_employee_response(employee)


@router.get("/employee-orders", response_model=list[EmployeeOrderResponse])
def list_employee_orders(db: Session = Depends(get_db), _admin=Depends(get_admin)):
    orders = db.query(EmployeeOrder).order_by(EmployeeOrder.created_at.desc()).all()
    return [order_to_response(order) for order in orders]


@router.post("/employee-orders", response_model=EmployeeOrderResponse, status_code=201)
def create_employee_order(
    payload: EmployeeOrderCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    employee = get_employee_or_404(db, payload.employee_id)
    table = get_table_or_404(db, payload.table_id)
    if not payload.items:
        raise HTTPException(status_code=400, detail="Pedido vazio")
    total = sum(item.quantity * item.price for item in payload.items)
    if total <= 0:
        raise HTTPException(status_code=400, detail="Total do pedido invalido")
    next_number = db.query(EmployeeOrder).count() + 1
    order = EmployeeOrder(
        code=f"PD-{next_number:04d}",
        employee_id=employee.id,
        table_id=table.id,
        items_json=json.dumps([item.model_dump() for item in payload.items]),
        total=total,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order_to_response(order)


@router.post("/employees/{employee_id}/toggle-table/{table_id}", response_model=EmployeeResponse)
def toggle_employee_table(
    employee_id: int,
    table_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    employee = get_employee_or_404(db, employee_id)
    get_table_or_404(db, table_id)
    existing = db.query(EmployeeTable).filter(
        EmployeeTable.employee_id == employee_id,
        EmployeeTable.table_id == table_id,
    ).first()
    if existing:
        db.delete(existing)
    else:
        db.add(EmployeeTable(employee_id=employee_id, table_id=table_id))
    db.commit()
    employees = db.query(Employee).options(
        joinedload(Employee.assigned_tables).joinedload(EmployeeTable.table)
    ).filter(Employee.id == employee_id).first()
    return to_employee_response(employees)