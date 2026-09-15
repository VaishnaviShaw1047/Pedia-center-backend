from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class ChildCreate(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    date_of_birth: date
    gender: str = Field(..., max_length=10)

    abha_id: Optional[str] = Field(None, pattern=r"^\d{14}$")
    aadhaar_number: Optional[str] = Field(None, pattern=r"^[2-9]\d{11}$")

    blood_group: Optional[str] = Field(None, max_length=3)
    known_allergies: Optional[str] = Field(None, max_length=255)
    existing_conditions: Optional[str] = Field(None, max_length=500)
    current_medications: Optional[str] = Field(None, max_length=255)
    immunization_status: Optional[str] = Field(None, max_length=15)
    referred_by: Optional[str] = Field(None, max_length=100)

    @field_validator("date_of_birth")
    @classmethod
    def check_paediatric_age(cls, value: date) -> date:
        today = date.today()
        if value > today:
            raise ValueError("Date of birth cannot be in the future")

        age = today.year - value.year
        if (today.month, today.day) < (value.month, value.day):
            age -= 1

        if age >= 18:
            raise ValueError("Patient must be under 18")
        return value


class GuardianCreate(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    relationship_to_child: str = Field(..., max_length=20)

    mobile_number: str = Field(..., pattern=r"^[6-9]\d{9}$")
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=8)

    address_line1: str = Field(..., max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    city: str = Field(..., max_length=50)
    state: str = Field(..., max_length=50)
    pincode: str = Field(..., pattern=r"^\d{6}$")

    preferred_language: Optional[str] = Field(None, max_length=20)

    terms_accepted: bool
    health_data_consent: bool

    children: list[ChildCreate] = Field(..., min_length=1)

    @field_validator("terms_accepted", "health_data_consent")
    @classmethod
    def must_be_accepted(cls, value: bool) -> bool:
        if not value:
            raise ValueError("This must be accepted to register")
        return value


class PatientOut(BaseModel):
    patient_id: int
    mrn: str
    first_name: str

    model_config = {"from_attributes": True}


class RegistrationResponse(BaseModel):
    guardian_id: int
    patients: list[PatientOut]
    message: str


class PatientListItem(BaseModel):
    patient_id: int
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    blood_group: Optional[str] = None
    guardian_name: str
    guardian_mobile: str

    model_config = {"from_attributes": True}


class PatientListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PatientListItem]


class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=10)
    abha_id: Optional[str] = Field(None, pattern=r"^\d{14}$")
    blood_group: Optional[str] = Field(None, max_length=3)
    known_allergies: Optional[str] = Field(None, max_length=255)
    existing_conditions: Optional[str] = Field(None, max_length=500)
    current_medications: Optional[str] = Field(None, max_length=255)
    immunization_status: Optional[str] = Field(None, max_length=15)
    referred_by: Optional[str] = Field(None, max_length=100)


class PatientDetail(BaseModel):
    patient_id: int
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    abha_id: Optional[str] = None
    blood_group: Optional[str] = None
    known_allergies: Optional[str] = None
    existing_conditions: Optional[str] = None
    current_medications: Optional[str] = None
    immunization_status: Optional[str] = None
    referred_by: Optional[str] = None

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    mobile_number: str = Field(..., pattern=r"^[6-9]\d{9}$")
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GuardianMe(BaseModel):
    guardian_id: int
    first_name: str
    last_name: str
    mobile_number: str
    role: str

    model_config = {"from_attributes": True}