from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking, Payment, WebhookEvent
from app.schemas import WebhookRequest, WebhookResponse


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "/webhook/",
    response_model=WebhookResponse,
)
def payment_webhook(
    webhook_data: WebhookRequest,
    db: Session = Depends(get_db),
):
    # 1. validate webhook event type
    if webhook_data.event_type != "PAYMENT_STATUS_UPDATED":
        raise HTTPException(
            status_code=400,
            detail="Unsupported webhook event type",
        )

    # 2. validate payment status
    if webhook_data.payment_status not in {"SUCCESS", "FAILED"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment status",
        )

    '''
    3. lock the payment row
    FOR UPDATE ensures that two concurrent webhook requests
    affecting the same payment cannot modify it simultaneously
    '''
    payment = (
        db.query(Payment)
        .filter(Payment.payment_id == webhook_data.payment_id)
        .with_for_update()
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    '''
    4. Check idempotency AFTER acquiring the lock
    
    This ordering is important.
    
    Request A:
    locks payment
    processes event
    commits

    Request B:
    waits for payment lock
    acquires lock after A commits
    sees event_id already exists
    returns safely
    '''
    existing_event = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.event_id == webhook_data.event_id)
        .first()
    )

    if existing_event:
        return {
            "message": "Webhook already processed",
        }

    # 5. find the associated booking
    booking = (
        db.query(Booking)
        .filter(Booking.booking_id == payment.booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    # 6. update payment and booking atomically
    payment.status = webhook_data.payment_status

    if webhook_data.payment_status == "SUCCESS":
        booking.status = "CONFIRMED"
    else:
        booking.status = "FAILED"

    # 7. record the webhook event
    event = WebhookEvent(
        event_id=webhook_data.event_id,
        payment_id=payment.payment_id,
        event_type=webhook_data.event_type,
        received_at=datetime.now(timezone.utc),
    )

    db.add(event)

    '''
    8. Commit everything as one transaction

    Either all changes succeed:

    payment update
    booking update
    webhook event

    or none of them are persisted.
    '''

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        # this can happen if another transaction inserted the
        # same event_id concurrently
        existing_event = (
            db.query(WebhookEvent)
            .filter(WebhookEvent.event_id == webhook_data.event_id)
            .first()
        )

        if existing_event:
            return {
                "message": "Webhook already processed",
            }

        raise HTTPException(
            status_code=500,
            detail="Failed to process webhook",
        )

    return {
        "message": "Webhook processed",
    }