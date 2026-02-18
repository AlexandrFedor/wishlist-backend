import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class WishlistCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_public: bool = True
    event_date: date | None = None


class WishlistUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_public: bool | None = None
    event_date: date | None = None


class WishlistResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str | None = None
    slug: str
    is_public: bool
    event_date: date | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WishlistListResponse(WishlistResponse):
    items_count: int = 0
    reserved_count: int = 0


class WishlistWithItemsResponse(WishlistResponse):
    items: list["ItemInWishlist"] = []


class ItemInWishlist(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    url: str | None = None
    price: float
    currency: str
    image_url: str | None = None
    position: int
    reserved_amount: float = 0
    is_fully_reserved: bool = False
    reservation_count: int = 0

    model_config = {"from_attributes": True}
