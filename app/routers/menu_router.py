import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_admin
from app.models.models import MenuCategory, MenuItem
from app.schemas.palace_schemas import MenuItemCreate, MenuItemResponse, MenuItemUpdate

router = APIRouter(prefix="/menu", tags=["Menu"])


def to_response(item: MenuItem) -> MenuItemResponse:
    allergens = json.loads(item.allergens_json) if item.allergens_json else []
    return MenuItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        category=item.category,
        price=item.price,
        image_url=item.image_url,
        available=item.available,
        featured=item.featured,
        allergens=allergens,
        created_at=item.created_at,
    )


def get_item_or_404(db: Session, item_id: int) -> MenuItem:
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item do cardapio nao encontrado")
    return item


@router.get("", response_model=list[MenuItemResponse])
@router.get("/", response_model=list[MenuItemResponse])
def list_menu(
    category: MenuCategory | None = None,
    available: bool | None = None,
    featured: bool | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(MenuItem)
    if category:
        query = query.filter(MenuItem.category == category)
    if available is not None:
        query = query.filter(MenuItem.available == available)
    if featured is not None:
        query = query.filter(MenuItem.featured == featured)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(MenuItem.name.ilike(like) | MenuItem.description.ilike(like))
    return [to_response(item) for item in query.order_by(MenuItem.category.asc(), MenuItem.name.asc()).all()]


@router.get("/{item_id}", response_model=MenuItemResponse)
def get_menu_item(item_id: int, db: Session = Depends(get_db)):
    return to_response(get_item_or_404(db, item_id))


@router.post("", response_model=MenuItemResponse, status_code=201)
@router.post("/", response_model=MenuItemResponse, status_code=201)
def create_menu_item(payload: MenuItemCreate, db: Session = Depends(get_db), _admin=Depends(get_admin)):
    item = MenuItem(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        price=payload.price,
        image_url=payload.image_url,
        available=payload.available,
        featured=payload.featured,
        allergens_json=json.dumps(payload.allergens),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return to_response(item)


@router.patch("/{item_id}", response_model=MenuItemResponse)
def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    item = get_item_or_404(db, item_id)
    data = payload.model_dump(exclude_unset=True)
    allergens = data.pop("allergens", None)
    for field, value in data.items():
        setattr(item, field, value)
    if allergens is not None:
        item.allergens_json = json.dumps(allergens)
    db.commit()
    db.refresh(item)
    return to_response(item)


@router.delete("/{item_id}")
def delete_menu_item(item_id: int, db: Session = Depends(get_db), _admin=Depends(get_admin)):
    item = get_item_or_404(db, item_id)
    db.delete(item)
    db.commit()
    return {"message": "Item removido com sucesso"}

