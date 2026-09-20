from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Guardian(Base):
    __tablename__ = "guardian"

    guardian_id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    relationship_to_child = Column(String(20), nullable=False)

    mobile_number = Column(String(10), nullable=False, unique=True, index=True)
    email = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="parent")

    address_line1 = Column(String(100), nullable=False)
    address_line2 = Column(String(100), nullable=True)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    pincode = Column(String(6), nullable=False)

    preferred_language = Column(String(20), nullable=True)

    terms_accepted = Column(Boolean, nullable=False, default=False)
    health_data_consent = Column(Boolean, nullable=False, default=False)
    consent_version = Column(String(20), nullable=True)
    consent_timestamp = Column(DateTime, nullable=True)

    mobile_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patients = relationship("Patient", back_populates="guardian")


class Patient(Base):
    __tablename__ = "patient"

    patient_id = Column(Integer, primary_key=True, index=True)
    patient_uid = Column(String(36), nullable=False, unique=True, index=True)
    mrn = Column(String(20), nullable=False, unique=True, index=True)

    guardian_id = Column(Integer, ForeignKey("guardian.guardian_id"), nullable=False)

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)

    abha_id = Column(String(14), nullable=True, unique=True)
    aadhaar_number = Column(String(12), nullable=True)

    blood_group = Column(String(3), nullable=True)
    known_allergies = Column(String(255), nullable=True)
    existing_conditions = Column(String(500), nullable=True)
    current_medications = Column(String(255), nullable=True)
    immunization_status = Column(String(15), nullable=True)
    referred_by = Column(String(100), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guardian = relationship("Guardian", back_populates="patients")


class Doctor(Base):
    __tablename__ = "doctor"

    doctor_id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(String(20), nullable=False, unique=True, index=True)

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)

    registration_no = Column(String(30), nullable=False, unique=True)
    qualification = Column(String(150), nullable=False)
    specialty = Column(String(60), nullable=False)
    experience_years = Column(Integer, nullable=False, default=0)

    languages = Column(String(100), nullable=True)
    consultation_fee = Column(Integer, nullable=False)
    available_days = Column(String(60), nullable=True)

    mobile_number = Column(String(10), nullable=True)
    email = Column(String(100), nullable=True)

    password_hash = Column(String(255), nullable=False)
    must_change_password = Column(Boolean, nullable=False, default=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    availability = relationship("DoctorAvailability", back_populates="doctor")


class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    availability_id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctor.doctor_id"), nullable=False, index=True)

    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_minutes = Column(Integer, nullable=False, default=15)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    doctor = relationship("Doctor", back_populates="availability")


class Appointment(Base):
    __tablename__ = "appointment"

    appointment_id = Column(Integer, primary_key=True, index=True)
    appointment_ref = Column(String(20), nullable=False, unique=True, index=True)

    doctor_id = Column(Integer, ForeignKey("doctor.doctor_id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"), nullable=False, index=True)
    guardian_id = Column(Integer, ForeignKey("guardian.guardian_id"), nullable=False)

    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False, default=15)

    status = Column(String(15), nullable=False, default="requested")
    reason_for_visit = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("doctor_id", "scheduled_at", name="uq_doctor_slot"),
    )

    doctor = relationship("Doctor")
    patient = relationship("Patient")
