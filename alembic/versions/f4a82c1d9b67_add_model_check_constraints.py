"""add model check constraints

Revision ID: f4a82c1d9b67
Revises: 9260dc171c16
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f4a82c1d9b67'
down_revision: Union[str, Sequence[str], None] = '9260dc171c16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        'ck_test_price_non_negative',
        'centre_tests',
        'test_price >= 0',
    )
    op.create_check_constraint(
        'ck_booking_amount_non_negative',
        'bookings',
        'amount >= 0',
    )
    op.create_check_constraint(
        'ck_booking_status',
        'bookings',
        "status IN ('PENDING', 'CONFIRMED', 'FAILED', 'CANCELLED')",
    )
    op.create_check_constraint(
        'ck_payment_amount_non_negative',
        'payments',
        'amount >= 0',
    )
    op.create_check_constraint(
        'ck_payment_status',
        'payments',
        "status IN ('SUCCESS', 'FAILED')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_payment_status', 'payments', type_='check')
    op.drop_constraint('ck_payment_amount_non_negative', 'payments', type_='check')
    op.drop_constraint('ck_booking_status', 'bookings', type_='check')
    op.drop_constraint('ck_booking_amount_non_negative', 'bookings', type_='check')
    op.drop_constraint('ck_test_price_non_negative', 'centre_tests', type_='check')
