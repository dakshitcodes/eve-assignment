from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_centre_admin
from app.models import Booking, CentreTest, DiagnosticCentre, DiagnosticTest
from app.schemas import (
    CentreCreateRequest,
    CentreResponse,
    CentreTestCreateRequest,
    CentreTestResponse,
    CentreTestUpdateRequest,
    CentreUpdateRequest,
)


router = APIRouter(
    prefix="/centres",
    tags=["Diagnostic Centres"]
)

@router.get("/", response_model=list[CentreResponse])
def get_centres(db: Session = Depends(get_db)):
    centres = db.query(DiagnosticCentre).all()

    return centres


@router.post(
    "/",
    response_model=CentreResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_centre(
    centre_data: CentreCreateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_centre_admin),
):
    centre = DiagnosticCentre(**centre_data.model_dump())
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


@router.patch(
    "/{centre_id}",
    response_model=CentreResponse,
)
def update_centre(
    centre_id: int,
    centre_data: CentreUpdateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_centre_admin),
):
    centre = db.query(DiagnosticCentre).filter(
        DiagnosticCentre.centre_id == centre_id
    ).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    for field, value in centre_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(centre, field, value)

    db.commit()
    db.refresh(centre)
    return centre


@router.delete("/{centre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_centre(
    centre_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_centre_admin),
):
    centre = db.query(DiagnosticCentre).filter(
        DiagnosticCentre.centre_id == centre_id
    ).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    has_bookings = db.query(Booking.booking_id).filter(
        Booking.centre_id == centre_id
    ).first()
    if has_bookings:
        raise HTTPException(
            status_code=409,
            detail="Centre has bookings and cannot be deleted",
        )

    db.query(CentreTest).filter(
        CentreTest.centre_id == centre_id
    ).delete(synchronize_session=False)
    db.delete(centre)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.post(
    "/{centre_id}/tests",
    response_model=CentreTestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_centre_test(
    centre_id: int,
    test_data: CentreTestCreateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_centre_admin),
):
    centre = db.query(DiagnosticCentre).filter(
        DiagnosticCentre.centre_id == centre_id
    ).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    test = db.query(DiagnosticTest).filter(
        DiagnosticTest.test_name == test_data.test_name
    ).first()
    if test:
        existing_offer = db.query(CentreTest).filter(
            CentreTest.centre_id == centre_id,
            CentreTest.test_id == test.test_id,
        ).first()
        if existing_offer:
            raise HTTPException(
                status_code=409,
                detail="Test is already offered at this centre",
            )
    else:
        test = DiagnosticTest(test_name=test_data.test_name)
        db.add(test)
        db.flush()

    offer = CentreTest(
        centre_id=centre_id,
        test_id=test.test_id,
        test_price=test_data.price,
    )
    db.add(offer)
    db.commit()
    return {
        "test_id": test.test_id,
        "test_name": test.test_name,
        "price": offer.test_price,
    }


@router.patch(
    "/{centre_id}/tests/{test_id}",
    response_model=CentreTestResponse,
)
def update_centre_test(
    centre_id: int,
    test_id: int,
    test_data: CentreTestUpdateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_centre_admin),
):
    offer = db.query(CentreTest).filter(
        CentreTest.centre_id == centre_id,
        CentreTest.test_id == test_id,
    ).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Centre test not found")

    test = db.query(DiagnosticTest).filter(
        DiagnosticTest.test_id == test_id
    ).first()
    if test_data.test_name is not None:
        test.test_name = test_data.test_name
    if test_data.price is not None:
        offer.test_price = test_data.price

    db.commit()
    return {
        "test_id": test.test_id,
        "test_name": test.test_name,
        "price": offer.test_price,
    }


@router.delete(
    "/{centre_id}/tests/{test_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_centre_test(
    centre_id: int,
    test_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_centre_admin),
):
    offer = db.query(CentreTest).filter(
        CentreTest.centre_id == centre_id,
        CentreTest.test_id == test_id,
    ).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Centre test not found")

    db.delete(offer)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)