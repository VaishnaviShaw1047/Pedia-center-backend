"""
Service layer — all business rules for the application.

Knows nothing about routes, request bodies or response models. Each method
takes plain arguments, applies the rules, calls the repository, and returns
model objects.

One compromise: services raise HTTPException directly rather than a domain
error the router would translate. Strictly a service should not know about
HTTP status codes. Keeping them here avoids an extra layer .

Classes:
    RegistrationService
    PatientService
    DoctorService
    AppointmentService
    AuthService
"""

import uuid
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.auth import create_access_token, hash_password, verify_password
from app.repository import (
    AppointmentRepository,
    DoctorRepository,
    GuardianRepository,
    PatientRepository,
)


# =====================================================================
#  REGISTRATION
# =====================================================================

class RegistrationService:

    guardians = GuardianRepository
    patients = PatientRepository

    @staticmethod
    def generate_mrn(patient_id: int) -> str:
        return f"PC-2026-{patient_id:06d}"

    @classmethod
    def register(
        cls, db: Session, payload
    ) -> tuple[models.Guardian, list[models.Patient]]:
        """
        Creates a guardian and their children in one transaction.
        Returns both; the router turns them into a response schema.
        """

        if cls.guardians.get_by_mobile(db, payload.mobile_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This mobile number is already registered",
            )

        guardian = models.Guardian(
            first_name=payload.first_name,
            last_name=payload.last_name,
            relationship_to_child=payload.relationship_to_child,
            mobile_number=payload.mobile_number,
            email=payload.email,
            password_hash=hash_password(payload.password),
            address_line1=payload.address_line1,
            address_line2=payload.address_line2,
            city=payload.city,
            state=payload.state,
            pincode=payload.pincode,
            preferred_language=payload.preferred_language,
            terms_accepted=payload.terms_accepted,
            health_data_consent=payload.health_data_consent,
        )

        # flush assigns guardian_id, needed as the children's foreign key
        cls.guardians.add(db, guardian)

        created: list[models.Patient] = []

        for child in payload.children:
            patient = models.Patient(
                patient_uid=str(uuid.uuid4()),
                mrn="",
                guardian_id=guardian.guardian_id,
                first_name=child.first_name,
                last_name=child.last_name,
                date_of_birth=child.date_of_birth,
                gender=child.gender,
                abha_id=child.abha_id,
                aadhaar_number=child.aadhaar_number,
                blood_group=child.blood_group,
                known_allergies=child.known_allergies,
                existing_conditions=child.existing_conditions,
                current_medications=child.current_medications,
                immunization_status=child.immunization_status,
                referred_by=child.referred_by,
            )
            

            # flush assigns patient_id, which the MRN is derived from
            cls.patients.add(db, patient)
            patient.mrn = cls.generate_mrn(patient.patient_id)
            created.append(patient)

        # one commit: the whole registration is atomic
        cls.guardians.commit(db)

        return guardian, created


# =====================================================================
#  PATIENT
# =====================================================================

class PatientService:

    repo = PatientRepository

    @classmethod
    def list_patients(
        cls, db: Session, search: str | None, page: int, page_size: int
    ) -> tuple[int, list[models.Patient]]:
        """Returns (total, page of patients). Total is counted before paging."""
        query = cls.repo.build_list_query(db, search)
        total = cls.repo.count(query)
        patients = cls.repo.page(query, page, page_size)
        return total, patients

    @classmethod
    def get_by_mrn(cls, db: Session, mrn: str) -> models.Patient:
        patient = cls.repo.get_by_mrn(db, mrn)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient

    @classmethod
    def update(cls, db: Session, mrn: str, payload) -> models.Patient:
        patient = cls.get_by_mrn(db, mrn)

        # exclude_unset: only the fields the client actually sent.
        # Without it, omitted fields arrive as None and wipe stored values.
        changes = payload.model_dump(exclude_unset=True)

        if not changes:
            raise HTTPException(
                status_code=400, detail="No fields provided to update"
            )

        for field, value in changes.items():
            setattr(patient, field, value)

        cls.repo.commit(db)
        return cls.repo.refresh(db, patient)


# =====================================================================
#  DOCTOR
# =====================================================================

