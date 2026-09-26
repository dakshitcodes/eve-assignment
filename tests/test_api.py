import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import (
    User,
    DiagnosticCentre,
    DiagnosticTest,
    CentreTest,
    Booking,
    Payment,
    WebhookEvent,
)
from app.security import sign_webhook_payload

client = TestClient(app)
WEBHOOK_SECRET = "test-payment-webhook-secret-at-least-32-chars"
CENTRE_ADMIN_KEY = "test-centre-admin-key-at-least-32-characters"


def post_webhook(payload, signature=None):
    headers = {}
    if signature is None:
        headers["X-Webhook-Signature"] = sign_webhook_payload(
            payload,
            WEBHOOK_SECRET,
        )
    else:
        headers["X-Webhook-Signature"] = signature

    return client.post(
        "/payments/webhook/",
        headers=headers,
        json=payload,
    )


def admin_headers():
    return {"X-Admin-Key": CENTRE_ADMIN_KEY}


@pytest.fixture(autouse=True)
def clean_database(monkeypatch):
    """
    Clean the database before every test.

    This makes every test independent from the others.
    """

    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setenv("CENTRE_ADMIN_API_KEY", CENTRE_ADMIN_KEY)
    db = SessionLocal()

    try:
        db.query(WebhookEvent).delete()
        db.query(Payment).delete()
        db.query(Booking).delete()
        db.query(CentreTest).delete()
        db.query(DiagnosticTest).delete()
        db.query(DiagnosticCentre).delete()
        db.query(User).delete()

        # reset PostgreSQL sequences so test data
        # always starts with predictable IDs
        db.execute(
            text(
                """
                ALTER SEQUENCE users_user_id_seq RESTART WITH 1;
                ALTER SEQUENCE diagnostic_centres_centre_id_seq RESTART WITH 1;
                ALTER SEQUENCE diagnostic_tests_test_id_seq RESTART WITH 1;
                ALTER SEQUENCE centre_tests_centre_test_id_seq RESTART WITH 1;
                ALTER SEQUENCE bookings_booking_id_seq RESTART WITH 1;
                ALTER SEQUENCE payments_payment_id_seq RESTART WITH 1;
                """
            )
        )

        db.commit()

    finally:
        db.close()

    seed_database()

    yield

    db = SessionLocal()

    try:
        db.query(WebhookEvent).delete()
        db.query(Payment).delete()
        db.query(Booking).delete()
        db.query(CentreTest).delete()
        db.query(DiagnosticTest).delete()
        db.query(DiagnosticCentre).delete()
        db.query(User).delete()

        db.commit()

    finally:
        db.close()


def seed_database():
    """
    Insert the minimum data required by the tests.
    """

    db = SessionLocal()

    try:
        centre1 = DiagnosticCentre(
            centre_name="Test Diagnostics Delhi",
            location="Delhi"
        )

        centre2 = DiagnosticCentre(
            centre_name="Test Diagnostics Dwarka",
            location="Dwarka"
        )

        test1 = DiagnosticTest(
            test_name="X Ray"
        )

        test2 = DiagnosticTest(
            test_name="CT Scan"
        )

        test3 = DiagnosticTest(
            test_name="MRI"
        )

        db.add_all([
            centre1,
            centre2,
            test1,
            test2,
            test3,
        ])

        db.commit()

        db.refresh(centre1)
        db.refresh(centre2)

        db.refresh(test1)
        db.refresh(test2)
        db.refresh(test3)

        centre_test1 = CentreTest(
            centre_id=centre1.centre_id,
            test_id=test1.test_id,
            test_price=500
        )

        centre_test2 = CentreTest(
            centre_id=centre1.centre_id,
            test_id=test2.test_id,
            test_price=1500
        )

        centre_test3 = CentreTest(
            centre_id=centre2.centre_id,
            test_id=test1.test_id,
            test_price=450
        )

        centre_test4 = CentreTest(
            centre_id=centre2.centre_id,
            test_id=test3.test_id,
            test_price=3000
        )

        db.add_all([
            centre_test1,
            centre_test2,
            centre_test3,
            centre_test4,
        ])

        db.commit()

    finally:
        db.close()


