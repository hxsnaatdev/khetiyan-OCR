from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_or_404
from ..enums import MutationStatus
from ..models import (
    Khasra,
    KhasraSummaryView,
    LandType,
    Mutation,
    Person,
    Village,
)
from ..schemas import DashboardOut, KhasraSummaryOut, VillageLandRow

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> DashboardOut:
    villages = db.scalar(select(func.count()).select_from(Village)) or 0
    khasras = db.scalar(select(func.count()).select_from(Khasra)) or 0
    persons = db.scalar(select(func.count()).select_from(Person)) or 0
    pending = (
        db.scalar(
            select(func.count())
            .select_from(Mutation)
            .where(Mutation.status == MutationStatus.pending)
        )
        or 0
    )
    disputed = (
        db.scalar(
            select(func.count())
            .select_from(Khasra)
            .where(Khasra.is_disputed.is_(True))
        )
        or 0
    )
    total_area = db.scalar(select(func.coalesce(func.sum(Khasra.area_hectare), 0)))

    return DashboardOut(
        villages=int(villages),
        khasras=int(khasras),
        persons=int(persons),
        pending_mutations=int(pending),
        disputed_khasras=int(disputed),
        total_area_hectare=float(total_area or 0),
    )


@router.get("/villages/{village_id}/land", response_model=list[VillageLandRow])
def village_land(
    village_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[VillageLandRow]:
    get_or_404(db, Village, village_id, "Village")
    rows = db.execute(
        select(
            LandType.name_hi,
            LandType.name_en,
            func.count(Khasra.id),
            func.coalesce(func.sum(Khasra.area_hectare), 0),
        )
        .join(Khasra, Khasra.land_type_id == LandType.id)
        .where(Khasra.village_id == village_id)
        .group_by(LandType.id, LandType.name_hi, LandType.name_en)
        .order_by(LandType.name_hi)
    ).all()

    return [
        VillageLandRow(
            land_type_hi=name_hi,
            land_type_en=name_en,
            khasra_count=int(count),
            total_area_hectare=float(area),
        )
        for name_hi, name_en, count, area in rows
    ]


@router.get("/khasra-summary", response_model=list[KhasraSummaryOut])
def khasra_summary(
    village_id: Optional[int] = None,
    disputed: Optional[bool] = None,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[KhasraSummaryView]:
    stmt = select(KhasraSummaryView)
    if village_id is not None:
        get_or_404(db, Village, village_id, "Village")
        stmt = stmt.where(KhasraSummaryView.village_id == village_id)
    if disputed is not None:
        stmt = stmt.where(KhasraSummaryView.is_disputed == disputed)
    stmt = stmt.order_by(KhasraSummaryView.village_hi, KhasraSummaryView.khasra_no)
    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt))
