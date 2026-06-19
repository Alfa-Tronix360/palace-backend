from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.models import (
    EmployeeRole,
    EventStatus,
    EventType,
    MenuCategory,
    TableLocation,
    TableStatus,
    TicketSeatStatus,
    TicketStatus,
    VenueAreaShape,
)


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class VenueAreaBase(CamelModel):
    name: str
    shape: VenueAreaShape = VenueAreaShape.rectangle
    x: float = 0
    y: float = 0
    width: float = 20
    height: float = 20
    color: str = "#B89A67"
    ticket_price: float = 0
    description: Optional[str] = None


class VenueAreaCreate(VenueAreaBase):
    pass


class VenueAreaUpdate(CamelModel):
    name: Optional[str] = None
    shape: Optional[VenueAreaShape] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    color: Optional[str] = None
    ticket_price: Optional[float] = None
    description: Optional[str] = None


class VenueAreaResponse(VenueAreaBase):
    id: int
    created_at: datetime


class VenueTableBase(CamelModel):
    number: int
    capacity: int
    location: TableLocation = TableLocation.indoor
    status: TableStatus = TableStatus.available
    description: Optional[str] = None
    x: Optional[float] = 0
    y: Optional[float] = 0
    area_id: Optional[int] = None
    price_tier: Optional[str] = "standard"
    image_url: Optional[str] = None


class VenueTableCreate(VenueTableBase):
    pass


class VenueTableUpdate(CamelModel):
    number: Optional[int] = None
    capacity: Optional[int] = None
    location: Optional[TableLocation] = None
    status: Optional[TableStatus] = None
    description: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    area_id: Optional[int] = None
    price_tier: Optional[str] = None
    image_url: Optional[str] = None


class VenueTableResponse(VenueTableBase):
    id: int
    created_at: datetime
    price: Optional[float] = None


class TicketSeatResponse(CamelModel):
    id: int
    event_id: int
    table_id: Optional[int]
    table_number: int
    x: Optional[float]
    y: Optional[float]
    capacity: int
    location: TableLocation
    price: float
    status: TicketSeatStatus

class PublishedEventBase(CamelModel):
    title: str
    date: datetime
    time: str
    description: str
    stage_label: str = "Palco"
    banner_url: Optional[str] = None
    base_price: float = 0


class PublishedEventCreate(PublishedEventBase):
    pass


class PublishedEventUpdate(CamelModel):
    title: Optional[str] = None
    date: Optional[datetime] = None
    time: Optional[str] = None
    description: Optional[str] = None
    stage_label: Optional[str] = None
    banner_url: Optional[str] = None
    base_price: Optional[float] = None
    published: Optional[bool] = None


class PublishedEventResponse(PublishedEventBase):
    id: int
    published: bool
    created_at: datetime
    seats: list[TicketSeatResponse] = []

class TicketPurchaseCreate(CamelModel):
    event_id: int
    seat_id: int


class TicketValidateCreate(CamelModel):
    qr_code: str


class DigitalTicketResponse(CamelModel):
    id: int
    event_id: int
    client_id: int
    client_name: str = ""
    client_phone: Optional[str] = None
    seat_id: int
    table_number: int = 0
    price: float
    qr_code: str
    whatsapp_url: Optional[str] = None
    delivery_status: str = "pending"
    status: TicketStatus
    used_at: Optional[datetime]
    purchased_at: datetime

class TicketValidationResponse(CamelModel):
    valid: bool
    message: str
    ticket: Optional[DigitalTicketResponse] = None


class TicketScanResponse(CamelModel):
    id: int
    ticket_id: int
    staff_id: Optional[int]
    event_id: int
    result: str
    scanned_at: datetime

class TicketWhatsAppSendCreate(CamelModel):
    phone: str


class TicketWhatsAppSendResponse(DigitalTicketResponse):
    whatsapp_url: str
    delivery_status: str = "sent"


class EmployeeBase(CamelModel):
    name: str
    phone: str
    role: EmployeeRole = EmployeeRole.attendant
    table_id: Optional[int] = None
    active: bool = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(CamelModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[EmployeeRole] = None
    table_id: Optional[int] = None
    active: Optional[bool] = None


class EmployeeAssignTable(CamelModel):
    table_id: Optional[int] = None


class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime


class EmployeeOrderItem(CamelModel):
    name: str
    quantity: int
    price: float


class EmployeeOrderCreate(CamelModel):
    employee_id: int
    table_id: int
    items: list[EmployeeOrderItem]


class EmployeeOrderResponse(CamelModel):
    id: int
    code: str
    employee_id: int
    employee_name: str
    table_id: int
    table_number: int
    items: list[EmployeeOrderItem]
    total: float
    created_at: datetime


class ReportItem(CamelModel):
    label: str
    value: float
    secondary: Optional[float] = None


class PaymentResponse(CamelModel):
    id: str
    reservation_id: Optional[str] = None
    event_id: Optional[str] = None
    client_id: str
    client_name: str
    amount: float
    method: str = "multicaixa"
    status: str
    reference: Optional[str] = None
    date: datetime


class PrivateEventCreate(CamelModel):
    type: EventType
    client_id: Optional[int] = None
    date: datetime
    guests: int
    notes: Optional[str] = None


class PrivateEventUpdate(CamelModel):
    type: Optional[EventType] = None
    date: Optional[datetime] = None
    guests: Optional[int] = None
    status: Optional[EventStatus] = None
    notes: Optional[str] = None
    budget: Optional[float] = None
    deposit_paid: Optional[bool] = None


class PrivateEventResponse(CamelModel):
    id: str
    code: str
    type: EventType
    client_id: str
    client_name: str
    date: datetime
    guests: int
    status: EventStatus
    notes: Optional[str] = None
    budget: Optional[float] = None
    deposit_paid: bool
    created_at: datetime


class MenuItemBase(CamelModel):
    name: str
    description: str
    category: MenuCategory
    price: float
    image_url: Optional[str] = None
    available: bool = True
    featured: bool = False
    allergens: list[str] = []


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[MenuCategory] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    available: Optional[bool] = None
    featured: Optional[bool] = None
    allergens: Optional[list[str]] = None


class MenuItemResponse(MenuItemBase):
    id: int
    created_at: datetime


class SiteImageResponse(CamelModel):
    key: str
    image_url: str
    updated_at: datetime


class SiteImageUpdate(CamelModel):
    image_url: str


class TransferRequestCreate(CamelModel):
    client_id: int
    vehicle_type: str
    vehicle_model: Optional[str] = None
    date: datetime
    time: str
    pickup_location: str
    notes: Optional[str] = None


class TransferRequestResponse(CamelModel):
    id: int
    client_id: int
    vehicle_type: str
    vehicle_model: Optional[str] = None
    date: datetime
    time: str
    pickup_location: str
    notes: Optional[str] = None
    status: str
    created_at: datetime
    
class ReservationApiCreate(CamelModel):
    clientId: Optional[int] = None
    tableId: int
    date: datetime
    time: str
    guests: int = 2
    notes: Optional[str] = None


class ReservationApiUpdate(CamelModel):
    tableId: Optional[int] = None
    date: Optional[datetime] = None
    time: Optional[str] = None
    guests: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ReservationApiResponse(CamelModel):
    id: str
    code: str
    clientId: str
    clientName: str
    tableId: str
    tableNumber: int
    date: datetime
    time: str
    guests: int
    status: str
    notes: Optional[str] = None
    createdAt: datetime
