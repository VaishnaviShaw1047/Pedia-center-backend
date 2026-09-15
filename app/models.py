from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
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