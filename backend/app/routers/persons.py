from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import EDITOR_ROLES, get_current_user, get_or_404, require_roles
from ..models import CurrentOwnershipView, Khasra, Ownership, Person
from ..schemas import CurrentOwnershipOut, PersonCreate, PersonOut, PersonUpdate
from ..security import hash_aadhaar

router = APIRouter(prefix="/api/persons", tags=["persons"])


@router.get("", response_model=list[PersonOut])
def list_persons(
    q: Optional[str] = None,
    village_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Person]:
    stmt = select(Person)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(Person.name_hi.like(pattern), Person.name_en.like(pattern))
        )
    if village_id is not None:
        stmt = (
            stmt.join(Ownership, Ownership.person_id == Person.id)
            .join(Khasra, Khasra.id == Ownership.khasra_id)
            .where(Khasra.village_id == village_id)
            .distinct()
        )
    stmt = stmt.order_by(Person.name_hi).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.post("", response_model=PersonOut, status_code=201)
def create_person(
    payload: PersonCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*EDITOR_ROLES)),
) -> Person:
    data = payload.model_dump()
    aadhaar = data.pop("aadhaar", None)
    if aadhaar:
        data["aadhaar_hash"] = hash_aadhaar(aadhaar)
        data["aadhaar_last4"] = aadhaar[-4:]

    person = Person(**data)
    db.add(person)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Aadhaar is already registered"
        ) from None
    db.refresh(person)
    return person


@router.get("/{person_id}", response_model=PersonOut)
def get_person(
    person_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> Person:
    return get_or_404(db, Person, person_id, "Person")


@router.patch("/{person_id}", response_model=PersonOut)
def update_person(
    person_id: int,
    payload: PersonUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*EDITOR_ROLES)),
) -> Person:
    person = get_or_404(db, Person, person_id, "Person")
    data = payload.model_dump(exclude_unset=True)

    if "aadhaar" in data:
        aadhaar = data.pop("aadhaar")
        if aadhaar:
            data["aadhaar_hash"] = hash_aadhaar(aadhaar)
            data["aadhaar_last4"] = aadhaar[-4:]
        else:
            data["aadhaar_hash"] = None
            data["aadhaar_last4"] = None

    for field, value in data.items():
        setattr(person, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Aadhaar is already registered"
        ) from None
    db.refresh(person)
    return person


@router.get("/{person_id}/lands", response_model=list[CurrentOwnershipOut])
def person_lands(
    person_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[CurrentOwnershipView]:
    get_or_404(db, Person, person_id, "Person")
    stmt = (
        select(CurrentOwnershipView)
        .where(CurrentOwnershipView.person_id == person_id)
        .order_by(CurrentOwnershipView.khasra_no)
    )
    return list(db.scalars(stmt))