class DoctorService:

    repo = DoctorRepository

    @staticmethod
    def generate_staff_id(doctor_id: int) -> str:
        return f"DOC-2026-{doctor_id:04d}"

    # ---------- creation ----------

    @classmethod
    def create(cls, db: Session, payload) -> models.Doctor:

        if cls.repo.get_by_registration_no(db, payload.registration_no):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A doctor with this registration number already exists",
            )

        doctor = models.Doctor(
            staff_id="",
            first_name=payload.first_name,
            last_name=payload.last_name,
            registration_no=payload.registration_no,
            qualification=payload.qualification,
            specialty=payload.specialty,
            experience_years=payload.experience_years,
            languages=payload.languages,
            consultation_fee=payload.consultation_fee,
            available_days=payload.available_days,
            mobile_number=payload.mobile_number,
            email=payload.email,
            password_hash=hash_password(payload.temporary_password),
        )

        cls.repo.add(db, doctor)
        doctor.staff_id = cls.generate_staff_id(doctor.doctor_id)
        cls.repo.commit(db)

        return cls.repo.refresh(db, doctor)

    # ---------- browsing ----------

    @classmethod
    def browse(
        cls,
        db: Session,
        specialty: str | None = None,
        language: str | None = None,
        max_fee: int | None = None,
        day: str | None = None,
        text: str | None = None,
    ) -> list[models.Doctor]:
        return cls.repo.search(db, specialty, language, max_fee, day, text)

    @classmethod
    def specialties(cls, db: Session):
        return cls.repo.specialty_counts(db)

    @classmethod
    def get_one(cls, db: Session, doctor_id: int) -> models.Doctor:
        doctor = cls.repo.get_active_by_id(db, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return doctor

    # ---------- availability ----------

    @classmethod
    def set_availability(
        cls, db: Session, doctor_id: int, payload
    ) -> models.DoctorAvailability:

        if not cls.repo.get_by_id(db, doctor_id):
            raise HTTPException(status_code=404, detail="Doctor not found")

        clash = cls.repo.find_overlapping_availability(
            db, doctor_id, payload.day_of_week, payload.start_time, payload.end_time
        )
        if clash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This overlaps an existing availability block for that day",
            )

        availability = models.DoctorAvailability(
            doctor_id=doctor_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
            slot_minutes=payload.slot_minutes,
        )

        cls.repo.add_availability(db, availability)
        cls.repo.commit(db)

        return cls.repo.refresh(db, availability)

    @classmethod
    def list_availability(cls, db: Session, doctor_id: int):
        return cls.repo.list_availability(db, doctor_id)

    # ---------- slots ----------

    @classmethod
    def free_slots(cls, db: Session, doctor_id: int, slot_date: date):
        """
        Generate every slot the rules produce for that weekday, then
        subtract the ones already booked and any that have already passed.
        """

        if slot_date < date.today():
            raise HTTPException(
                status_code=400, detail="Cannot look up slots in the past"
            )

        doctor = cls.get_one(db, doctor_id)
        weekday = slot_date.weekday()

        rules = cls.repo.get_availability_for_day(db, doctor_id, weekday)

        generated: list[datetime] = []
        for rule in rules:
            cursor = datetime.combine(slot_date, rule.start_time)
            day_end = datetime.combine(slot_date, rule.end_time)
            step = timedelta(minutes=rule.slot_minutes)

            # cursor + step: the slot must END within the block, or a
            # 12:50 start would overrun a 13:00 finish
            while cursor + step <= day_end:
                generated.append(cursor)
                cursor += step

        booked = cls.repo.booked_times_on(
            db,
            doctor_id,
            datetime.combine(slot_date, time.min),
            datetime.combine(slot_date, time.max),
        )

        now = datetime.now()
        free = [
            slot.strftime("%H:%M")
            for slot in sorted(generated)
            if slot not in booked and slot > now
        ]

        return doctor, weekday, free


# =====================================================================
#  APPOINTMENT
# =====================================================================

