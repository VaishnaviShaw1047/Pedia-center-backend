"""
Repository layer — all database access for the application.

No business rules live here. Every method does one thing: ask the database
a question, or write a row. If SQLAlchemy were swapped for something else,
this is the only file that would change.

Classes:
    GuardianRepository
    PatientRepository
    DoctorRepository
    AppointmentRepository
    UserRepository
"""

from datetime import datetime, time

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app import models


# =====================================================================
#  GUARDIAN
# =====================================================================

class GuardianRepository:

    @staticmethod
    def get_by_mobile(db: Session, mobile_number: str) -> models.Guardian | None:
        return (
            db.query(models.Guardian)
            .filter(models.Guardian.mobile_number == mobile_number)
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, guardian_id: int) -> models.Guardian | None:
        return (
            db.query(models.Guardian)
            .filter(models.Guardian.guardian_id == guardian_id)
            .first()
        )

    @staticmethod
    def add(db: Session, guardian: models.Guardian) -> models.Guardian:
        """Stage and flush so the database assigns guardian_id."""
        db.add(guardian)
        db.flush()
        return guardian

    @staticmethod
    def commit(db: Session) -> None:
        db.commit()

    @staticmethod
    def rollback(db: Session) -> None:
        db.rollback()


# =====================================================================
#  PATIENT
# =====================================================================