def signup_user(
    email="test@example.com",
    password="test123",
    user_name="Test User"
):
    response = client.post(
        "/auth/signup",
        json={
            "user_name": user_name,
            "email": email,
            "password": password,
        },
    )

    return response


def login_user(
    email="test@example.com",
    password="test123"
):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    return response


def get_auth_headers(
    email="test@example.com",
    password="test123"
):
    login_response = login_user(
        email=email,
        password=password
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# AUTH TESTS
# ============================================================


def test_signup_success():
    response = signup_user()

    assert response.status_code == 200

    data = response.json()

    assert "user_id" in data
    assert data["user_name"] == "Test User"
    assert data["email"] == "test@example.com"


def test_duplicate_signup():
    first_response = signup_user()

    assert first_response.status_code == 200

    second_response = signup_user()

    assert second_response.status_code == 409

    assert second_response.json()["detail"] == "Email already registered"


def test_login_success():
    signup_user()

    response = login_user()

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    signup_user()

    response = login_user(
        password="wrongpassword"
    )

    assert response.status_code == 401

    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email():
    response = login_user(
        email="unknown@example.com"
    )

    assert response.status_code == 401

    assert response.json()["detail"] == "Invalid email or password"

# ============================================================
# CENTRE TESTS
# ============================================================


def test_get_centres():
    response = client.get("/centres/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["centre_name"] == "Test Diagnostics Delhi"


def test_get_centre_tests():
    response = client.get("/centres/1/tests")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["test_name"] == "X Ray"
    assert data[0]["price"] == 500

    assert data[1]["test_name"] == "CT Scan"
    assert data[1]["price"] == 1500


def test_get_centre_with_no_matching_tests():
    response = client.get("/centres/999/tests")

    assert response.status_code == 200

    assert response.json() == []


def test_centre_management_requires_admin_key():
    response = client.post(
        "/centres/",
        json={"centre_name": "Managed Centre", "location": "Delhi"},
    )

    assert response.status_code == 401


def test_admin_can_manage_centre_and_offered_tests():
    headers = admin_headers()
    centre_response = client.post(
        "/centres/",
        headers=headers,
        json={"centre_name": "Managed Centre", "location": "Delhi"},
    )

    assert centre_response.status_code == 201
    centre = centre_response.json()
    centre_id = centre["centre_id"]

    update_response = client.patch(
        f"/centres/{centre_id}",
        headers=headers,
        json={"location": "Noida"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["location"] == "Noida"

    test_response = client.post(
        f"/centres/{centre_id}/tests",
        headers=headers,
        json={"test_name": "Managed MRI", "price": 1200},
    )
    assert test_response.status_code == 201
    centre_test = test_response.json()
    test_id = centre_test["test_id"]

    offer_update_response = client.patch(
        f"/centres/{centre_id}/tests/{test_id}",
        headers=headers,
        json={"price": 1350, "test_name": "MRI Scan"},
    )
    assert offer_update_response.status_code == 200
    assert offer_update_response.json()["price"] == 1350
    assert offer_update_response.json()["test_name"] == "MRI Scan"

    offers_response = client.get(f"/centres/{centre_id}/tests")
    assert offers_response.status_code == 200
    assert offers_response.json() == [
        {"test_id": test_id, "test_name": "MRI Scan", "price": 1350}
    ]

    delete_offer_response = client.delete(
        f"/centres/{centre_id}/tests/{test_id}",
        headers=headers,
    )
    assert delete_offer_response.status_code == 204

    delete_centre_response = client.delete(
        f"/centres/{centre_id}",
        headers=headers,
    )
    assert delete_centre_response.status_code == 204


# ============================================================
# BOOKING TESTS
# ============================================================


def test_create_booking_success():
    signup_user()

    headers = get_auth_headers()

    response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "test_id": 1,
            "centre_id": 1,
            "appointment_time": "2026-09-28T10:00:00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "booking_id" in data
    assert data["status"] == "PENDING"
    assert data["amount"] == 500


def test_create_booking_for_unavailable_test():
    signup_user()

    headers = get_auth_headers()

    response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "test_id": 3,
            "centre_id": 1,
            "appointment_time": "2026-09-28T10:00:00",
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Selected test is not available at this centre"
    )


def test_create_booking_without_authentication():
    response = client.post(
        "/bookings/",
        json={
            "test_id": 1,
            "centre_id": 1,
            "appointment_time": "2026-09-28T10:00:00",
        },
    )

    assert response.status_code in [401, 403]


# ============================================================
# PAYMENT TESTS
# ============================================================


def create_booking_for_test(
    test_id=1,
    centre_id=1
):
    signup_user()

    headers = get_auth_headers()

    response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_time": "2026-09-28T10:00:00",
        },
    )

    assert response.status_code == 200

    return response.json(), headers


def test_successful_payment():
    booking, headers = create_booking_for_test()

    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["booking_id"],
            "payment_status": "SUCCESS",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_status"] == "SUCCESS"
    assert data["booking_status"] == "CONFIRMED"
    assert data["amount"] == 500


def test_failed_payment():
    booking, headers = create_booking_for_test(
        test_id=2,
        centre_id=1
    )

    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["booking_id"],
            "payment_status": "FAILED",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_status"] == "FAILED"
    assert data["booking_status"] == "FAILED"
    assert data["amount"] == 1500


def test_failed_payment_can_be_retried():
    booking, headers = create_booking_for_test()

    failed_response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["booking_id"],
            "payment_status": "FAILED",
        },
    )
    assert failed_response.status_code == 200
    assert failed_response.json()["booking_status"] == "FAILED"

    retry_response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["booking_id"],
            "payment_status": "SUCCESS",
        },
    )
    assert retry_response.status_code == 200
    assert retry_response.json()["payment_status"] == "SUCCESS"
    assert retry_response.json()["booking_status"] == "CONFIRMED"
    assert retry_response.json()["payment_id"] != failed_response.json()["payment_id"]

    db = SessionLocal()
    try:
        payments = (
            db.query(Payment)
            .filter(Payment.booking_id == booking["booking_id"])
            .order_by(Payment.payment_id)
            .all()
        )
        assert [payment.status for payment in payments] == ["FAILED", "SUCCESS"]
    finally:
        db.close()


