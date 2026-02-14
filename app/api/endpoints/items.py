import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.item import AutofillRequest, AutofillResponse, ItemCreate, ItemResponse, ItemUpdate
from app.services import item_service
from app.services.scraper_service import scrape_url

router = APIRouter(tags=["items"])


@router.post("/wishlists/{wishlist_id}/items", response_model=ItemResponse, status_code=201)
async def create_item(
    wishlist_id: uuid.UUID,
    data: ItemCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await item_service.create_item(db, wishlist_id, user.id, data)


@router.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: uuid.UUID,
    data: ItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await item_service.update_item(db, item_id, user.id, data)


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await item_service.delete_item(db, item_id, user.id)


@router.post("/items/autofill", response_model=AutofillResponse)
async def autofill_item(data: AutofillRequest):
    return scrape_url(data.url)
