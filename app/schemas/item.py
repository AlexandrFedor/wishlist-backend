import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    url: str | None = None
    price: float = Field(gt=0)
    currency: str = "RUB"
    image_url: str | None = None
    position: int = 0


class ItemUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    url: str | None = None
    price: float | None = Field(None, gt=0)
    currency: str | None = None
    image_url: str | None = None
    position: int | None = None


class ItemResponse(BaseModel):
    id: uuid.UUID
    wishlist_id: uuid.UUID
    title: str
    description: str | None = None
    url: str | None = None
    price: float
    currency: str
    image_url: str | None = None
    position: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AutofillRequest(BaseModel):
    url: str


class AutofillResponse(BaseModel):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    price: float | None = None
