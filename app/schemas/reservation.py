import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReservationCreate(BaseModel):
    amount: float = Field(gt=0)
    is_full_reservation: bool = False
    guest_name: str | None = None
    guest_email: str | None = None
    message: str | None = None


class ReservationUpdate(BaseModel):
    amount: float | None = Field(None, gt=0)
    message: str | None = None


class ReservationResponse(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    user_id: uuid.UUID | None = None
    guest_name: str | None = None
    amount: float
    is_full_reservation: bool
    message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReservationAnonymousResponse(BaseModel):
    """Response for wishlist owner — hides who reserved."""
    id: uuid.UUID
    item_id: uuid.UUID
    amount: float
    is_full_reservation: bool
    created_at: datetime

    model_config = {"from_attributes": True}
