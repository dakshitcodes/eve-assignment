from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, CentreTest, Booking
from app.schemas import (
    BookingCreateRequest,
    BookingResponse,
)

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)

@router.post("/", response_model=BookingResponse)
def create_booking(
    booking_data: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    centre_test = (
        db.query(CentreTest)
        .filter(
            CentreTest.centre_id == booking_data.centre_id,
            CentreTest.test_id == booking_data.test_id
        )
        .first()
    )

    if not centre_test:
        raise HTTPException(
            status_code=400,
            detail="Selected test is not available at this centre"
        )

    new_booking = Booking(
    user_id=current_user.user_id,
    test_id=booking_data.test_id,
    centre_id=booking_data.centre_id,
    appointment_time=booking_data.appointment_time,
    amount=centre_test.test_price,
    status="PENDING"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return {
        "booking_id": new_booking.booking_id,
        "status": new_booking.status,
        "amount": new_booking.amount
    }