from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import ADMIN_ROLES, db_error, get_current_user, get_or_404, require_roles
from ..models import Khasra, Khata, Ownership, Person
from ..schemas import OwnershipCreate, OwnershipOut

router = APIRouter(prefix="/api/ownership", tags=["ownership"])


@router.get("", response_model=list[OwnershipOut])
def list_ownership(
    khasra_id: Optional[int] = None,
    person_id: Optional[int] = None,
    khata_id: Optional[int] = None,
    current_only: bool = True,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Ownership]:
    stmt = select(Ownership)
    if khasra_id is not None:
        stmt = stmt.where(Ownership.khasra_id == khasra_id)
    if person_id is not None:
        stmt = stmt.where(Ownership.person_id == person_id)
    if khata_id is not None:
        stmt = stmt.where(Ownership.khata_id == khata_id)
    if current_only:
        stmt = stmt.where(Ownership.to_date.is_(None))
    stmt = stmt.order_by(Ownership.khasra_id, Ownership.from_date)
    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.get("/{ownership_id}", response_model=OwnershipOut)
def get_ownership(
    ownership_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> Ownership:
    return get_or_404(db, Ownership, ownership_id, "Ownership record")


@router.post("", response_model=OwnershipOut, status_code=201)
def create_ownership(
    payload: OwnershipCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*ADMIN_ROLES)),
) -> Ownership:
    khasra = get_or_404(db, Khasra, payload.khasra_id, "Khasra")
    khata = get_or_404(db, Khata, payload.khata_id, "Khata")
    get_or_404(db, Person, payload.person_id, "Person")

    if khata.village_id != khasra.village_id:
        raise HTTPException(
            status_code=400,
            detail="Khata and khasra must belong to the same village",
        )

    ownership = Ownership(**payload.model_dump())
    db.add(ownership)
    try:
        db.commit()
    except DBAPIError as exc:
        db.rollback()
        raise db_error(exc) from None
    db.refresh(ownership)
    return ownership