class AppointmentService:

    repo = AppointmentRepository

    @staticmethod
    def generate_ref(appointment_id: int) -> str:
        return f"APT-2026-{appointment_id:06d}"

    @classmethod
    def slot_length_if_offered(
        cls, db: Session, doctor_id: int, when: datetime
    ) -> int | None:
        """
        Regenerate the doctor's slots for that weekday and look for an exact
        match. Returns the slot length in minutes, or None if the time is
        not a slot the doctor offers.
        """
        rules = cls.repo.get_availability_rules(db, doctor_id, when.weekday())

        for rule in rules:
            cursor = datetime.combine(when.date(), rule.start_time)
            day_end = datetime.combine(when.date(), rule.end_time)
            step = timedelta(minutes=rule.slot_minutes)

            while cursor + step <= day_end:
                if cursor == when:
                    return rule.slot_minutes
                cursor += step

        return None

    @classmethod
    def book(
        cls,
        db: Session,
        guardian: models.Guardian,
        doctor_id: int,
        patient_id: int,
        scheduled_at: datetime,
        reason_for_visit: str | None,
    ) -> models.Appointment:

        doctor = cls.repo.get_active_doctor(db, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        # ownership: the child must belong to this guardian.
        # 404 rather than 403 — a 403 would confirm the patient exists.
        patient = cls.repo.get_patient_for_guardian(
            db, patient_id, guardian.guardian_id
        )
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # normalise: a client sending 10:15:03 would not match a 10:15:00 slot
        when = scheduled_at.replace(second=0, microsecond=0, tzinfo=None)

        if when <= datetime.now():
            raise HTTPException(
                status_code=400, detail="Appointment time must be in the future"
            )

        slot_minutes = cls.slot_length_if_offered(db, doctor.doctor_id, when)
        if slot_minutes is None:
            raise HTTPException(
                status_code=400,
                detail="That time is not an available slot for this doctor",
            )

        if cls.repo.find_slot_conflict(db, doctor.doctor_id, when):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="That slot has just been taken",
            )

        if cls.repo.find_same_day_for_patient(db, patient.patient_id, when):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This patient already has an appointment on that day",
            )

        appointment = models.Appointment(
            appointment_ref="",
            doctor_id=doctor.doctor_id,
            patient_id=patient.patient_id,
            guardian_id=guardian.guardian_id,
            scheduled_at=when,
            duration_minutes=slot_minutes,
            status="requested",
            reason_for_visit=reason_for_visit,
        )

        try:
            cls.repo.add(db, appointment)
            appointment.appointment_ref = cls.generate_ref(appointment.appointment_id)
            cls.repo.commit(db)
        except IntegrityError:
            # two requests passed the check at the same moment; the unique
            # constraint on (doctor_id, scheduled_at) caught the loser
            cls.repo.rollback(db)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="That slot has just been taken",
            )

        return cls.repo.refresh(db, appointment)

    @classmethod
    def list_for_guardian(
        cls, db: Session, guardian: models.Guardian, upcoming_only: bool
    ) -> list[models.Appointment]:
        return cls.repo.list_for_guardian(db, guardian.guardian_id, upcoming_only)

    @classmethod
    def cancel(
        cls, db: Session, guardian: models.Guardian, ref: str
    ) -> models.Appointment:

        appointment = cls.repo.get_by_ref_for_guardian(db, ref, guardian.guardian_id)

        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if appointment.status in ("cancelled", "completed"):
            raise HTTPException(
                status_code=400,
                detail=f"This appointment is already {appointment.status}",
            )

        appointment.status = "cancelled"
        cls.repo.commit(db)

        return cls.repo.refresh(db, appointment)


# =====================================================================
#  AUTH
# =====================================================================

class AuthService:
    """
    Login rules only. Token creation and the request dependencies stay in
    app/auth.py — those are infrastructure used by every router, not a
    feature service.
    """

    guardians = GuardianRepository
    doctors = DoctorRepository

    # ---------- guardian ----------

    @classmethod
    def login_guardian(cls, db: Session, mobile_number: str, password: str) -> str:
        guardian = cls.guardians.get_by_mobile(db, mobile_number)

        # same message for both failures: naming which one leaks
        # whether that mobile number is registered
        if not guardian or not verify_password(password, guardian.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect mobile number or password",
            )

        if not guardian.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is inactive",
            )

        return create_access_token(guardian.guardian_id, guardian.role)

    # ---------- doctor ----------

    @classmethod
    def login_doctor(cls, db: Session, staff_id: str, password: str) -> models.Doctor:
        """Returns the doctor; the router builds the response with the token."""
        doctor = cls.doctors.get_by_staff_id(db, staff_id.strip().upper())

        if not doctor or not verify_password(password, doctor.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect staff ID or password",
            )

        if not doctor.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is inactive",
            )

        return doctor

    @staticmethod
    def doctor_token(doctor: models.Doctor) -> str:
        # token_type="doctor" is what stops this token being accepted
        # by guardian endpoints
        return create_access_token(doctor.doctor_id, "doctor", token_type="doctor")

    @classmethod
    def change_doctor_password(
        cls,
        db: Session,
        doctor: models.Doctor,
        current_password: str,
        new_password: str,
    ) -> None:
        if not verify_password(current_password, doctor.password_hash):
            raise HTTPException(
                status_code=400, detail="Current password is incorrect"
            )

        doctor.password_hash = hash_password(new_password)
        doctor.must_change_password = False
        cls.doctors.commit(db)

