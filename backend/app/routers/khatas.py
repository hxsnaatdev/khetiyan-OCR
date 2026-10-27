from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import EDITOR_ROLES, get_current_user, get_or_404, require_roles
from ..models import KhasraSummaryView, Khata, Ownership, Village
from ..schemas import KhasraSummaryOut, KhataCreate, KhataOut

router = APIRouter(prefix="/api/khatas", tags=["khatas"])


@router.get("", response_model=list[KhataOut])
def list_khatas(
    village_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Khata]:
    stmt = select(Khata).order_by(Khata.khata_no)
    if village_id is not None:
        stmt = stmt.where(Khata.village_id == village_id)
    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.post("", response_model=KhataOut, status_code=201)
def create_khata(
    payload: KhataCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*EDITOR_ROLES)),
) -> Khata:
    get_or_404(db, Village, payload.village_id, "Village")
    khata = Khata(**payload.model_dump())
    db.add(khata)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This khata number already exists in the village",
        ) from None
    db.refresh(khata)
    return khata


@router.get("/{khata_id}", response_model=KhataOut)
def get_khata(
    khata_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> Khata:
    return get_or_404(db, Khata, khata_id, "Khata")


@router.get("/{khata_id}/khasras", response_model=list[KhasraSummaryOut])
def khata_khasras(
    khata_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[KhasraSummaryView]:
    get_or_404(db, Khata, khata_id, "Khata")
    stmt = (
        select(KhasraSummaryView)
        .join(
            Ownership,
            Ownership.khasra_id == KhasraSummaryView.khasra_id,
        )
        .where(Ownership.khata_id == khata_id, Ownership.to_date.is_(None))
        .distinct()
        .order_by(KhasraSummaryView.khasra_no)
    )
    return list(db.scalars(stmt))
