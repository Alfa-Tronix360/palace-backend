from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_equipa, get_chefe_sala
from app.models.models import Employee, EmployeeOrder, MenuItem, MenuCategory
from app.schemas.palace_schemas import EmployeeResponse
import json

router = APIRouter(prefix="/operacional", tags=["Operacional"])


@router.get("/fluxo/cozinha")
def fluxo_cozinha(db: Session = Depends(get_db), _user=Depends(get_equipa)):
    """Pedidos com itens de cozinha (entradas, pratos principais, sobremesas)"""
    categorias_cozinha = {
        MenuCategory.starters.value,
        MenuCategory.mains.value,
        MenuCategory.desserts.value,
    }
    orders = db.query(EmployeeOrder).order_by(EmployeeOrder.created_at.desc()).limit(50).all()
    resultado = []
    for order in orders:
        try:
            items = json.loads(order.items_json)
        except Exception:
            items = []
        items_cozinha = [i for i in items if i.get("category") in categorias_cozinha or True]
        if items_cozinha:
            resultado.append({
                "id": order.id,
                "code": order.code,
                "table_id": order.table_id,
                "employee_id": order.employee_id,
                "items": items_cozinha,
                "total": order.total,
                "created_at": order.created_at.isoformat(),
            })
    return resultado


@router.get("/fluxo/bar")
def fluxo_bar(db: Session = Depends(get_db), _user=Depends(get_equipa)):
    """Pedidos com itens de bar (bebidas, cocktails, vinhos)"""
    categorias_bar = {
        MenuCategory.drinks.value,
        MenuCategory.cocktails.value,
        MenuCategory.wines.value,
    }
    orders = db.query(EmployeeOrder).order_by(EmployeeOrder.created_at.desc()).limit(50).all()
    resultado = []
    for order in orders:
        try:
            items = json.loads(order.items_json)
        except Exception:
            items = []
        items_bar = [i for i in items if i.get("category") in categorias_bar or True]
        if items_bar:
            resultado.append({
                "id": order.id,
                "code": order.code,
                "table_id": order.table_id,
                "employee_id": order.employee_id,
                "items": items_bar,
                "total": order.total,
                "created_at": order.created_at.isoformat(),
            })
    return resultado


@router.get("/equipa")
def listar_equipa(db: Session = Depends(get_db), _user=Depends(get_equipa)):
    """Lista todos os funcionários activos"""
    employees = db.query(Employee).filter(Employee.active == True).order_by(Employee.name).all()
    return [
        {
            "id": e.id,
            "name": e.name,
            "phone": e.phone,
            "role": e.role.value,
            "table_id": e.table_id,
            "active": e.active,
            "created_at": e.created_at.isoformat(),
        }
        for e in employees
    ]


@router.patch("/equipa/{employee_id}/mesa")
def atribuir_mesa(
    employee_id: int,
    table_id: int | None = None,
    db: Session = Depends(get_db),
    _user=Depends(get_chefe_sala),
):
    """Atribui ou remove mesa de um funcionário (chefe de sala e admin)"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    employee.table_id = table_id
    db.commit()
    db.refresh(employee)
    return {"id": employee.id, "name": employee.name, "table_id": employee.table_id}