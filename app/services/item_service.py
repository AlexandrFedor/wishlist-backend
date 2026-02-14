import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.item import Item
from app.models.wishlist import Wishlist
from app.schemas.item import ItemCreate, ItemUpdate


async def _get_wishlist_owned(db: AsyncSession, wishlist_id: uuid.UUID, user_id: uuid.UUID) -> Wishlist:
    result = await db.execute(
        select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user_id)
    )
    wishlist = result.scalar_one_or_none()
    if wishlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return wishlist


async def _get_item_owned(db: AsyncSession, item_id: uuid.UUID, user_id: uuid.UUID) -> Item:
    result = await db.execute(
        select(Item)
        .join(Wishlist)
        .where(Item.id == item_id, Wishlist.user_id == user_id, Item.is_deleted.is_(False))
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


async def create_item(
    db: AsyncSession, wishlist_id: uuid.UUID, user_id: uuid.UUID, data: ItemCreate
) -> Item:
    await _get_wishlist_owned(db, wishlist_id, user_id)
    item = Item(wishlist_id=wishlist_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_item(
    db: AsyncSession, item_id: uuid.UUID, user_id: uuid.UUID, data: ItemUpdate
) -> Item:
    item = await _get_item_owned(db, item_id, user_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item_id: uuid.UUID, user_id: uuid.UUID) -> None:
    item = await _get_item_owned(db, item_id, user_id)
    # Soft delete if item has reservations
    result = await db.execute(
        select(Item)
        .options(selectinload(Item.reservations))
        .where(Item.id == item_id)
    )
    item_with_rels = result.scalar_one()
    if item_with_rels.reservations:
        item_with_rels.is_deleted = True
    else:
        await db.delete(item_with_rels)
    await db.commit()