class PatientRepository:

    @staticmethod
    def add(db: Session, patient: models.Patient) -> models.Patient:
        """Stage and flush so the database assigns patient_id."""
        db.add(patient)
        db.flush()
        return patient

    @staticmethod
    def get_by_mrn(db: Session, mrn: str) -> models.Patient | None:
        return db.query(models.Patient).filter(models.Patient.mrn == mrn).first()

    @staticmethod
    def get_for_guardian(
        db: Session, patient_id: int, guardian_id: int
    ) -> models.Patient | None:
        """
        The ownership query. Both conditions in one filter, so the check
        cannot be forgotten — it is part of finding the record at all.
        """
        return (
            db.query(models.Patient)
            .filter(
                models.Patient.patient_id == patient_id,
                models.Patient.guardian_id == guardian_id,
                models.Patient.is_active == True,
            )
            .first()
        )

    @staticmethod
    def build_list_query(db: Session, search: str | None):
        """
        Returns an unexecuted query so the service can count and paginate
        against the same filters. joinedload avoids the N+1 problem when
        building guardian_name for each row.
        """
        query = (
            db.query(models.Patient)
            .options(joinedload(models.Patient.guardian))
            .filter(models.Patient.is_active == True)
        )

        if search:
            term = f"%{search.strip()}%"
            query = query.join(models.Guardian).filter(
                or_(
                    models.Patient.first_name.ilike(term),
                    models.Patient.last_name.ilike(term),
                    models.Patient.mrn.ilike(term),
                    models.Guardian.mobile_number.ilike(term),
                )
            )

        return query

    @staticmethod
    def count(query) -> int:
        return query.count()

    @staticmethod
    def page(query, page: int, page_size: int) -> list[models.Patient]:
        return (
            query.order_by(models.Patient.patient_id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

    @staticmethod
    def commit(db: Session) -> None:
        db.commit()

    @staticmethod
    def refresh(db: Session, patient: models.Patient) -> models.Patient:
        db.refresh(patient)
        return patient


# =====================================================================
#  DOCTOR  (and availability)
# =====================================================================

class DoctorRepository:

    # ---------- doctors ----------

    @staticmethod
    def get_by_registration_no(
        db: Session, registration_no: str
    ) -> models.Doctor | None:
        return (
            db.query(models.Doctor)
            .filter(models.Doctor.registration_no == registration_no)
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, doctor_id: int) -> models.Doctor | None:
        return (
            db.query(models.Doctor)
            .filter(models.Doctor.doctor_id == doctor_id)
            .first()
        )

    @staticmethod
    def get_active_by_id(db: Session, doctor_id: int) -> models.Doctor | None:
        return (
            db.query(models.Doctor)
            .filter(
                models.Doctor.doctor_id == doctor_id,
                models.Doctor.is_active == True,
            )
            .first()
        )

    @staticmethod
    def get_by_staff_id(db: Session, staff_id: str) -> models.Doctor | None:
        staff=db.query(models.Doctor).filter(models.Doctor.staff_id == staff_id).first()
        return staff

    @staticmethod
    def search(
        db: Session,
        specialty: str | None = None,
        language: str | None = None,
        max_fee: int | None = None,
        day: str | None = None,
        text: str | None = None,
    ) -> list[models.Doctor]:
        query = db.query(models.Doctor).filter(models.Doctor.is_active == True)

        if specialty:
            query = query.filter(models.Doctor.specialty.ilike(f"%{specialty}%"))

        if language:
            query = query.filter(models.Doctor.languages.ilike(f"%{language}%"))

        if max_fee is not None:
            query = query.filter(models.Doctor.consultation_fee <= max_fee)

        if day:
            query = query.filter(models.Doctor.available_days.ilike(f"%{day}%"))

        if text:
            term = f"%{text.strip()}%"
            query = query.filter(
                or_(
                    models.Doctor.first_name.ilike(term),
                    models.Doctor.last_name.ilike(term),
                    models.Doctor.specialty.ilike(term),
                )
            )

        return query.order_by(models.Doctor.experience_years.desc()).all()

    @staticmethod
    def specialty_counts(db: Session):
        """Aggregation rather than row fetching — GROUP BY with a count."""
        return (
            db.query(
                models.Doctor.specialty,
                func.count(models.Doctor.doctor_id).label("doctor_count"),
            )
            .filter(models.Doctor.is_active == True)
            .group_by(models.Doctor.specialty)
            .order_by(models.Doctor.specialty)
            .all()
        )

    @staticmethod
    def add(db: Session, doctor: models.Doctor) -> models.Doctor:
        db.add(doctor)
        db.flush()
        return doctor

    # ---------- availability ----------

    @staticmethod
    def find_overlapping_availability(
        db: Session, doctor_id: int, day_of_week: int, start_time, end_time
    ) -> models.DoctorAvailability | None:
        """
        Standard interval overlap test:
        existing.start < new.end AND existing.end > new.start
        """
        return (
            db.query(models.DoctorAvailability)
            .filter(
                models.DoctorAvailability.doctor_id == doctor_id,
                models.DoctorAvailability.day_of_week == day_of_week,
                models.DoctorAvailability.is_active == True,
                models.DoctorAvailability.start_time < end_time,
                models.DoctorAvailability.end_time > start_time,
            )
            .first()
        )

    @staticmethod
    def get_availability_for_day(
        db: Session, doctor_id: int, weekday: int
    ) -> list[models.DoctorAvailability]:
        return (
            db.query(models.DoctorAvailability)
            .filter(
                models.DoctorAvailability.doctor_id == doctor_id,
                models.DoctorAvailability.day_of_week == weekday,
                models.DoctorAvailability.is_active == True,
            )
            .all()
        )

    @staticmethod
    def list_availability(
        db: Session, doctor_id: int
    ) -> list[models.DoctorAvailability]:
        return (
            db.query(models.DoctorAvailability)
            .filter(
                models.DoctorAvailability.doctor_id == doctor_id,
                models.DoctorAvailability.is_active == True,
            )
            .order_by(
                models.DoctorAvailability.day_of_week,
                models.DoctorAvailability.start_time,
            )
            .all()
        )

    @staticmethod
    def add_availability(
        db: Session, availability: models.DoctorAvailability
    ) -> models.DoctorAvailability:
        db.add(availability)
        return availability

    @staticmethod
    def booked_times_on(db: Session, doctor_id: int, day_start, day_end) -> set:
        rows = (
            db.query(models.Appointment.scheduled_at)
            .filter(
                models.Appointment.doctor_id == doctor_id,
                models.Appointment.scheduled_at >= day_start,
                models.Appointment.scheduled_at <= day_end,
                models.Appointment.status.in_(["requested", "confirmed"]),
            )
            .all()
        )
        return {row.scheduled_at for row in rows}

    # ---------- transaction ----------

    @staticmethod
    def commit(db: Session) -> None:
        db.commit()

    @staticmethod
    def refresh(db: Session, obj):
        db.refresh(obj)
        return obj


# =====================================================================
#  APPOINTMENT
# =====================================================================

class AppointmentRepository:

    # ---------- lookups used before booking ----------

    @staticmethod
    def get_active_doctor(db: Session, doctor_id: int) -> models.Doctor | None:
        return DoctorRepository.get_active_by_id(db, doctor_id)

    @staticmethod
    def get_patient_for_guardian(
        db: Session, patient_id: int, guardian_id: int
    ) -> models.Patient | None:
        return PatientRepository.get_for_guardian(db, patient_id, guardian_id)

    @staticmethod
    def get_availability_rules(
        db: Session, doctor_id: int, weekday: int
    ) -> list[models.DoctorAvailability]:
        return DoctorRepository.get_availability_for_day(db, doctor_id, weekday)

    # ---------- conflict checks ----------

    @staticmethod
    def find_slot_conflict(
        db: Session, doctor_id: int, when: datetime
    ) -> models.Appointment | None:
        return (
            db.query(models.Appointment)
            .filter(
                models.Appointment.doctor_id == doctor_id,
                models.Appointment.scheduled_at == when,
                models.Appointment.status.in_(["requested", "confirmed"]),
            )
            .first()
        )

    @staticmethod
    def find_same_day_for_patient(
        db: Session, patient_id: int, day: datetime
    ) -> models.Appointment | None:
        day_start = datetime.combine(day.date(), time.min)
        day_end = datetime.combine(day.date(), time.max)

        return (
            db.query(models.Appointment)
            .filter(
                models.Appointment.patient_id == patient_id,
                models.Appointment.scheduled_at >= day_start,
                models.Appointment.scheduled_at <= day_end,
                models.Appointment.status.in_(["requested", "confirmed"]),
            )
            .first()
        )

    # ---------- reads ----------

    @staticmethod
    def get_by_ref_for_guardian(
        db: Session, ref: str, guardian_id: int
    ) -> models.Appointment | None:
        return (
            db.query(models.Appointment)
            .options(
                joinedload(models.Appointment.doctor),
                joinedload(models.Appointment.patient),
            )
            .filter(
                models.Appointment.appointment_ref == ref,
                models.Appointment.guardian_id == guardian_id,
            )
            .first()
        )

    @staticmethod
    def list_for_guardian(
        db: Session, guardian_id: int, upcoming_only: bool
    ) -> list[models.Appointment]:
        query = (
            db.query(models.Appointment)
            .options(
                joinedload(models.Appointment.doctor),
                joinedload(models.Appointment.patient),
            )
            .filter(models.Appointment.guardian_id == guardian_id)
        )

        if upcoming_only:
            query = query.filter(
                models.Appointment.scheduled_at >= datetime.now(),
                models.Appointment.status.in_(["requested", "confirmed"]),
            )

        return query.order_by(models.Appointment.scheduled_at).all()

    # ---------- writes ----------

    @staticmethod
    def add(db: Session, appointment: models.Appointment) -> models.Appointment:
        """Stage and flush so the database assigns appointment_id."""
        db.add(appointment)
        db.flush()
        return appointment

    @staticmethod
    def commit(db: Session) -> None:
        db.commit()

    @staticmethod
    def rollback(db: Session) -> None:
        db.rollback()

    @staticmethod
    def refresh(db: Session, appointment: models.Appointment) -> models.Appointment:
        db.refresh(appointment)
        return appointment

class UserRepository:

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> models.User | None:
        return (
            db.query(models.User)
            .filter(models.User.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_by_username(db: Session, username: str) -> models.User | None:
        return (
            db.query(models.User)
            .filter(models.User.username == username)
            .first()
        )

    @staticmethod
    def adduser(db: Session, user: models.User) -> models.User:
        """Stage and flush so the database assigns user_id."""
        db.add(user)
        db.flush()
        return user

    @staticmethod
    def commit(db: Session) -> None:
        db.commit()

    @staticmethod
    def rollback(db: Session) -> None:
        db.rollback()