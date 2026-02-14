import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.schemas.reservation import (
    ReservationAnonymousResponse,
    ReservationCreate,
    ReservationResponse,
    ReservationUpdate,
)
from app.services import reservation_service

router = APIRouter(tags=["reservations"])


@router.post("/items/{item_id}/reserve", response_model=ReservationResponse, status_code=201)
async def reserve_item(
    item_id: uuid.UUID,
    data: ReservationCreate,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    reservation = await reservation_service.create_reservation(db, item_id, data, user)

    # Emit socket event
    from app.core.websocket import sio
    from sqlalchemy import select
    from app.models.item import Item
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Item).options(selectinload(Item.wishlist)).where(Item.id == item_id)
    )
    item = result.scalar_one_or_none()
    if item:
        await sio.emit(
            "item:reserved",
            {"item_id": str(item_id), "reservation_id": str(reservation.id)},
            room=f"wishlist:{item.wishlist.slug}",
        )

    return reservation


@router.put("/reservations/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: uuid.UUID,
    data: ReservationUpdate,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    return await reservation_service.update_reservation(db, reservation_id, data, user)


@router.delete("/reservations/{reservation_id}", status_code=204)
async def delete_reservation(
    reservation_id: uuid.UUID,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    # Get item info before deletion for socket event
    from sqlalchemy import select
    from app.models.reservation import Reservation
    from app.models.item import Item
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Reservation).where(Reservation.id == reservation_id)
    )
    res = result.scalar_one_or_none()
    item_id = res.item_id if res else None

    await reservation_service.delete_reservation(db, reservation_id, user)

    if item_id:
        from app.core.websocket import sio

        result = await db.execute(
            select(Item).options(selectinload(Item.wishlist)).where(Item.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item:
            await sio.emit(
                "item:unreserved",
                {"item_id": str(item_id), "reservation_id": str(reservation_id)},
                room=f"wishlist:{item.wishlist.slug}",
            )


@router.get("/items/{item_id}/reservations")
async def list_reservations(
    item_id: uuid.UUID,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    reservations, is_owner = await reservation_service.get_item_reservations(db, item_id, user)
    if is_owner:
        return [ReservationAnonymousResponse.model_validate(r) for r in reservations]
    return [ReservationResponse.model_validate(r) for r in reservations]
