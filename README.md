# EVE Healthcare Backend API

Backend service for diagnostic test bookings and simulated payments, developed as part of the EVE Healthcare SDE Intern Backend Engineering Assignment.

The application provides authenticated users with the ability to browse diagnostic centres and tests, create diagnostic test bookings, make simulated payments, and process payment-provider webhooks.

The implementation focuses on clean API design, relational database modelling, validation, authorization, transactional consistency, webhook idempotency, and automated testing.

---

## Tech Stack

* **Python**
* **FastAPI**
* **PostgreSQL**
* **SQLAlchemy**
* **Alembic**
* **JWT Authentication**
* **Argon2 Password Hashing**
* **Pytest**

---

## Features

* User signup
* User login
* JWT-based authentication
* Password hashing using Argon2
* Request validation
* Diagnostic centre retrieval
* Diagnostic test retrieval
* Centre-specific test pricing
* Authenticated diagnostic test bookings
* Booking lifecycle management through payment processing
* Simulated payment processing
* Successful and failed payment handling
* Payment ownership validation
* Payment webhook processing
* Idempotent webhook handling
* PostgreSQL row-level locking for concurrent webhook processing
* Database-level constraints
* Alembic database migrations
* Automated API tests
* Swagger/OpenAPI documentation

---

# Project Structure

```text
eve-health-assignment/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── dependencies.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   │
│   └── routers/
│       ├── __init__.py
│       ├── auth.py
│       ├── bookings.py
│       ├── centres.py
│       ├── payments.py
│       └── webhooks.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
│   └── test_api.py
│
├── .env.example
├── .gitignore
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# Getting Started

## Prerequisites

Make sure the following are installed:

* Python 3.10+
* PostgreSQL
* Git

---

## 1. Clone the Repository

```bash
git clone <your-github-repository-url>
cd eve-health-assignment
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Create the PostgreSQL Database

Create a PostgreSQL database named:

```text
eve_healthcare
```

For example:

```sql
CREATE DATABASE eve_healthcare;
```

---

## 5. Configure Environment Variables

Create a `.env` file in the project root.

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/eve_healthcare
SECRET_KEY=your_long_random_secret_key
CENTRE_ADMIN_API_KEY=your_long_random_secret_key
PAYMENT_WEBHOOK_SECRET=your_long_random_secret_key
```

The `SECRET_KEY` should be a long random value and should not be committed to the repository.

The actual `.env` file should remain excluded through `.gitignore`.

A `.env.example` file is provided to show the required configuration.

---

## 6. Run Database Migrations

Apply the Alembic migrations:

```bash
alembic upgrade head
```

Check the current migration:

```bash
alembic current
```

---

## 7. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive Swagger/OpenAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

# API Documentation

## Health Check

### `GET /health`

Returns the health status of the API.

Example response:

```json
{
  "status": "ok"
}
```

---

# Authentication

Authentication is JWT-based.

Protected endpoints require the following HTTP header:

```http
Authorization: Bearer <jwt-token>
```

---

## Signup

### `POST /auth/signup`

Creates a new user account.

### Request

```json
{
  "user_name": "John Doe",
  "email": "john@example.com",
  "password": "test123"
}
```

### Example Response

```json
{
  "user_id": 1,
  "user_name": "John Doe",
  "email": "john@example.com"
}
```

### Validation

* Username must be between 1 and 50 characters.
* Email must be valid.
* Password must be between 6 and 128 characters.
* Email must be unique.

If the email is already registered, the API returns:

```text
409 Conflict
```

---

## Login

### `POST /auth/login`

Authenticates an existing user and returns a JWT access token.

### Request

```json
{
  "email": "john@example.com",
  "password": "test123"
}
```

### Response

```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```

The returned access token must be supplied when accessing protected endpoints.

---

# Diagnostic Centres

## Get Diagnostic Centres

### `GET /centres/`

Returns the available diagnostic centres.

### Example Response

```json
[
  {
    "centre_id": 1,
    "centre_name": "Adhiraj Focus Diagnostics Delhi",
    "location": "Delhi"
  }
]
```

---

## Get Tests Available at a Centre

### `GET /centres/{centre_id}/tests`

Returns the diagnostic tests available at a particular centre along with their prices.

### Example

```http
GET /centres/1/tests
```

### Response

```json
[
  {
    "test_id": 1,
    "test_name": "X Ray",
    "price": 500
  },
  {
    "test_id": 2,
    "test_name": "CT Scan",
    "price": 1500
  }
]
```

## Centre and Test Management

Write operations require the `X-Admin-Key` header, matched against `CENTRE_ADMIN_API_KEY` in
the server environment. Keep this key private; user JWTs do not grant administrative access.

* `POST /centres/` creates a centre with `centre_name` and `location`.
* `PATCH /centres/{centre_id}` updates either centre field.
* `DELETE /centres/{centre_id}` removes a centre that has no bookings.
* `POST /centres/{centre_id}/tests` creates or attaches a test and its centre-specific `price`.
* `PATCH /centres/{centre_id}/tests/{test_id}` updates the offered price and/or test name.
* `DELETE /centres/{centre_id}/tests/{test_id}` removes the test offering without deleting the test.

For example, create an offering with:

```http
POST /centres/1/tests
X-Admin-Key: <CENTRE_ADMIN_API_KEY>
Content-Type: application/json

