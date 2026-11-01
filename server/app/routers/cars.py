from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.car import Car
from app.schemas.car import CarCreate, CarUpdate, CarResponse
from app.utils.auth_deps import get_current_car_owner

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
# "/{car_id}" (car_id="mine") and fail UUID parsing at the database query.
@router.get("/mine", response_model=list[CarResponse])
def list_my_cars(
    current_car_owner: dict = Depends(get_current_car_owner),
    db: Session = Depends(get_db),
):
    """List all of the current car owner's own cars, including inactive ones."""
    cars = db.query(Car).filter(Car.owner_id == current_car_owner["id"]).all()
    return [CarResponse.model_validate(car) for car in cars]


@router.get("", response_model=list[CarResponse])
def browse_cars(
    category: Optional[str] = None,
    city: Optional[str] = None,
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Browse publicly listed cars. Public endpoint — no authentication
    required. Only ever returns is_active cars; owners see their full
    inventory (including inactive listings) via GET /cars/mine instead.
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

    cars = query.offset(skip).limit(limit).all()
    return [CarResponse.model_validate(car) for car in cars]


@router.get("/{car_id}", response_model=CarResponse)
def get_car(car_id: str, db: Session = Depends(get_db)):
    """View a single car's details. Public — only shows active listings."""
    car = db.query(Car).filter(Car.id == car_id, Car.is_active == True).first()  # noqa: E712
    if not car:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    return CarResponse.model_validate(car)


@router.patch("/{car_id}", response_model=CarResponse)
def update_car(
    car_id: str,
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
    car_id: str,
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
