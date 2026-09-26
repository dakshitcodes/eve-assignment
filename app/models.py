from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)

from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)


class DiagnosticCentre(Base):
    __tablename__ = "diagnostic_centres"

    centre_id = Column(Integer, primary_key=True)
    centre_name = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)


class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    test_id = Column(Integer, primary_key=True)
    test_name = Column(String(100), nullable=False)


class CentreTest(Base):
    __tablename__ = "centre_tests"

    centre_test_id = Column(Integer, primary_key=True)
    test_id = Column(
        Integer,
        ForeignKey("diagnostic_tests.test_id"),
        nullable=False,
    )
    centre_id = Column(
        Integer,
        ForeignKey("diagnostic_centres.centre_id"),
        nullable=False,
    )
    test_price = Column(
        Numeric(10, 2),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "centre_id",
            "test_id",
            name="uq_centre_test",
        ),
        CheckConstraint(
            "test_price >= 0",
            name="ck_test_price_non_negative",
        ),
    )


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False,
    )
    test_id = Column(
        Integer,
        ForeignKey("diagnostic_tests.test_id"),
        nullable=False,
    )
    centre_id = Column(
        Integer,
        ForeignKey("diagnostic_centres.centre_id"),
        nullable=False,
    )
    appointment_time = Column(
        DateTime,
        nullable=False,
    )
    amount = Column(
        Numeric(10, 2),
        nullable=False,
    )
    status = Column(
        String(20),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "amount >= 0",
            name="ck_booking_amount_non_negative",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'CONFIRMED', 'FAILED', 'CANCELLED')",
            name="ck_booking_status",
        ),
    )


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True)
    booking_id = Column(
        Integer,
        ForeignKey("bookings.booking_id"),
        nullable=False,
    )
    amount = Column(
        Numeric(10, 2),
        nullable=False,
    )
    status = Column(
        String(20),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "amount >= 0",
            name="ck_payment_amount_non_negative",
        ),
        CheckConstraint(
            "status IN ('SUCCESS', 'FAILED')",
            name="ck_payment_status",
        ),
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    event_id = Column(String(255), primary_key=True)
    payment_id = Column(
        Integer,
        ForeignKey("payments.payment_id"),
        nullable=False,
    )
    event_type = Column(
        String(100),
        nullable=False,
    )
    received_at = Column(
        DateTime,
        nullable=False,
    )