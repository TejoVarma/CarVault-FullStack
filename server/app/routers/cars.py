from typing import Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import tuple_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.car import Car
from app.schemas.car import CarCreate, CarPage, CarUpdate, CarResponse
from app.utils.auth_deps import get_current_car_owner
from app.utils.pagination import decode_cursor, encode_cursor

router = APIRouter()


@router.post("", response_model=CarResponse, status_code=status.HTTP_201_CREATED)
def create_car(
    car_data: CarCreate,
    current_car_owner: dict = Depends(get_current_car_owner),
    db: Session = Depends(get_db),
):
    """List a new car. Requires the car_owner role."""
    new_car = Car(owner_id=current_car_owner["id"], **car_data.model_dump())
    db.add(new_car)
    db.commit()
    db.refresh(new_car)
    return CarResponse.model_validate(new_car)


# IMPORTANT: this must be declared BEFORE /{car_id} — FastAPI matches routes
# in declaration order, and "/mine" would otherwise be captured by
# "/{car_id}" (car_id="mine") and be rejected with a 422 as an invalid UUID.
@router.get("/mine", response_model=list[CarResponse])
def list_my_cars(
    current_car_owner: dict = Depends(get_current_car_owner),
    db: Session = Depends(get_db),
):
    """List all of the current car owner's own cars, including inactive ones."""
    cars = (
        db.query(Car)
        .filter(Car.owner_id == current_car_owner["id"])
        .order_by(Car.created_at.desc(), Car.id.desc())
        .all()
    )
    return [CarResponse.model_validate(car) for car in cars]


@router.get("", response_model=CarPage, responses={422: {"description": "Invalid cursor or filter value"}})
def browse_cars(
    category: Optional[str] = None,
    city: Optional[str] = None,
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100, description="Cars per page"),
    cursor: Optional[str] = Query(None, description="next_cursor from the previous page"),
    db: Session = Depends(get_db),
):
    """
    Browse publicly listed cars. Public endpoint — no authentication
    required. Only ever returns is_active cars; owners see their full
    inventory (including inactive listings) via GET /cars/mine instead.

    Keyset-paginated, newest first: pass the previous page's next_cursor to
    get the cars that come after it. next_cursor is null on the last page.
    """
    query = db.query(Car).filter(Car.is_active == True)  # noqa: E712

    if category:
        query = query.filter(Car.category == category)
    if city:
        query = query.filter(Car.city.ilike(f"%{city}%"))
    if min_price is not None:
        query = query.filter(Car.daily_rate >= min_price)
    if max_price is not None:
        query = query.filter(Car.daily_rate <= max_price)

    if cursor:
        after_created_at, after_id = decode_cursor(cursor)
        query = query.filter(tuple_(Car.created_at, Car.id) < tuple_(after_created_at, after_id))

    # (created_at, id) is a total order, so a cursor points at exactly one
    # place in the list. Fetching one extra row tells us whether a next page exists.
    rows = query.order_by(Car.created_at.desc(), Car.id.desc()).limit(limit + 1).all()
    page = rows[:limit]
    next_cursor = encode_cursor(page[-1].created_at, page[-1].id) if len(rows) > limit else None
    return CarPage(items=[CarResponse.model_validate(car) for car in page], next_cursor=next_cursor)


@router.get("/{car_id}", response_model=CarResponse)
def get_car(car_id: UUID, db: Session = Depends(get_db)):
    """View a single car's details. Public — only shows active listings."""
    car = db.query(Car).filter(Car.id == car_id, Car.is_active == True).first()  # noqa: E712
    if not car:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    return CarResponse.model_validate(car)


@router.patch("/{car_id}", response_model=CarResponse)
def update_car(
    car_id: UUID,
    car_data: CarUpdate,
    current_car_owner: dict = Depends(get_current_car_owner),
    db: Session = Depends(get_db),
):
    """Edit a car. Must be owned by the current car owner."""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    if str(car.owner_id) != current_car_owner["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this car"
        )

    updates = car_data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(car, field, value)

    db.commit()
    db.refresh(car)
    return CarResponse.model_validate(car)


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car(
    car_id: UUID,
    current_car_owner: dict = Depends(get_current_car_owner),
    db: Session = Depends(get_db),
):
    """Delete a car. Must be owned by the current car owner."""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    if str(car.owner_id) != current_car_owner["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this car"
        )

    db.delete(car)
    db.commit()
    return None
