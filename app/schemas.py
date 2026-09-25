from datetime import date, datetime, time
from typing import Optional


from pydantic import BaseModel, EmailStr, Field, field_validator


class ChildCreateRequest(BaseModel):
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


class RegistrationRequest(BaseModel):
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

    children: list[ChildCreateRequest] = Field(..., min_length=1)

    @field_validator("terms_accepted", "health_data_consent")
    @classmethod
    def must_be_accepted(cls, value: bool) -> bool:
        if not value:
            raise ValueError("This must be accepted to register")
        return value


class RegisteredPatientResponse(BaseModel):
    patient_id: int
    mrn: str
    first_name: str

    model_config = {"from_attributes": True}


class RegistrationResponse(BaseModel):
    guardian_id: int
    patients: list[RegisteredPatientResponse]
    message: str


class PatientSummaryResponse(BaseModel):
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
    items: list[PatientSummaryResponse]


class PatientUpdateRequest(BaseModel):
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


class PatientDetailResponse(BaseModel):
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


class GuardianLoginRequest(BaseModel):
    mobile_number: str = Field(..., pattern=r"^[6-9]\d{9}$")
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GuardianProfileResponse(BaseModel):
    guardian_id: int
    first_name: str
    last_name: str
    mobile_number: str
    role: str

    model_config = {"from_attributes": True}

class DoctorCreateRequest(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    registration_no: str = Field(..., max_length=30)
    qualification: str = Field(..., max_length=150)
    specialty: str = Field(..., max_length=60)
    experience_years: int = Field(0, ge=0, le=70)
    languages: Optional[str] = Field(None, max_length=100)
    consultation_fee: int = Field(..., ge=0)
    available_days: Optional[str] = Field(None, max_length=60)
    mobile_number: Optional[str] = Field(None, pattern=r"^[6-9]\d{9}$")
    email: Optional[EmailStr] = None
    temporary_password: str = Field(..., min_length=8)


class DoctorCreateResponse(BaseModel):
    doctor_id: int
    staff_id: str
    first_name: str
    last_name: str
    specialty: str
    message: str


class DoctorSummaryResponse(BaseModel):
    doctor_id: int
    staff_id: str
    first_name: str
    last_name: str
    qualification: str
    specialty: str
    experience_years: int
    languages: Optional[str] = None
    consultation_fee: int
    available_days: Optional[str] = None

    model_config = {"from_attributes": True}


class DoctorLoginRequest(BaseModel):
    staff_id: str = Field(..., max_length=20)
    password: str


class DoctorLoginRequest(BaseModel):
    staff_id: str = Field(..., max_length=20)
    password: str


class DoctorPublicResponse(BaseModel):
    doctor_id: int
    first_name: str
    last_name: str
    qualification: str
    specialty: str
    experience_years: int
    languages: Optional[str] = None
    consultation_fee: int
    available_days: Optional[str] = None

    model_config = {"from_attributes": True}


class SpecialtyCountResponse(BaseModel):
    specialty: str
    doctor_count: int


class AvailabilityCreateRequest(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0 = Monday, 6 = Sunday")
    start_time: time
    end_time: time
    slot_minutes: int = Field(15, ge=5, le=120)

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, value: time, info) -> time:
        start = info.data.get("start_time")
        if start and value <= start:
            raise ValueError("end_time must be after start_time")
        return value


class AvailabilityResponse(BaseModel):
    availability_id: int
    doctor_id: int
    day_of_week: int
    start_time: time
    end_time: time
    slot_minutes: int

    model_config = {"from_attributes": True}


class AvailableSlotsResponse(BaseModel):
    doctor_id: int
    doctor_name: str
    date: date
    day_of_week: int
    slots: list[str]

class AppointmentBookingRequest(BaseModel):
    doctor_id: int
    patient_id: int
    scheduled_at: datetime
    reason_for_visit: Optional[str] = Field(None, max_length=255)


class AppointmentResponse(BaseModel):
    appointment_id: int
    appointment_ref: str
    doctor_id: int
    doctor_name: str
    patient_id: int
    patient_name: str
    mrn: str
    scheduled_at: datetime
    duration_minutes: int
    status: str
    reason_for_visit: Optional[str] = None


class AppointmentCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=255)

class DoctorTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool
    doctor_name: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class DoctorProfileResponse(BaseModel):
    doctor_id: int
    staff_id: str
    first_name: str
    last_name: str
    specialty: str
    registration_no: str
    must_change_password: bool

    model_config = {"from_attributes": True}