def test_invalid_payment_status():
    booking, headers = create_booking_for_test()

    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["booking_id"],
            "payment_status": "INVALID",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Invalid payment status"


def test_payment_for_nonexistent_booking():
    signup_user()

    headers = get_auth_headers()

    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": 9999,
            "payment_status": "SUCCESS",
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Booking not found"


def test_payment_for_already_processed_booking():
    booking, headers = create_booking_for_test()

    first_payment = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["booking_id"],
            "payment_status": "SUCCESS",
        },
    )

    assert first_payment.status_code == 200

    second_payment = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["booking_id"],
            "payment_status": "SUCCESS",
        },
    )

    assert second_payment.status_code == 400

    assert (
        second_payment.json()["detail"]
        == "Payment cannot be processed for this booking"
    )


# ============================================================
# PAYMENT OWNERSHIP TEST
# ============================================================


def test_user_cannot_pay_another_users_booking():
    first_booking, first_headers = create_booking_for_test()

    signup_user(
        email="second@example.com",
        password="test123",
        user_name="Second User"
    )

    second_headers = get_auth_headers(
        email="second@example.com",
        password="test123"
    )

    response = client.post(
        "/payments/",
        headers=second_headers,
        json={
            "booking_id": first_booking["booking_id"],
            "payment_status": "SUCCESS",
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Booking not found"


# ============================================================
# WEBHOOK TESTS
# ============================================================


def create_payment_for_webhook():
    booking, headers = create_booking_for_test()

    payment_response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["booking_id"],
            "payment_status": "SUCCESS",
        },
    )

    assert payment_response.status_code == 200

    payment = payment_response.json()

    return (
        booking["booking_id"],
        payment["payment_id"],
    )


def test_webhook_success():
    booking_id, payment_id = create_payment_for_webhook()

    response = post_webhook(
        {
            "event_id": "evt_test_001",
            "payment_id": payment_id,
            "event_type": "PAYMENT_STATUS_UPDATED",
            "payment_status": "SUCCESS",
        },
    )

    assert response.status_code == 200

    assert response.json()["message"] == "Webhook processed"