{"test_name": "MRI", "price": 1200}
```

---

# Booking System

Authenticated users can create diagnostic test bookings.

A booking contains:

* Patient/user
* Diagnostic test
* Diagnostic centre
* Appointment date/time
* Amount
* Booking status

The booking model supports the following states:

```text
PENDING
CONFIRMED
FAILED
CANCELLED
```

---

## Create Booking

### `POST /bookings/`

Authentication required.

### Request

```json
{
  "test_id": 1,
  "centre_id": 1,
  "appointment_time": "2026-09-28T10:00:00"
}
```

### Example Response

```json
{
  "booking_id": 1,
  "status": "PENDING",
  "amount": 500
}
```

A newly created booking starts in:

```text
PENDING
```

---

## Booking State Flow

A newly created booking starts in:

```text
PENDING
```

A successful payment changes the booking from:

```text
PENDING → CONFIRMED
```

A failed payment changes the booking from:

```text
PENDING → FAILED
```

The database model also supports:

```text
CANCELLED
```

as a reserved booking state for future cancellation functionality. No cancellation endpoint is currently implemented.

---

# Booking Amount

The booking stores the price applicable at the time the booking is created.

For example:

```text
Centre: Centre 1
Test: X Ray
Price at booking time: ₹500
```

The booking stores:

```text
amount = ₹500
```

If the centre subsequently changes the X-Ray price to ₹600, the existing booking continues to retain:

```text
₹500
```

This preserves the historical transaction amount associated with the booking.

---

# Simulated Payments

The assignment requires a simulated payment service rather than integration with a real payment gateway.

## Create Payment

### `POST /payments/`

Authentication required.

### Request

```json
{
  "booking_id": 1,
  "payment_status": "SUCCESS"
}
```

Supported payment statuses:

```text
SUCCESS
FAILED
```

---

## Successful Payment

When a simulated payment succeeds:

```text
Payment:
SUCCESS

Booking:
CONFIRMED
```

### Example Response

```json
{
  "payment_id": 1,
  "booking_id": 1,
  "amount": 500,
  "payment_status": "SUCCESS",
  "booking_status": "CONFIRMED"
}
```

---

## Failed Payment

When a simulated payment fails:

```text
Payment:
FAILED

