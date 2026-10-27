import secrets
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import (
    EDITOR_ROLES,
    MANAGER_ROLES,
    db_error,
    get_current_user,
    get_or_404,
    require_roles,
)
from ..enums import AcquisitionMode, MutationStatus, MutationType
from ..models import Khasra, Mutation, Ownership, Person
from ..schemas import MutationCreate, MutationOut, MutationReject

router = APIRouter(prefix="/api/mutations", tags=["mutations"])


def _available_share(db: Session, khasra_id: int, person_id: int) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(Ownership.share_percentage), 0)).where(
            Ownership.khasra_id == khasra_id,
            Ownership.person_id == person_id,
            Ownership.to_date.is_(None),
        )
    )
    return Decimal(total)


@router.get("", response_model=list[MutationOut])
def list_mutations(
    status: Optional[MutationStatus] = None,
    khasra_id: Optional[int] = None,
    person_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Mutation]:
    stmt = select(Mutation)
    if status is not None:
        stmt = stmt.where(Mutation.status == status)
    if khasra_id is not None:
        stmt = stmt.where(Mutation.khasra_id == khasra_id)
    if person_id is not None:
        stmt = stmt.where(
            (Mutation.from_person_id == person_id)
            | (Mutation.to_person_id == person_id)
        )
    stmt = stmt.order_by(Mutation.order_date.desc(), Mutation.id.desc())
    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.get("/{mutation_id}", response_model=MutationOut)
def get_mutation(
    mutation_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> Mutation:
    return get_or_404(db, Mutation, mutation_id, "Mutation")


@router.post("", response_model=MutationOut, status_code=201)
def create_mutation(
    payload: MutationCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*EDITOR_ROLES)),
) -> Mutation:
    get_or_404(db, Khasra, payload.khasra_id, "Khasra")
    get_or_404(db, Person, payload.to_person_id, "Person")

    if payload.mutation_type == MutationType.correction:
        if payload.from_person_id is not None:
            get_or_404(db, Person, payload.from_person_id, "Person")
    else:
        if payload.from_person_id is None:
            raise HTTPException(
                status_code=422,
                detail="from_person_id is required for this mutation type",
            )
        get_or_404(db, Person, payload.from_person_id, "Person")
        if payload.from_person_id == payload.to_person_id:
            raise HTTPException(
                status_code=400,
                detail="from_person_id and to_person_id must be different",
            )
        available = _available_share(
            db, payload.khasra_id, payload.from_person_id
        )
        if available < Decimal(str(payload.share_percentage)):
            raise HTTPException(
                status_code=400,
                detail=f"Person only holds {available}% of this khasra",
            )

    mutation_no = payload.mutation_no or (
        f"MUT-{datetime.now():%Y%m%d}-{secrets.token_hex(3).upper()}"
    )
    data = payload.model_dump(exclude={"mutation_no"})
    mutation = Mutation(mutation_no=mutation_no, **data)
    db.add(mutation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Mutation number already exists"
        ) from None
    db.refresh(mutation)
    return mutation


@router.post("/{mutation_id}/approve", response_model=MutationOut)
def approve_mutation(
    mutation_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*MANAGER_ROLES)),
) -> Mutation:
    mutation = db.scalar(
        select(Mutation)
        .where(Mutation.id == mutation_id)
        .with_for_update()
    )
    if mutation is None:
        raise HTTPException(status_code=404, detail="Mutation not found")
    if mutation.status != MutationStatus.pending:
        raise HTTPException(
            status_code=409, detail="Only pending mutations can be approved"
        )

    get_or_404(db, Khasra, mutation.khasra_id, "Khasra")
    to_person = get_or_404(db, Person, mutation.to_person_id, "Person")

    if mutation.mutation_type == MutationType.correction:
        mutation.status = MutationStatus.approved
        db.commit()
        db.refresh(mutation)
        return mutation

    if mutation.from_person_id is None:
        raise HTTPException(
            status_code=422,
            detail="from_person_id is required to approve this mutation",
        )
    from_person = get_or_404(db, Person, mutation.from_person_id, "Person")
    if from_person.id == to_person.id:
        raise HTTPException(
            status_code=400, detail="Cannot transfer land to the same person"
        )

    share = Decimal(mutation.share_percentage)
    rows = list(
        db.scalars(
            select(Ownership)
            .where(
                Ownership.khasra_id == mutation.khasra_id,
                Ownership.person_id == mutation.from_person_id,
                Ownership.to_date.is_(None),
            )
            .order_by(Ownership.from_date, Ownership.id)
            .with_for_update()
        )
    )
    available = sum((Decimal(row.share_percentage) for row in rows), Decimal(0))
    if available < share:
        raise HTTPException(
            status_code=400,
            detail=f"Person only holds {available}% of this khasra",
        )

    remaining = share
    allocation = []
    for row in rows:
        if remaining <= 0:
            break
        take = min(Decimal(row.share_percentage), remaining)
        retention = Decimal(row.share_percentage) - take
        row.to_date = mutation.order_date
        allocation.append(
            {
                "khata_id": row.khata_id,
                "share": take,
                "retention": retention,
                "acquisition_mode": row.acquisition_mode,
                "source_mutation_id": row.source_mutation_id,
            }
        )
        remaining -= take

    db.flush()

    for item in allocation:
        if item["retention"] > 0:
            db.add(
                Ownership(
                    khasra_id=mutation.khasra_id,
                    khata_id=item["khata_id"],
                    person_id=from_person.id,
                    share_percentage=item["retention"],
                    acquisition_mode=item["acquisition_mode"],
                    from_date=mutation.order_date,
                    to_date=None,
                    source_mutation_id=item["source_mutation_id"],
                )
            )
    db.flush()

    mode = AcquisitionMode(mutation.mutation_type.value)
    for item in allocation:
        db.add(
            Ownership(
                khasra_id=mutation.khasra_id,
                khata_id=item["khata_id"],
                person_id=to_person.id,
                share_percentage=item["share"],
                acquisition_mode=mode,
                from_date=mutation.order_date,
                to_date=None,
                source_mutation_id=mutation.id,
            )
        )
    db.flush()

    mutation.status = MutationStatus.approved
    try:
        db.commit()
    except DBAPIError as exc:
        db.rollback()
        raise db_error(exc) from None
    db.refresh(mutation)
    return mutation


@router.post("/{mutation_id}/reject", response_model=MutationOut)
def reject_mutation(
    mutation_id: int,
    payload: Optional[MutationReject] = None,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*MANAGER_ROLES)),
) -> Mutation:
    mutation = db.scalar(
        select(Mutation)
        .where(Mutation.id == mutation_id)
        .with_for_update()
    )
    if mutation is None:
        raise HTTPException(status_code=404, detail="Mutation not found")
    if mutation.status != MutationStatus.pending:
        raise HTTPException(
            status_code=409, detail="Only pending mutations can be rejected"
        )

    mutation.status = MutationStatus.rejected
    if payload is not None and payload.remarks_hi:
        mutation.remarks_hi = payload.remarks_hi
    db.commit()
    db.refresh(mutation)
    return mutation
