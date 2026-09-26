from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Booking, Payment
from app.schemas import (
    PaymentRequest,
    PaymentResponse,
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

@router.post("/", response_model=PaymentResponse)
def create_payment(
    payment_data: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.booking_id == payment_data.booking_id,
            Booking.user_id == current_user.user_id
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )
    if booking.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Payment cannot be processed for this booking"
        )

    if payment_data.payment_status not in ["SUCCESS", "FAILED"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment status"
        )
    payment = Payment(
    booking_id=booking.booking_id,
    amount=booking.amount,
    status=payment_data.payment_status
    )

    db.add(payment)

    if payment_data.payment_status == "SUCCESS":
        booking.status = "CONFIRMED"
    else:
        booking.status = "FAILED"

    db.commit()
    db.refresh(payment)

    return {
        "payment_id": payment.payment_id,
        "booking_id": booking.booking_id,
        "amount": payment.amount,
        "payment_status": payment.status,
        "booking_status": booking.status
    }

