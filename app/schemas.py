from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


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


class CentreTestResponse(BaseModel):
    test_id: int
    test_name: str
    price: float


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