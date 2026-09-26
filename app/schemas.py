from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, model_validator


class SignupRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class SignupResponse(BaseModel):
    user_id: int
    user_name: str
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


class BookingCreateRequest(BaseModel):
    test_id: int
    centre_id: int
    appointment_time: datetime


class BookingResponse(BaseModel):
    booking_id: int
    status: str
    amount: float


class CentreResponse(BaseModel):
    centre_id: int
    centre_name: str
    location: str


class CentreCreateRequest(BaseModel):
    centre_name: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=255)


class CentreUpdateRequest(BaseModel):
    centre_name: str | None = Field(default=None, min_length=1, max_length=100)
    location: str | None = Field(default=None, min_length=1, max_length=255)

    @model_validator(mode="after")
    def require_update_fields(self):
        if self.centre_name is None and self.location is None:
            raise ValueError("At least one centre field must be provided")
        return self


class CentreTestResponse(BaseModel):
    test_id: int
    test_name: str
    price: float


class CentreTestCreateRequest(BaseModel):
    test_name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0)


class CentreTestUpdateRequest(BaseModel):
    test_name: str | None = Field(default=None, min_length=1, max_length=100)
    price: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_update_fields(self):
        if self.test_name is None and self.price is None:
            raise ValueError("At least one test field must be provided")
        return self


class PaymentRequest(BaseModel):
    booking_id: int
    payment_status: str


class PaymentResponse(BaseModel):
    payment_id: int
    booking_id: int
    amount: float
    payment_status: str
    booking_status: str

class WebhookRequest(BaseModel):
    event_id: str
    payment_id: int
    event_type: str
    payment_status: str


class WebhookResponse(BaseModel):
    message: str