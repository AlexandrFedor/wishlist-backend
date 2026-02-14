import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.item import Item
from app.models.reservation import Reservation
from app.models.user import User
from app.models.wishlist import Wishlist
from app.schemas.reservation import ReservationCreate, ReservationUpdate


async def create_reservation(
    db: AsyncSession,
    item_id: uuid.UUID,
    data: ReservationCreate,
    user: User | None = None,
) -> Reservation:
    # Lock the item row to prevent race conditions
    result = await db.execute(
        select(Item)
        .options(selectinload(Item.reservations), selectinload(Item.wishlist))
        .where(Item.id == item_id, Item.is_deleted.is_(False))
        .with_for_update()
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # Owner cannot reserve their own items
    if user and item.wishlist.user_id == user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot reserve your own item")

    # Guest must provide name
    if user is None and not data.guest_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Guest name is required")

    reserved_total = sum(r.amount for r in item.reservations)
    remaining = Decimal(str(item.price)) - reserved_total

    if remaining <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item is fully reserved")

    amount = Decimal(str(data.amount))

    if data.is_full_reservation:
        if reserved_total > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot fully reserve — partial contributions exist",
            )
        amount = Decimal(str(item.price))
    else:
        # Validate minimum contribution: min(10% of price, 100 RUB)
        min_amount = min(Decimal(str(item.price)) * Decimal("0.1"), Decimal("100"))
        if amount < min_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum contribution is {min_amount}",
            )
        if amount > remaining:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum contribution is {remaining}",
            )

    reservation = Reservation(
        item_id=item_id,
        user_id=user.id if user else None,
        guest_name=data.guest_name if user is None else None,
        guest_email=data.guest_email if user is None else None,
        amount=amount,
        is_full_reservation=data.is_full_reservation,
        message=data.message,
    )
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)
    return reservation


async def update_reservation(
    db: AsyncSession,
    reservation_id: uuid.UUID,
    data: ReservationUpdate,
    user: User | None = None,
) -> Reservation:
    result = await db.execute(
        select(Reservation).where(Reservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    # Only the reservation creator can update
    if user and reservation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your reservation")
    if user is None and reservation.user_id is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your reservation")

    if data.amount is not None:
        reservation.amount = Decimal(str(data.amount))
    if data.message is not None:
        reservation.message = data.message

    await db.commit()
    await db.refresh(reservation)
    return reservation


async def delete_reservation(
    db: AsyncSession,
    reservation_id: uuid.UUID,
    user: User | None = None,
) -> None:
    result = await db.execute(
        select(Reservation).where(Reservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    if user and reservation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your reservation")
    if user is None and reservation.user_id is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your reservation")

    await db.delete(reservation)
    await db.commit()


async def get_item_reservations(
    db: AsyncSession,
    item_id: uuid.UUID,
    requester: User | None = None,
) -> tuple[list[Reservation], bool]:
    """Returns (reservations, is_owner)."""
    result = await db.execute(
        select(Item).options(selectinload(Item.wishlist)).where(Item.id == item_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    is_owner = requester is not None and item.wishlist.user_id == requester.id

    res_result = await db.execute(
        select(Reservation).where(Reservation.item_id == item_id).order_by(Reservation.created_at)
    )
    reservations = list(res_result.scalars().all())
    return reservations, is_owner
