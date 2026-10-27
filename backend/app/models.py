from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base
from .enums import (
    AcquisitionMode,
    DocType,
    Gender,
    KhataType,
    MutationStatus,
    MutationType,
    Season,
    UserRole,
)


class State(Base):
    __tablename__ = "state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(2), unique=True)
    name_hi: Mapped[str] = mapped_column(String(80))
    name_en: Mapped[str] = mapped_column(String(80))


class District(Base):
    __tablename__ = "district"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("state.id"))
    code: Mapped[str] = mapped_column(String(10))
    name_hi: Mapped[str] = mapped_column(String(80))
    name_en: Mapped[str] = mapped_column(String(80))


class Tehsil(Base):
    __tablename__ = "tehsil"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    district_id: Mapped[int] = mapped_column(ForeignKey("district.id"))
    code: Mapped[str] = mapped_column(String(10))
    name_hi: Mapped[str] = mapped_column(String(80))
    name_en: Mapped[str] = mapped_column(String(80))


class Village(Base):
    __tablename__ = "village"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tehsil_id: Mapped[int] = mapped_column(ForeignKey("tehsil.id"))
    code: Mapped[str] = mapped_column(String(10))
    name_hi: Mapped[str] = mapped_column(String(80))
    name_en: Mapped[str] = mapped_column(String(80))
    total_area_hectare: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))


class LandType(Base):
    __tablename__ = "land_type"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name_hi: Mapped[str] = mapped_column(String(50))
    name_en: Mapped[str] = mapped_column(String(50))


class Person(Base):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    aadhaar_hash: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    aadhaar_last4: Mapped[Optional[str]] = mapped_column(String(4))
    name_hi: Mapped[str] = mapped_column(String(120))
    name_en: Mapped[Optional[str]] = mapped_column(String(120))
    father_name_hi: Mapped[Optional[str]] = mapped_column(String(120))
    gender: Mapped[Gender] = mapped_column(SAEnum(Gender))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    mobile: Mapped[Optional[str]] = mapped_column(String(15))
    address_hi: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )


class Khasra(Base):
    __tablename__ = "khasra"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    village_id: Mapped[int] = mapped_column(ForeignKey("village.id"))
    khasra_no: Mapped[str] = mapped_column(String(20))
    area_hectare: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    land_type_id: Mapped[int] = mapped_column(ForeignKey("land_type.id"))
    soil_type: Mapped[Optional[str]] = mapped_column(String(50))
    irrigation_source: Mapped[Optional[str]] = mapped_column(String(50))
    boundary: Mapped[Optional[Any]] = mapped_column(JSON)
    is_disputed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Khata(Base):
    __tablename__ = "khata"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    village_id: Mapped[int] = mapped_column(ForeignKey("village.id"))
    khata_no: Mapped[str] = mapped_column(String(20))
    khata_type: Mapped[KhataType] = mapped_column(SAEnum(KhataType))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )


class Mutation(Base):
    __tablename__ = "mutation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    mutation_no: Mapped[str] = mapped_column(String(30), unique=True)
    khasra_id: Mapped[int] = mapped_column(ForeignKey("khasra.id"))
    from_person_id: Mapped[Optional[int]] = mapped_column(ForeignKey("person.id"))
    to_person_id: Mapped[int] = mapped_column(ForeignKey("person.id"))
    share_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    mutation_type: Mapped[MutationType] = mapped_column(SAEnum(MutationType))
    order_date: Mapped[date] = mapped_column(Date)
    status: Mapped[MutationStatus] = mapped_column(
        SAEnum(MutationStatus), default=MutationStatus.pending
    )
    remarks_hi: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )


class Ownership(Base):
    __tablename__ = "ownership"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    khasra_id: Mapped[int] = mapped_column(ForeignKey("khasra.id"))
    khata_id: Mapped[int] = mapped_column(ForeignKey("khata.id"))
    person_id: Mapped[int] = mapped_column(ForeignKey("person.id"))
    share_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    acquisition_mode: Mapped[AcquisitionMode] = mapped_column(SAEnum(AcquisitionMode))
    from_date: Mapped[date] = mapped_column(Date)
    to_date: Mapped[Optional[date]] = mapped_column(Date)
    source_mutation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("mutation.id")
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )


class Crop(Base):
    __tablename__ = "crop"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name_hi: Mapped[str] = mapped_column(String(50))
    name_en: Mapped[str] = mapped_column(String(50))


class CropCycle(Base):
    __tablename__ = "crop_cycle"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    khasra_id: Mapped[int] = mapped_column(ForeignKey("khasra.id"))
    crop_id: Mapped[int] = mapped_column(ForeignKey("crop.id"))
    season: Mapped[Season] = mapped_column(SAEnum(Season))
    crop_year: Mapped[int] = mapped_column(SmallInteger)
    sown_date: Mapped[Optional[date]] = mapped_column(Date)
    harvested_date: Mapped[Optional[date]] = mapped_column(Date)
    area_hectare: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    yield_quintal: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )


class AppUser(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name_hi: Mapped[str] = mapped_column(String(120))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole))
    village_id: Mapped[Optional[int]] = mapped_column(ForeignKey("village.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )


class LandDocument(Base):
    __tablename__ = "land_document"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    khasra_id: Mapped[int] = mapped_column(ForeignKey("khasra.id"))
    doc_type: Mapped[DocType] = mapped_column(SAEnum(DocType))
    file_name: Mapped[str] = mapped_column(String(255))
    file_uri: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("app_user.id"))
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    table_name: Mapped[str] = mapped_column(String(64))
    record_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(SAEnum("INSERT", "UPDATE", "DELETE"))
    old_value: Mapped[Optional[Any]] = mapped_column(JSON)
    new_value: Mapped[Optional[Any]] = mapped_column(JSON)
    changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )


class CurrentOwnershipView(Base):
    __tablename__ = "v_current_ownership"

    ownership_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    khasra_id: Mapped[int] = mapped_column(BigInteger)
    khasra_no: Mapped[str] = mapped_column(String(20))
    village_hi: Mapped[str] = mapped_column(String(80))
    tehsil_hi: Mapped[str] = mapped_column(String(80))
    district_hi: Mapped[str] = mapped_column(String(80))
    khata_id: Mapped[int] = mapped_column(BigInteger)
    khata_no: Mapped[str] = mapped_column(String(20))
    person_id: Mapped[int] = mapped_column(BigInteger)
    owner_hi: Mapped[str] = mapped_column(String(120))
    owner_en: Mapped[Optional[str]] = mapped_column(String(120))
    share_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    acquisition_mode: Mapped[str] = mapped_column(String(30))
    from_date: Mapped[date] = mapped_column(Date)


class KhasraSummaryView(Base):
    __tablename__ = "v_khasra_summary"

    khasra_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    village_id: Mapped[int] = mapped_column(Integer)
    khasra_no: Mapped[str] = mapped_column(String(20))
    village_hi: Mapped[str] = mapped_column(String(80))
    area_hectare: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    land_type_hi: Mapped[str] = mapped_column(String(50))
    is_disputed: Mapped[bool] = mapped_column(Boolean)
    allocated_share: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    owner_count: Mapped[int] = mapped_column(BigInteger)
