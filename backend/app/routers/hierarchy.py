from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import EDITOR_ROLES, get_current_user, get_or_404, require_roles
from ..models import District, LandType, State, Tehsil, Village
from ..schemas import (
    DistrictOut,
    LandTypeOut,
    StateOut,
    TehsilOut,
    VillageCreate,
    VillageOut,
)

router = APIRouter(prefix="/api", tags=["hierarchy"])


@router.get("/states", response_model=list[StateOut])
def list_states(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[State]:
    return list(db.scalars(select(State).order_by(State.name_hi)))


@router.get("/districts", response_model=list[DistrictOut])
def list_districts(
    state_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[District]:
    stmt = select(District).order_by(District.name_hi)
    if state_id is not None:
        stmt = stmt.where(District.state_id == state_id)
    return list(db.scalars(stmt))


@router.get("/tehsils", response_model=list[TehsilOut])
def list_tehsils(
    district_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Tehsil]:
    stmt = select(Tehsil).order_by(Tehsil.name_hi)
    if district_id is not None:
        stmt = stmt.where(Tehsil.district_id == district_id)
    return list(db.scalars(stmt))


@router.get("/villages", response_model=list[VillageOut])
def list_villages(
    tehsil_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Village]:
    stmt = select(Village).order_by(Village.name_hi)
    if tehsil_id is not None:
        stmt = stmt.where(Village.tehsil_id == tehsil_id)
    return list(db.scalars(stmt))


@router.post("/villages", response_model=VillageOut, status_code=201)
def create_village(
    payload: VillageCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*EDITOR_ROLES)),
) -> Village:
    get_or_404(db, Tehsil, payload.tehsil_id, "Tehsil")
    village = Village(**payload.model_dump())
    db.add(village)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Village code already exists"
        ) from None
    db.refresh(village)
    return village


@router.get("/land-types", response_model=list[LandTypeOut])
def list_land_types(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[LandType]:
    return list(db.scalars(select(LandType).order_by(LandType.name_hi)))