def test_webhook_invalid_payment():
    response = post_webhook(
        {
            "event_id": "evt_test_002",
            "payment_id": 9999,
            "event_type": "PAYMENT_STATUS_UPDATED",
            "payment_status": "SUCCESS",
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Payment not found"


def test_webhook_invalid_status():
    booking_id, payment_id = create_payment_for_webhook()

    response = post_webhook(
        {
            "event_id": "evt_test_003",
            "payment_id": payment_id,
            "event_type": "PAYMENT_STATUS_UPDATED",
            "payment_status": "INVALID",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Invalid payment status"


def test_webhook_updates_payment_and_booking():
    booking_id, payment_id = create_payment_for_webhook()

    response = post_webhook(
        {
            "event_id": "evt_test_004",
            "payment_id": payment_id,
            "event_type": "PAYMENT_STATUS_UPDATED",
            "payment_status": "FAILED",
        },
    )

    assert response.status_code == 200

    db = SessionLocal()

    try:
        payment = (
            db.query(Payment)
            .filter(Payment.payment_id == payment_id)
            .first()
        )

        booking = (
            db.query(Booking)
            .filter(Booking.booking_id == booking_id)
            .first()
        )

        assert payment.status == "FAILED"
        assert booking.status == "FAILED"

    finally:
        db.close()


def test_webhook_is_idempotent():
    booking_id, payment_id = create_payment_for_webhook()

    webhook_data = {
        "event_id": "evt_test_idempotent",
        "payment_id": payment_id,
        "event_type": "PAYMENT_STATUS_UPDATED",
        "payment_status": "SUCCESS",
    }

    first_response = post_webhook(webhook_data)

    assert first_response.status_code == 200

    assert (
        first_response.json()["message"]
        == "Webhook processed"
    )

    second_response = post_webhook(webhook_data)

    assert second_response.status_code == 200

    assert (
        second_response.json()["message"]
        == "Webhook already processed"
    )

    db = SessionLocal()

    try:
        events = (
            db.query(WebhookEvent)
            .filter(
                WebhookEvent.event_id
                == "evt_test_idempotent"
            )
            .all()
        )

        assert len(events) == 1

    finally:
        db.close()


def test_different_webhook_events_can_be_processed():
    booking_id, payment_id = create_payment_for_webhook()

    first_response = post_webhook(
        {
            "event_id": "evt_test_005",
            "payment_id": payment_id,
            "event_type": "PAYMENT_STATUS_UPDATED",
            "payment_status": "SUCCESS",
        },
    )

    assert first_response.status_code == 200

    # the payment is now CONFIRMED through the first webhook
    # this second event has a different event_id, so it is not
    # considered a duplicate.
    second_response = post_webhook(
        {
            "event_id": "evt_test_006",
            "payment_id": payment_id,
            "event_type": "PAYMENT_STATUS_UPDATED",
            "payment_status": "FAILED",
        },
    )

    assert second_response.status_code == 200

    assert (
        second_response.json()["message"]
        == "Webhook processed"
    )

def test_webhook_invalid_event_type():
    booking_id, payment_id = create_payment_for_webhook()

    response = post_webhook(
        {
            "event_id": "evt_invalid_type",
            "payment_id": payment_id,
            "event_type": "UNKNOWN_EVENT",
            "payment_status": "SUCCESS",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Unsupported webhook event type"
    )



def test_webhook_nonexistent_payment():
    response = post_webhook(
        {
            "event_id": "evt_missing_payment",
            "payment_id": 99999,
            "event_type": "PAYMENT_STATUS_UPDATED",
            "payment_status": "SUCCESS",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_webhook_rejects_missing_signature():
    response = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt_unsigned",
            "payment_id": 1,
            "event_type": "PAYMENT_STATUS_UPDATED",
            "payment_status": "SUCCESS",
        },
    )

    assert response.status_code == 401


def test_webhook_rejects_invalid_signature():
    response = post_webhook(
        {
            "event_id": "evt_bad_signature",
            "payment_id": 1,
            "event_type": "PAYMENT_STATUS_UPDATED",
            "payment_status": "SUCCESS",
        },
        signature="sha256=invalid",
    )

    assert response.status_code == 401


def test_webhook_fails_closed_without_secret(monkeypatch):
    monkeypatch.delenv("PAYMENT_WEBHOOK_SECRET")
    response = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt_unconfigured",
            "payment_id": 1,
            "event_type": "PAYMENT_STATUS_UPDATED",
            "payment_status": "SUCCESS",
        },
    )

    assert response.status_code == 503