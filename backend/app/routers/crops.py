from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..enums import Season
from ..models import Crop, CropCycle, Khasra
from ..schemas import CropCycleDetail, CropCycleOut, CropOut

router = APIRouter(prefix="/api", tags=["crops"])


@router.get("/crops", response_model=list[CropOut])
def list_crops(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Crop]:
    return list(db.scalars(select(Crop).order_by(Crop.name_hi)))


@router.get("/crop-cycles", response_model=list[CropCycleDetail])
def list_crop_cycles(
    khasra_id: Optional[int] = None,
    village_id: Optional[int] = None,
    season: Optional[Season] = None,
    crop_year: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[CropCycleDetail]:
    stmt = select(CropCycle, Crop.name_hi, Crop.name_en).join(
        Crop, Crop.id == CropCycle.crop_id
    )
    if khasra_id is not None:
        stmt = stmt.where(CropCycle.khasra_id == khasra_id)
    if village_id is not None:
        stmt = stmt.join(Khasra, Khasra.id == CropCycle.khasra_id).where(
            Khasra.village_id == village_id
        )
    if season is not None:
        stmt = stmt.where(CropCycle.season == season)
    if crop_year is not None:
        stmt = stmt.where(CropCycle.crop_year == crop_year)
    stmt = stmt.order_by(
        CropCycle.crop_year.desc(), CropCycle.season, CropCycle.id
    )
    stmt = stmt.limit(limit).offset(offset)

    result: list[CropCycleDetail] = []
    for cycle, name_hi, name_en in db.execute(stmt).all():
        data = CropCycleOut.model_validate(cycle).model_dump()
        result.append(
            CropCycleDetail(**data, crop_name_hi=name_hi, crop_name_en=name_en)
        )
    return result
