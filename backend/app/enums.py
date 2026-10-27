from enum import Enum


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class KhataType(str, Enum):
    individual = "individual"
    joint = "joint"
    institutional = "institutional"


class MutationType(str, Enum):
    sale = "sale"
    inheritance = "inheritance"
    gift = "gift"
    partition = "partition"
    government_allotment = "government_allotment"
    correction = "correction"


class MutationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AcquisitionMode(str, Enum):
    sale = "sale"
    inheritance = "inheritance"
    gift = "gift"
    partition = "partition"
    government_allotment = "government_allotment"


class Season(str, Enum):
    kharif = "kharif"
    rabi = "rabi"
    zaid = "zaid"


class DocType(str, Enum):
    khasra_map = "khasra_map"
    jamabandi = "jamabandi"
    mutation_order = "mutation_order"
    sale_deed = "sale_deed"
    gift_deed = "gift_deed"
    other = "other"


class UserRole(str, Enum):
    admin = "admin"
    tehsildar = "tehsildar"
    patwari = "patwari"
    viewer = "viewer"
