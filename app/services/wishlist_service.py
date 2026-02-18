import re
import secrets
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.item import Item
from app.models.wishlist import Wishlist
from app.schemas.wishlist import WishlistCreate, WishlistUpdate


def _generate_slug(title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower().strip()).strip("-")
    if not base:
        base = "wishlist"
    suffix = secrets.token_urlsafe(4)
    return f"{base}-{suffix}"


async def get_user_wishlists(db: AsyncSession, user_id: uuid.UUID) -> list[Wishlist]:
    result = await db.execute(
        select(Wishlist)
        .options(selectinload(Wishlist.items).selectinload(Item.reservations))
        .where(Wishlist.user_id == user_id)
        .order_by(Wishlist.created_at.desc())
    )
    return list(result.scalars().all())


async def create_wishlist(db: AsyncSession, user_id: uuid.UUID, data: WishlistCreate) -> Wishlist:
    wishlist = Wishlist(
        user_id=user_id,
        title=data.title,
        description=data.description,
        slug=_generate_slug(data.title),
        is_public=data.is_public,
        event_date=data.event_date,
    )
    db.add(wishlist)
    await db.commit()
    await db.refresh(wishlist)
    return wishlist


async def get_wishlist(db: AsyncSession, wishlist_id: uuid.UUID, user_id: uuid.UUID) -> Wishlist:
    result = await db.execute(
        select(Wishlist)
        .options(selectinload(Wishlist.items).selectinload(Item.reservations))
        .where(Wishlist.id == wishlist_id, Wishlist.user_id == user_id)
    )
    wishlist = result.scalar_one_or_none()
    if wishlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return wishlist


async def get_wishlist_by_slug(db: AsyncSession, slug: str) -> Wishlist:
    result = await db.execute(
        select(Wishlist)
        .options(selectinload(Wishlist.items).selectinload(Item.reservations))
        .where(Wishlist.slug == slug, Wishlist.is_public.is_(True))
    )
    wishlist = result.scalar_one_or_none()
    if wishlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return wishlist


async def update_wishlist(
    db: AsyncSession, wishlist_id: uuid.UUID, user_id: uuid.UUID, data: WishlistUpdate
) -> Wishlist:
    wishlist = await get_wishlist(db, wishlist_id, user_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(wishlist, key, value)
    await db.commit()
    await db.refresh(wishlist)
    return wishlist


async def delete_wishlist(db: AsyncSession, wishlist_id: uuid.UUID, user_id: uuid.UUID) -> None:
    wishlist = await get_wishlist(db, wishlist_id, user_id)
    await db.delete(wishlist)
    await db.commit()
