import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.wishlist import (
    ItemInWishlist,
    WishlistCreate,
    WishlistListResponse,
    WishlistResponse,
    WishlistUpdate,
    WishlistWithItemsResponse,
)
from app.services import wishlist_service

router = APIRouter(tags=["wishlists"])


@router.get("/wishlists", response_model=list[WishlistListResponse])
async def list_wishlists(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wishlists = await wishlist_service.get_user_wishlists(db, user.id)
    return [_build_wishlist_list_response(w) for w in wishlists]


@router.post("/wishlists", response_model=WishlistResponse, status_code=201)
async def create_wishlist(
    data: WishlistCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await wishlist_service.create_wishlist(db, user.id, data)


@router.get("/wishlists/{wishlist_id}", response_model=WishlistWithItemsResponse)
async def get_wishlist(
    wishlist_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wishlist = await wishlist_service.get_wishlist(db, wishlist_id, user.id)
    return _build_wishlist_response(wishlist, is_owner=True)


@router.put("/wishlists/{wishlist_id}", response_model=WishlistResponse)
async def update_wishlist(
    wishlist_id: uuid.UUID,
    data: WishlistUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await wishlist_service.update_wishlist(db, wishlist_id, user.id, data)


@router.delete("/wishlists/{wishlist_id}", status_code=204)
async def delete_wishlist(
    wishlist_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await wishlist_service.delete_wishlist(db, wishlist_id, user.id)


@router.get("/w/{slug}", response_model=WishlistWithItemsResponse)
async def get_public_wishlist(slug: str, db: AsyncSession = Depends(get_db)):
    wishlist = await wishlist_service.get_wishlist_by_slug(db, slug)
    return _build_wishlist_response(wishlist, is_owner=False)


def _build_wishlist_response(wishlist, *, is_owner: bool) -> WishlistWithItemsResponse:
    items = []
    for item in wishlist.items:
        if item.is_deleted:
            continue
        reserved_amount = float(sum(r.amount for r in item.reservations))
        is_fully_reserved = reserved_amount >= float(item.price)
        items.append(
            ItemInWishlist(
                id=item.id,
                title=item.title,
                description=item.description,
                url=item.url,
                price=float(item.price),
                currency=item.currency,
                image_url=item.image_url,
                position=item.position,
                reserved_amount=reserved_amount,
                is_fully_reserved=is_fully_reserved,
                reservation_count=len(item.reservations),
            )
        )
    items.sort(key=lambda i: i.position)

    return WishlistWithItemsResponse(
        id=wishlist.id,
        user_id=wishlist.user_id,
        title=wishlist.title,
        description=wishlist.description,
        slug=wishlist.slug,
        is_public=wishlist.is_public,
        event_date=wishlist.event_date,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        items=items,
    )


def _build_wishlist_list_response(wishlist) -> WishlistListResponse:
    items_count = 0
    reserved_count = 0
    for item in wishlist.items:
        if item.is_deleted:
            continue
        items_count += 1
        if item.reservations:
            reserved_count += 1

    return WishlistListResponse(
        id=wishlist.id,
        user_id=wishlist.user_id,
        title=wishlist.title,
        description=wishlist.description,
        slug=wishlist.slug,
        is_public=wishlist.is_public,
        event_date=wishlist.event_date,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        items_count=items_count,
        reserved_count=reserved_count,
    )
