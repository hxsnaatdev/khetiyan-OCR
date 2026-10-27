from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

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


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class UserOut(ORMModel):
    id: int
    username: str
    full_name_hi: str
    role: UserRole
    village_id: Optional[int] = None
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class StateOut(ORMModel):
    id: int
    code: str
    name_hi: str
    name_en: str


class DistrictOut(ORMModel):
    id: int
    state_id: int
    code: str
    name_hi: str
    name_en: str


class TehsilOut(ORMModel):
    id: int
    district_id: int
    code: str
    name_hi: str
    name_en: str


class VillageOut(ORMModel):
    id: int
    tehsil_id: int
    code: str
    name_hi: str
    name_en: str
    total_area_hectare: Optional[float] = None


class VillageCreate(BaseModel):
    tehsil_id: int
    code: str = Field(max_length=10)
    name_hi: str = Field(min_length=1, max_length=80)
    name_en: str = Field(min_length=1, max_length=80)
    total_area_hectare: Optional[float] = Field(default=None, ge=0)


class LandTypeOut(ORMModel):
    id: int
    code: str
    name_hi: str
    name_en: str


class PersonCreate(BaseModel):
    aadhaar: Optional[str] = Field(default=None, pattern=r"^\d{12}$")
    name_hi: str = Field(min_length=1, max_length=120)
    name_en: Optional[str] = Field(default=None, max_length=120)
    father_name_hi: Optional[str] = Field(default=None, max_length=120)
    gender: Gender = Gender.other
    date_of_birth: Optional[date] = None
    mobile: Optional[str] = Field(default=None, pattern=r"^[0-9+\-]{6,15}$")
    address_hi: Optional[str] = Field(default=None, max_length=255)


class PersonUpdate(BaseModel):
    aadhaar: Optional[str] = Field(default=None, pattern=r"^\d{12}$")
    name_hi: Optional[str] = Field(default=None, min_length=1, max_length=120)
    name_en: Optional[str] = Field(default=None, max_length=120)
    father_name_hi: Optional[str] = Field(default=None, max_length=120)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    mobile: Optional[str] = Field(default=None, pattern=r"^[0-9+\-]{6,15}$")
    address_hi: Optional[str] = Field(default=None, max_length=255)


class PersonOut(ORMModel):
    id: int
    aadhaar_last4: Optional[str] = None
    name_hi: str
    name_en: Optional[str] = None
    father_name_hi: Optional[str] = None
    gender: Gender
    date_of_birth: Optional[date] = None
    mobile: Optional[str] = None
    address_hi: Optional[str] = None
    created_at: Optional[datetime] = None


class KhasraCreate(BaseModel):
    village_id: int
    khasra_no: str = Field(min_length=1, max_length=20)
    area_hectare: float = Field(gt=0)
    land_type_id: int
    soil_type: Optional[str] = Field(default=None, max_length=50)
    irrigation_source: Optional[str] = Field(default=None, max_length=50)
    boundary: Optional[Any] = None
    is_disputed: bool = False


class KhasraUpdate(BaseModel):
    khasra_no: Optional[str] = Field(default=None, min_length=1, max_length=20)
    area_hectare: Optional[float] = Field(default=None, gt=0)
    land_type_id: Optional[int] = None
    soil_type: Optional[str] = Field(default=None, max_length=50)
    irrigation_source: Optional[str] = Field(default=None, max_length=50)
    boundary: Optional[Any] = None
    is_disputed: Optional[bool] = None


class KhasraOut(ORMModel):
    id: int
    village_id: int
    khasra_no: str
    area_hectare: float
    land_type_id: int
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = None
    boundary: Optional[Any] = None
    is_disputed: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class KhataCreate(BaseModel):
    village_id: int
    khata_no: str = Field(min_length=1, max_length=20)
    khata_type: KhataType = KhataType.individual


class KhataOut(ORMModel):
    id: int
    village_id: int
    khata_no: str
    khata_type: KhataType
    created_at: Optional[datetime] = None


class OwnershipCreate(BaseModel):
    khasra_id: int
    khata_id: int
    person_id: int
    share_percentage: float = Field(gt=0, le=100)
    acquisition_mode: AcquisitionMode
    from_date: date
    to_date: Optional[date] = None


class OwnershipOut(ORMModel):
    id: int
    khasra_id: int
    khata_id: int
    person_id: int
    share_percentage: float
    acquisition_mode: AcquisitionMode
    from_date: date
    to_date: Optional[date] = None
    source_mutation_id: Optional[int] = None


class MutationCreate(BaseModel):
    mutation_no: Optional[str] = Field(default=None, max_length=30)
    khasra_id: int
    from_person_id: Optional[int] = None
    to_person_id: int
    share_percentage: float = Field(gt=0, le=100)
    mutation_type: MutationType
    order_date: date
    remarks_hi: Optional[str] = Field(default=None, max_length=255)


class MutationOut(ORMModel):
    id: int
    mutation_no: str
    khasra_id: int
    from_person_id: Optional[int] = None
    to_person_id: int
    share_percentage: float
    mutation_type: MutationType
    order_date: date
    status: MutationStatus
    remarks_hi: Optional[str] = None
    created_at: Optional[datetime] = None


class MutationReject(BaseModel):
    remarks_hi: Optional[str] = Field(default=None, max_length=255)


class CurrentOwnershipOut(ORMModel):
    ownership_id: int
    khasra_id: int
    khasra_no: str
    village_hi: str
    tehsil_hi: str
    district_hi: str
    khata_id: int
    khata_no: str
    person_id: int
    owner_hi: str
    owner_en: Optional[str] = None
    share_percentage: float
    acquisition_mode: str
    from_date: date


class KhasraSummaryOut(ORMModel):
    khasra_id: int
    village_id: int
    khasra_no: str
    village_hi: str
    area_hectare: float
    land_type_hi: str
    is_disputed: bool
    allocated_share: float
    owner_count: int


class CropOut(ORMModel):
    id: int
    code: str
    name_hi: str
    name_en: str


class CropCycleCreate(BaseModel):
    crop_id: int
    season: Season
    crop_year: int = Field(ge=1900, le=2100)
    sown_date: Optional[date] = None
    harvested_date: Optional[date] = None
    area_hectare: Optional[float] = Field(default=None, gt=0)
    yield_quintal: Optional[float] = Field(default=None, ge=0)


class CropCycleOut(ORMModel):
    id: int
    khasra_id: int
    crop_id: int
    season: Season
    crop_year: int
    sown_date: Optional[date] = None
    harvested_date: Optional[date] = None
    area_hectare: Optional[float] = None
    yield_quintal: Optional[float] = None


class CropCycleDetail(CropCycleOut):
    crop_name_hi: str
    crop_name_en: str


class LandDocumentOut(ORMModel):
    id: int
    khasra_id: int
    doc_type: DocType
    file_name: str
    file_uri: str
    uploaded_by: int
    uploaded_at: Optional[datetime] = None


class LandDocumentCreate(BaseModel):
    doc_type: DocType
    file_name: str = Field(min_length=1, max_length=255)
    file_uri: str = Field(min_length=1, max_length=500)


class VillageLandRow(BaseModel):
    land_type_hi: str
    land_type_en: str
    khasra_count: int
    total_area_hectare: float


class DashboardOut(BaseModel):
    villages: int
    khasras: int
    persons: int
    pending_mutations: int
    disputed_khasras: int
    total_area_hectare: float