Booking:
FAILED
```

### Example Response

```json
{
  "payment_id": 1,
  "booking_id": 1,
  "amount": 500,
  "payment_status": "FAILED",
  "booking_status": "FAILED"
}
```

---

## Payment Validation

Payments are validated before processing.

The implementation handles cases including:

* Non-existent booking IDs
* Payments made for another user's booking
* Invalid payment statuses
* Attempts to charge an already confirmed booking
* Failed payment attempts

A payment can be processed for a pending booking. If the latest attempt failed, the user can retry;
once an attempt succeeds, the confirmed booking cannot be charged again. Each attempt is stored as
a separate payment record.

---

# Payment Webhook

## `POST /payments/webhook/`

The webhook endpoint simulates a payment provider sending payment-status updates to the backend.
Requests must include an `X-Webhook-Signature` header containing `sha256=` followed by the
hexadecimal HMAC-SHA256 signature of the canonical JSON payload. Canonicalize by sorting object
keys, using compact separators (`,` and `:`), and encoding as UTF-8 before signing. The signing key
is `PAYMENT_WEBHOOK_SECRET`; webhook requests are rejected if the secret is not configured or the
signature does not match.

### Request

```json
{
  "event_id": "evt_123",
  "payment_id": 1,
  "event_type": "PAYMENT_STATUS_UPDATED",
  "payment_status": "SUCCESS"
}
```

Supported event type:

```text
PAYMENT_STATUS_UPDATED
```

Supported payment statuses:

```text
SUCCESS
FAILED
```

---

# Webhook Idempotency

Webhook processing is designed to be **idempotent**.

If evt_123 has already been processed, the request is treated as a duplicate. The existing payment and associated booking are not processed again.

Each webhook contains a unique:

```text
event_id
```

The backend stores processed webhook events in the `webhook_events` table.

The `event_id` is used as the primary key, providing a database-level uniqueness guarantee.

---

## Duplicate Webhook

If the same webhook event is received again, it is not processed a second time.

For example:

```json
{
  "event_id": "evt_123",
  "payment_id": 1,
  "event_type": "PAYMENT_STATUS_UPDATED",
  "payment_status": "SUCCESS"
}
```

If evt_123 has already been processed, the request is treated as a duplicate. The existing payment and associated booking are not processed again.

Example response:

```json
{
  "message": "Webhook already processed"
}
```

---

# Concurrent Webhook Protection

The webhook implementation also protects against concurrent processing of the same payment.

A PostgreSQL row-level lock is used when retrieving the payment:

```sql
SELECT ... FOR UPDATE
```

This ensures that concurrent webhook requests attempting to modify the same payment cannot simultaneously perform conflicting updates.

The processing flow is:

```text
Webhook Request
       │
       ▼
Validate Event
       │
       ▼
Lock Payment Row
       │
       ▼
Check Event ID
       │
       ▼
Find Booking
       │
       ▼
Update Payment
       │
       ▼
Update Booking
       │
       ▼
Record Webhook Event
       │
       ▼
Commit Transaction
```

The payment update, booking update, and webhook event insertion are performed within the same database transaction.

Therefore:

```text
All changes succeed
        OR
