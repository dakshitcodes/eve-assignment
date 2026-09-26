from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DiagnosticCentre, CentreTest, DiagnosticTest

from app.schemas import CentreResponse, CentreTestResponse


router = APIRouter(
    prefix="/centres",
    tags=["Diagnostic Centres"]
)

@router.get("/", response_model=list[CentreResponse])
def get_centres(db: Session = Depends(get_db)):
    centres = db.query(DiagnosticCentre).all()

    return centres

@router.get(
    "/{centre_id}/tests",
    response_model=list[CentreTestResponse]
)
def get_centre_tests(
    centre_id: int,
    db: Session = Depends(get_db)
):
    centre_tests = (
        db.query(CentreTest, DiagnosticTest)
        .join(
            DiagnosticTest,
            CentreTest.test_id == DiagnosticTest.test_id
        )
        .filter(CentreTest.centre_id == centre_id)
        .all()
    )

    return [
        {
            "test_id": test.test_id,
            "test_name": test.test_name,
            "price": centre_test.test_price
        }
        for centre_test, test in centre_tests
    ]