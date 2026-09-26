from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.bookings import router as bookings_router
from app.routers.centres import router as centres_router
from app.routers.payments import router as payments_router
from app.routers.webhooks import router as webhooks_router


app = FastAPI(
    title="Eve Healthcare Backend API",
    description="Diagnostic test booking and simulated payment service",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(bookings_router)
app.include_router(centres_router)
app.include_router(payments_router)
app.include_router(webhooks_router)