All changes are rolled back
```

This prevents partially applied webhook operations.

---

# Database Design

The application uses PostgreSQL with SQLAlchemy.

The primary entities are:

```text
Users
Diagnostic Centres
Diagnostic Tests
Centre Tests
Bookings
Payments
Webhook Events
```

---

## Users

Stores application users.

Important fields include:

* User ID
* Username
* Email
* Password hash

The email is unique.

Passwords are never stored in plaintext.

---

## Diagnostic Centres

Stores diagnostic centre information.

Important fields include:

* Centre ID
* Centre name
* Location

---

## Diagnostic Tests

Stores available diagnostic tests.

Important fields include:

* Test ID
* Test name

---

## Centre Tests

Represents the relationship between diagnostic centres and diagnostic tests.

A diagnostic test can be offered by multiple centres, and a centre can offer multiple diagnostic tests.

Therefore, the relationship is represented using the `centre_tests` table.

The table stores:

* Centre
* Test
* Price

The price belongs to the centre-test relationship because the same diagnostic test can have different prices at different centres.

A uniqueness constraint is applied to:

```text
(centre_id, test_id)
```

---

## Bookings

Stores diagnostic test appointments.

Important fields include:

* Booking ID
* User
* Diagnostic test
* Diagnostic centre
* Appointment date/time
* Amount
* Booking status

The booking model supports the following states:

```text
PENDING
CONFIRMED
FAILED
CANCELLED
```

The booking amount represents the price at the time of booking.

---

## Payments

Stores simulated payment attempts.

Important fields include:

* Payment ID
* Booking ID
* Amount
* Payment status

Supported payment statuses:

```text
SUCCESS
FAILED
```

Multiple payment attempts can be associated with a booking. A failed attempt may be retried, while a
successful attempt leaves the booking confirmed and prevents further payment processing.

---

## Webhook Events

Stores processed payment webhook events.

Important fields include:

* Event ID
* Payment ID
* Event type
* Received timestamp

The `event_id` provides the idempotency mechanism for webhook processing.

---

# Database Constraints

The application uses database-level constraints in addition to application-level validation.

Examples include:

### Required fields

Important fields use:

```sql
NOT NULL
```

### Centre/Test uniqueness

```text
UNIQUE(centre_id, test_id)
```

### Non-negative prices

Prices cannot be negative.

### Non-negative amounts

Booking/payment amounts cannot be negative.

### Booking status

The booking model supports the following states:

```text
PENDING
CONFIRMED
FAILED
CANCELLED
```

### Payment status

Only supported payment states are accepted:

```text
SUCCESS
FAILED
```

These constraints provide an additional layer of protection against invalid database state.

---

# Security

## Password Hashing

Passwords are hashed using Argon2 through `pwdlib`.

Plaintext passwords are never stored in the database.

---

## JWT Authentication

JWT access tokens are used to authenticate protected API requests.

The JWT secret is loaded from an environment variable rather than being hardcoded into the application.

Invalid or expired authentication tokens result in:

```text
401 Unauthorized
```

---

## Authorization

Authentication and authorization are handled separately.

A valid JWT identifies the authenticated user, while ownership checks ensure that users cannot perform operations on resources belonging to other users.

For example, a user cannot make a payment for another user's booking.

---

## Environment Secrets

Sensitive configuration is stored in environment variables.

Example:

```env
DATABASE_URL=...
SECRET_KEY=...
CENTRE_ADMIN_API_KEY=...
PAYMENT_WEBHOOK_SECRET=...
```

The actual `.env` file should not be committed to Git.

The repository contains `.env.example` with placeholder values.

---

# Database Migrations

Alembic is used for database schema migrations.

## Apply Migrations

```bash
alembic upgrade head
```

## Check Current Migration

```bash
alembic current
```

## View Migration History

```bash
alembic history
```

## Generate a Migration

After modifying SQLAlchemy models:

```bash
alembic revision --autogenerate -m "migration description"
```

The generated migration should be reviewed before applying it.

---

# Testing

Automated tests are implemented using Pytest and FastAPI's testing utilities.

Run the test suite with:

```bash
pytest -v
```

The test suite covers important functional and edge-case scenarios.

### Authentication

* Successful signup
* Duplicate signup
* Successful login
* Incorrect password
* Unknown email
* JWT authentication
* Invalid JWT

### Diagnostic Centres and Tests

* Diagnostic centre listing
* Centre/test listing
* Centres without matching tests

### Bookings

* Successful booking
* Invalid/non-existent test
* Invalid/non-existent centre
* Unauthenticated booking
* Booking validation

### Payments

* Successful payment
* Failed payment
* Invalid payment status
* Payment for a non-existent booking
* Payment for an already processed booking
* Payment ownership validation

### Webhooks

* Successful webhook
* Invalid payment ID
* Invalid payment status
* Invalid event type
* Booking state update
* Payment state update
* Duplicate webhook
* Webhook idempotency
* Multiple webhook events

---

# Running Tests

After configuring the database and environment:

```bash
pytest -v
```

A successful test run should report all implemented tests as passing.

---

# API Flow

The main application flow is:

```text
                    ┌───────────────┐
                    │     User      │
                    └───────┬───────┘
                            │
                            ▼
                     ┌────────────┐
                     │   Signup   │
                     └─────┬──────┘
                           │
                           ▼
                     ┌────────────┐
                     │   Login    │
                     └─────┬──────┘
                           │
                           ▼
                         JWT
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
       View Centres    View Tests    Create Booking
                                           │
                                           ▼
                                      PENDING
                                           │
                                           ▼
                                  Simulated Payment
                                     /          \
                                    /            \
                                   ▼              ▼
                              SUCCESS          FAILED
                                  │                │
                                  ▼                ▼
                              CONFIRMED          FAILED
```

The payment provider can additionally send status updates through:

```text
Payment Provider
       │
       ▼
POST /payments/webhook/
       │
       ▼
Validate Event
       │
       ▼
Check Idempotency
       │
       ▼
