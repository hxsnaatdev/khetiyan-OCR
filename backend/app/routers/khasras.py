from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import EDITOR_ROLES, get_current_user, get_or_404, require_roles
from ..models import (
    Crop,
    CropCycle,
    CurrentOwnershipView,
    Khasra,
    LandDocument,
    LandType,
    Village,
)
from ..schemas import (
    CropCycleCreate,
    CropCycleDetail,
    CropCycleOut,
    CurrentOwnershipOut,
    KhasraCreate,
    KhasraOut,
    KhasraUpdate,
    LandDocumentCreate,
    LandDocumentOut,
)

router = APIRouter(prefix="/api/khasras", tags=["khasras"])


@router.get("", response_model=list[KhasraOut])
def list_khasras(
    village_id: Optional[int] = None,
    land_type_id: Optional[int] = None,
    disputed: Optional[bool] = None,
    q: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Khasra]:
    stmt = select(Khasra)
    if village_id is not None:
        stmt = stmt.where(Khasra.village_id == village_id)
    if land_type_id is not None:
        stmt = stmt.where(Khasra.land_type_id == land_type_id)
    if disputed is not None:
        stmt = stmt.where(Khasra.is_disputed == disputed)
    if q:
        stmt = stmt.where(Khasra.khasra_no.like(f"%{q}%"))
    stmt = stmt.order_by(Khasra.khasra_no).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.post("", response_model=KhasraOut, status_code=201)
def create_khasra(
    payload: KhasraCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*EDITOR_ROLES)),
) -> Khasra:
    get_or_404(db, Village, payload.village_id, "Village")
    get_or_404(db, LandType, payload.land_type_id, "Land type")

    khasra = Khasra(**payload.model_dump())
    db.add(khasra)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This khasra number already exists in the village",
        ) from None
    db.refresh(khasra)
    return khasra


@router.get("/{khasra_id}", response_model=KhasraOut)
def get_khasra(
    khasra_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> Khasra:
    return get_or_404(db, Khasra, khasra_id, "Khasra")


@router.patch("/{khasra_id}", response_model=KhasraOut)
def update_khasra(
    khasra_id: int,
    payload: KhasraUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*EDITOR_ROLES)),
) -> Khasra:
    khasra = get_or_404(db, Khasra, khasra_id, "Khasra")
    data = payload.model_dump(exclude_unset=True)

    if "land_type_id" in data:
        get_or_404(db, LandType, data["land_type_id"], "Land type")

    for field, value in data.items():
        setattr(khasra, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This khasra number already exists in the village",
        ) from None
    db.refresh(khasra)
    return khasra


@router.get("/{khasra_id}/owners", response_model=list[CurrentOwnershipOut])
def khasra_owners(
    khasra_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[CurrentOwnershipView]:
    get_or_404(db, Khasra, khasra_id, "Khasra")
    stmt = (
        select(CurrentOwnershipView)
        .where(CurrentOwnershipView.khasra_id == khasra_id)
        .order_by(CurrentOwnershipView.share_percentage.desc())
    )
    return list(db.scalars(stmt))


@router.get("/{khasra_id}/crops", response_model=list[CropCycleDetail])
def khasra_crops(
    khasra_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[CropCycleDetail]:
    get_or_404(db, Khasra, khasra_id, "Khasra")
    rows = db.execute(
        select(CropCycle, Crop.name_hi, Crop.name_en)
        .join(Crop, Crop.id == CropCycle.crop_id)
        .where(CropCycle.khasra_id == khasra_id)
        .order_by(CropCycle.crop_year.desc(), CropCycle.season)
    ).all()

    result: list[CropCycleDetail] = []
    for cycle, name_hi, name_en in rows:
        data = CropCycleOut.model_validate(cycle).model_dump()
        result.append(
            CropCycleDetail(
                **data, crop_name_hi=name_hi, crop_name_en=name_en
            )
        )
    return result


@router.post("/{khasra_id}/crops", response_model=CropCycleOut, status_code=201)
def create_crop_cycle(
    khasra_id: int,
    payload: CropCycleCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*EDITOR_ROLES)),
) -> CropCycle:
    get_or_404(db, Khasra, khasra_id, "Khasra")
    get_or_404(db, Crop, payload.crop_id, "Crop")

    cycle = CropCycle(khasra_id=khasra_id, **payload.model_dump())
    db.add(cycle)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A crop cycle for this crop, season and year already exists",
        ) from None
    db.refresh(cycle)
    return cycle


@router.get("/{khasra_id}/documents", response_model=list[LandDocumentOut])
def list_documents(
    khasra_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[LandDocument]:
    get_or_404(db, Khasra, khasra_id, "Khasra")
    stmt = (
        select(LandDocument)
        .where(LandDocument.khasra_id == khasra_id)
        .order_by(LandDocument.uploaded_at.desc())
    )
    return list(db.scalars(stmt))


@router.post(
    "/{khasra_id}/documents", response_model=LandDocumentOut, status_code=201
)
def add_document(
    khasra_id: int,
    payload: LandDocumentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*EDITOR_ROLES)),
) -> LandDocument:
    get_or_404(db, Khasra, khasra_id, "Khasra")
    document = LandDocument(
        khasra_id=khasra_id,
        uploaded_by=user.id,
        **payload.model_dump(),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document