Lock Payment
       │
       ▼
Update Payment
       │
       ▼
Update Booking
       │
       ▼
Record Event
```

---

# Important Design Decisions

## 1. Why PostgreSQL?

PostgreSQL is well suited for this system because the application contains related entities such as users, centres, tests, bookings, payments, and webhook events.

Foreign keys and database constraints help maintain referential and transactional integrity.

---

## 2. Why Store Price in the Booking?

The centre-test price represents the current price.

The booking amount represents the price agreed upon when the booking was created.

Keeping the booking amount separately prevents historical bookings from changing if the current test price changes.

---

## 3. Why Store Webhook Events?

Payment providers can retry webhook events.

Without storing processed event IDs, the same event could potentially be processed multiple times.

The `webhook_events` table provides a persistent record of processed events and enables idempotent processing.

---

## 4. Why Use a Database Transaction for Webhooks?

A webhook may update multiple pieces of state:

```text
Payment
Booking
Webhook Event
```

These changes need to remain consistent.

Using a single database transaction ensures that either all related changes are committed or none of them are.

---

## 5. Why Use Row-Level Locking?

Two webhook requests could arrive at nearly the same time for the same payment.

Row-level locking ensures that concurrent requests cannot independently modify the same payment state at the same time.

---

# Assumptions

The following assumptions were made during implementation:

1. Payments are simulated and no real payment gateway is integrated.

2. Diagnostic centre and test data can be seeded directly into the PostgreSQL database.

3. Appointment slot availability management is outside the scope of this assignment.

4. Webhook events represent payment-provider status notifications.

5. Webhook `event_id` values are unique.

6. A failed payment may be retried; a confirmed booking cannot be charged again.

7. Payment attempts are represented separately from bookings.

8. The booking amount stores the price applicable at the time of booking.

---

# Edge Cases Handled

The implementation considers the following scenarios:

* Invalid signup data
* Duplicate user registration
* Invalid login credentials
* Missing/invalid JWT
* Invalid centre ID
* Invalid test ID
* Invalid booking ID
* Unauthorized access to another user's booking
* Invalid payment status
* Payment for an invalid booking
* Repeated payment processing
* Failed payments
* Invalid webhook events
* Invalid webhook payment IDs
* Repeated webhook events
* Concurrent webhook processing

The assignment specifically emphasizes invalid requests, repeated webhook events, invalid booking IDs, failed payments, and unauthorized resource modification.

---

# Future Improvements

If more development time were available, the following improvements could be considered:

* Redis caching
* Redis-based rate limiting
* Celery/background jobs
* Docker and Docker Compose
* Pagination
* Appointment slot management
* Real payment gateway integration
* Webhook secret rotation and key management
* Structured logging
* Monitoring and metrics
* More comprehensive integration tests
* Dedicated test database
* External-service retry handling
* More granular payment state transitions

These correspond to several of the optional engineering areas suggested by the assignment, including Redis, Celery, Docker, Swagger/OpenAPI, testing, structured logging, pagination, rate limiting, and webhook retry handling.

---

# Complete Local Workflow

```bash
# Clone repository
git clone <your-github-repository-url>
cd eve-health-assignment

# Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure .env

# Apply database migrations
alembic upgrade head

# Run tests
pytest -v

# Start development server
uvicorn app.main:app --reload
```

---

# API Documentation

Once the server is running, interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The OpenAPI schema can also be accessed through FastAPI's generated documentation endpoints.

---

# Submission Checklist

Before submitting the repository, verify that it contains:

```text
README.md
requirements.txt
Source code
Tests
Alembic migrations
.env.example
.gitignore
```

If Docker is used, also include:

```text
Dockerfile
docker-compose.yml
```

The assignment submission requirements explicitly call for the README, dependency file, source code, and tests, with Docker files required when Docker is used.

---

# Conclusion

This project implements a backend service for diagnostic test bookings and simulated payments with a focus on:

* Clean REST APIs
* JWT authentication
* Secure password storage
* Relational database design
* Booking lifecycle management
* Simulated payments
* Idempotent payment webhooks
* Transactional consistency
* Concurrent webhook protection
* Authorization
* Validation
* Automated testing
* Database migrations