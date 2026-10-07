"""
Service layer — all business rules for the application.

Knows nothing about routes, request bodies or response models. Each method
takes plain arguments, applies the rules, calls the repository, and returns
model objects.

One compromise: services raise HTTPException directly rather than a domain
error the router would translate. Strictly a service should not know about
HTTP status codes. Keeping them here avoids an extra layer.

Classes:
    RegistrationService
    PatientService
    DoctorService
    AppointmentService
    UserService
    AuthService
"""

import uuid
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status

from app.mongodb import (
    users_collection,
    guardians_collection,
    patients_collection,
    doctors_collection,
    appointments_collection,
)

from app import schemas

from app.auth import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)

from app.repository import (
    AppointmentRepository,
    DoctorRepository,
    GuardianRepository,
    PatientRepository,
    UserRepository,
    PatientTreatmentRecordRepository,
)


# =====================================================================
# REGISTRATION
# =====================================================================

class RegistrationService:

    guardians = GuardianRepository
    patients = PatientRepository

    @staticmethod
    def generate_mrn(patient_id: int) -> str:
        return f"PC-2026-{patient_id:06d}"

    @classmethod
    def register(cls, payload):
        """
        Creates a guardian and their children in MongoDB.
        """

        # 1. Check whether mobile number is already registered
        if cls.guardians.get_by_mobile(payload.mobile_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This mobile number is already registered",
            )

        # 2. Generate the next guardian_id
        last_guardian = guardians_collection.find_one(
            {},
            sort=[("guardian_id", -1)],
        )

        next_guardian_id = (
            last_guardian["guardian_id"] + 1
            if last_guardian
            else 1
        )

        # 3. Create guardian document
        guardian = {
            "guardian_id": next_guardian_id,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "role": "parent",
            "relationship_to_child": payload.relationship_to_child,
            "mobile_number": payload.mobile_number,
            "email": payload.email,
            "password_hash": hash_password(payload.password),
            "address_line1": payload.address_line1,
            "address_line2": payload.address_line2,
            "city": payload.city,
            "state": payload.state,
            "pincode": payload.pincode,
            "preferred_language": payload.preferred_language,
            "terms_accepted": payload.terms_accepted,
            "health_data_consent": payload.health_data_consent,
            "is_active": True,
        }

        cls.guardians.add(guardian)

        # 4. Create patients
        created = []

        for child in payload.children:

            last_patient = patients_collection.find_one(
                {},
                sort=[("patient_id", -1)],
            )

            next_patient_id = (
                last_patient["patient_id"] + 1
                if last_patient
                else 1
            )

            patient = {
                "patient_id": next_patient_id,
                "patient_uid": str(uuid.uuid4()),
                "mrn": cls.generate_mrn(next_patient_id),
                "guardian_id": next_guardian_id,
                "guardian_name": (
                    f"{payload.first_name} {payload.last_name}"
                ),
                "guardian_mobile_number": payload.mobile_number,
                "first_name": child.first_name,
                "last_name": child.last_name,
                "date_of_birth": datetime.combine(
                    child.date_of_birth,
                    datetime.min.time(),
                ),
                "gender": child.gender,
                "abha_id": child.abha_id,
                "aadhaar_number": child.aadhaar_number,
                "blood_group": child.blood_group,
                "known_allergies": child.known_allergies,
                "existing_conditions": child.existing_conditions,
                "current_medications": child.current_medications,
                "immunization_status": child.immunization_status,
                "referred_by": child.referred_by,
                "is_active": True,
            }

            cls.patients.add(patient)
            created.append(patient)

        return guardian, created


# =====================================================================
# PATIENT
# =====================================================================

class PatientService:

    repo = PatientRepository

    @classmethod
    def list_patients(
        cls,
        search: str | None,
        page: int,
        page_size: int,
    ) -> tuple[int, list[dict]]:

        query = cls.repo.build_list_query(search)
        total = cls.repo.count(query)
        patients = cls.repo.page(query, page, page_size)

        return total, patients

    @classmethod
    def get_by_mrn(
        cls,
        mrn: str,
    ) -> dict:

        patient = cls.repo.get_by_mrn(mrn)

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient not found",
            )

        return patient

    @classmethod
    def update(
        cls,
        mrn: str,
        payload,
    ) -> dict:

        patient = cls.get_by_mrn(mrn)

        changes = payload.model_dump(
            exclude_unset=True
        )

        if not changes:
            raise HTTPException(
                status_code=400,
                detail="No fields provided to update",
            )

        cls.repo.update(
            patient["patient_id"],
            changes,
        )

        return cls.get_by_mrn(mrn)


# =====================================================================
# DOCTOR
# =====================================================================

class DoctorService:

    repo = DoctorRepository

    @staticmethod
    def generate_staff_id(
        doctor_id: int,
    ) -> str:

        return f"DOC-2026-{doctor_id:04d}"

    # -----------------------------------------------------------------
    # CREATE DOCTOR
    # -----------------------------------------------------------------

    @classmethod
    def create(
        cls,
        payload,
    ):

        if cls.repo.get_by_registration_no(
            payload.registration_no
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A doctor with this registration "
                    "number already exists"
                ),
            )

        last_doctor = doctors_collection.find_one(
            {},
            sort=[("doctor_id", -1)],
        )

        next_doctor_id = (
            last_doctor["doctor_id"] + 1
            if last_doctor
            else 1
        )

        doctor = {
            "doctor_id": next_doctor_id,
            "staff_id": cls.generate_staff_id(
                next_doctor_id
            ),
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "registration_no": payload.registration_no,
            "qualification": payload.qualification,
            "specialty": payload.specialty,
            "experience_years": payload.experience_years,
            "languages": payload.languages,
            "consultation_fee": payload.consultation_fee,
            "available_days": payload.available_days,
            "mobile_number": payload.mobile_number,
            "email": payload.email,
            "password_hash": hash_password(
                payload.temporary_password
            ),
            "is_active": True,
            "availability": [],
        }

        cls.repo.add(doctor)

        return cls.repo.get_by_id(
            next_doctor_id
        )

    # -----------------------------------------------------------------
    # BROWSE DOCTORS
    # -----------------------------------------------------------------

    @classmethod
    def browse(
        cls,
        specialty: str | None = None,
        language: str | None = None,
        max_fee: int | None = None,
        day: str | None = None,
        text: str | None = None,
    ):

        return cls.repo.search(
            specialty=specialty,
            language=language,
            max_fee=max_fee,
            day=day,
            text=text,
        )

    @classmethod
    def specialties(cls):

        return cls.repo.specialty_counts()

    @classmethod
    def get_one(
        cls,
        doctor_id: int,
    ):

        doctor = cls.repo.get_active_by_id(
            doctor_id
        )

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found",
            )

        return doctor

    # -----------------------------------------------------------------
    # AVAILABILITY
    # -----------------------------------------------------------------

    @classmethod
    def set_availability(
        cls,
        doctor_id: int,
        payload,
    ):

        if not cls.repo.get_by_id(
            doctor_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Doctor not found",
            )

        clash = cls.repo.find_overlapping_availability(
            doctor_id,
            payload.day_of_week,
            payload.start_time,
            payload.end_time,
        )

        if clash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This overlaps an existing availability "
                    "block for that day"
                ),
            )

        availability = {
            "day_of_week": payload.day_of_week,
            "start_time": payload.start_time,
            "end_time": payload.end_time,
            "slot_minutes": payload.slot_minutes,
            "is_active": True,
        }

        return cls.repo.add_availability(
            doctor_id,
            availability,
        )

    @classmethod
    def list_availability(
        cls,
        doctor_id: int,
    ):

        if not cls.repo.get_active_by_id(
            doctor_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Doctor not found",
            )

        return cls.repo.list_availability(
            doctor_id
        )

    # -----------------------------------------------------------------
    # FREE SLOTS
    # -----------------------------------------------------------------

    @classmethod
    def free_slots(
        cls,
        doctor_id: int,
        slot_date: date,
    ):

        if slot_date < date.today():
            raise HTTPException(
                status_code=400,
                detail="Cannot look up slots in the past",
            )

        doctor = cls.get_one(
            doctor_id
        )

        weekday = slot_date.weekday()

        rules = cls.repo.get_availability_for_day(
            doctor_id,
            weekday,
        )

        generated: list[datetime] = []

        for rule in rules:

            cursor = datetime.combine(
                slot_date,
                rule["start_time"],
            )

            day_end = datetime.combine(
                slot_date,
                rule["end_time"],
            )

            step = timedelta(
                minutes=rule["slot_minutes"]
            )

            while cursor + step <= day_end:
                generated.append(cursor)
                cursor += step

        booked = cls.repo.booked_times_on(
            doctor_id,
            datetime.combine(
                slot_date,
                time.min,
            ),
            datetime.combine(
                slot_date,
                time.max,
            ),
        )

        now = datetime.now()

        free = [
            slot.strftime("%H:%M")
            for slot in sorted(generated)
            if slot not in booked
            and slot > now
        ]

        return doctor, weekday, free


# =====================================================================
# APPOINTMENT
# =====================================================================

class AppointmentService:

    repo = AppointmentRepository

    @staticmethod
    def generate_ref(
        appointment_id: int,
    ) -> str:

        return f"APT-2026-{appointment_id:06d}"

    @classmethod
    def slot_length_if_offered(
        cls,
        doctor_id: int,
        when: datetime,
    ) -> int | None:

        rules = cls.repo.get_availability_rules(
            doctor_id,
            when.weekday(),
        )

        for rule in rules:

            cursor = datetime.combine(
                when.date(),
                rule["start_time"],
            )

            day_end = datetime.combine(
                when.date(),
                rule["end_time"],
            )

            step = timedelta(
                minutes=rule["slot_minutes"]
            )

            while cursor + step <= day_end:

                if cursor == when:
                    return rule["slot_minutes"]

                cursor += step

        return None

    @classmethod
    def book(
        cls,
        guardian,
        doctor_id: int,
        patient_id: int,
        scheduled_at: datetime,
        reason_for_visit: str | None,
    ):

        # 1. Check doctor
        doctor = cls.repo.get_active_doctor(
            doctor_id
        )

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found",
            )

        # 2. Get guardian_id
        if isinstance(guardian, dict):
            guardian_id = guardian["guardian_id"]
        else:
            guardian_id = guardian.guardian_id

        # 3. Check patient ownership
        patient = cls.repo.get_patient_for_guardian(
            patient_id,
            guardian_id,
        )

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient not found",
            )

        # 4. Normalize appointment time
        when = scheduled_at.replace(
            second=0,
            microsecond=0,
            tzinfo=None,
        )

        if when <= datetime.now():
            raise HTTPException(
                status_code=400,
                detail="Appointment time must be in the future",
            )

        # 5. Check offered slot
        slot_minutes = cls.slot_length_if_offered(
            doctor["doctor_id"],
            when,
        )

        if slot_minutes is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "That time is not an available "
                    "slot for this doctor"
                ),
            )

        # 6. Check doctor slot conflict
        if cls.repo.find_slot_conflict(
            doctor["doctor_id"],
            when,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="That slot has just been taken",
            )

        # 7. Check patient's same-day appointment
        if cls.repo.find_same_day_for_patient(
            patient["patient_id"],
            when,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This patient already has an "
                    "appointment on that day"
                ),
            )

        # 8. Generate appointment ID
        last_appointment = appointments_collection.find_one(
            {},
            sort=[("appointment_id", -1)],
        )

        next_appointment_id = (
            last_appointment["appointment_id"] + 1
            if last_appointment
            else 1
        )

        # 9. Create appointment
        appointment = {
            "appointment_id": next_appointment_id,
            "appointment_ref": cls.generate_ref(
                next_appointment_id
            ),
            "doctor_id": doctor["doctor_id"],
            "patient_id": patient["patient_id"],
            "guardian_id": guardian_id,
            "scheduled_at": when,
            "duration_minutes": slot_minutes,
            "status": "requested",
            "reason_for_visit": reason_for_visit,
        }

        # 10. Save appointment
        cls.repo.add(appointment)

        return cls.repo.refresh(
            appointment
        )

    @classmethod
    def list_for_guardian(
        cls,
        guardian,
        upcoming_only: bool,
    ):

        if isinstance(guardian, dict):
            guardian_id = guardian["guardian_id"]
        else:
            guardian_id = guardian.guardian_id

        return cls.repo.list_for_guardian(
            guardian_id,
            upcoming_only,
        )

    @classmethod
    def cancel(
        cls,
        guardian,
        ref: str,
    ):

        if isinstance(guardian, dict):
            guardian_id = guardian["guardian_id"]
        else:
            guardian_id = guardian.guardian_id

        appointment = cls.repo.get_by_ref_for_guardian(
            ref,
            guardian_id,
        )

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found",
            )

        if appointment["status"] in (
            "cancelled",
            "completed",
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"This appointment is already "
                    f"{appointment['status']}"
                ),
            )

        appointments_collection.update_one(
            {
                "appointment_id": appointment[
                    "appointment_id"
                ]
            },
            {
                "$set": {
                    "status": "cancelled"
                }
            },
        )

        return cls.repo.refresh(
            {
                **appointment,
                "status": "cancelled",
            }
        )


# =====================================================================
# USER
# =====================================================================

class UserService:

    userRepo = UserRepository

    @classmethod
    def get_user_by_id(
        cls,
        user_id: int,
    ):

        user = cls.userRepo.get_by_id(
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        return user

    @classmethod
    def get_user_by_username(
        cls,
        username: str,
    ):

        user = cls.userRepo.get_by_username(
            username
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        return user

    @classmethod
    def create_user(
        cls,
        payload: schemas.UserCreateRequest,
    ):

        existing_user = cls.userRepo.get_by_username(
            payload.username
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A user with this username "
                    "already exists"
                ),
            )

        # Generate next user_id
        last_user = users_collection.find_one(
            {},
            sort=[("user_id", -1)],
        )

        next_user_id = (
            last_user["user_id"] + 1
            if last_user
            else 1
        )

        user = {
            "user_id": next_user_id,
            "username": payload.username,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "user_type": payload.user_type,

            # Used for authorization
            "role": payload.user_type,

            # User passwords use the "password" field
            "password": hash_password(
                payload.password
            ),

            "is_active": True,
        }

        cls.userRepo.adduser(
            user
        )

        return user

    @classmethod
    def update_user(
        cls,
        user_id: int,
        user_data,
    ):

        cls.get_user_by_id(
            user_id
        )

        changes = user_data.model_dump(
            exclude_unset=True
        )

        if not changes:
            raise HTTPException(
                status_code=400,
                detail="No fields provided to update",
            )

        cls.userRepo.update_user(
            user_id,
            changes,
        )

        return cls.get_user_by_id(
            user_id
        )

    @classmethod
    def delete_user(
        cls,
        user_id: int,
    ) -> None:

        cls.get_user_by_id(
            user_id
        )

        cls.userRepo.delete_user(
            user_id
        )

    @classmethod
    def list_users(
        cls,
        search: str | None,
        page: int,
        page_size: int,
    ):

        return cls.userRepo.list_users(
            search,
            page,
            page_size,
        )

    @classmethod
    def authenticate_user(
        cls,
        username: str,
        password: str,
    ):

        user = cls.userRepo.get_by_username(
            username
        )

        if not user or not verify_password(
            password,
            user["password"],
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        return user

    @classmethod
    def reset_user_password(
        cls,
        user_id: int,
        new_password: str,
    ) -> None:

        cls.get_user_by_id(
            user_id
        )

        cls.userRepo.update_user(
            user_id,
            {
                "password": hash_password(
                    new_password
                )
            },
        )

    @classmethod
    def change_user_password(
        cls,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> None:

        user = cls.get_user_by_id(
            user_id
        )

        if not verify_password(
            current_password,
            user["password"],
        ):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect",
            )

        cls.userRepo.update_user(
            user_id,
            {
                "password": hash_password(
                    new_password
                )
            },
        )

    @classmethod
    def generate_user_token(
        cls,
        user,
    ) -> str:

        return create_access_token(
            user["user_id"],
            user.get("role", user.get("user_type", "user")),
            token_type="user",
        )

    @classmethod
    def verify_user_token(
        cls,
        token: str,
    ):

        payload = verify_token(
            token
        )

        user_id = payload.get(
            "sub"
        )

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        return cls.get_user_by_id(
            int(user_id)
        )


# =====================================================================
# AUTHENTICATION
# =====================================================================

class AuthService:

    guardians = GuardianRepository
    doctors = DoctorRepository
    users = UserRepository

    # -----------------------------------------------------------------
    # GUARDIAN LOGIN
    # -----------------------------------------------------------------

    @classmethod
    def login_guardian(
        cls,
        mobile_number: str,
        password: str,
    ) -> str:

        guardian = cls.guardians.get_by_mobile(
            mobile_number
        )

        if not guardian or not verify_password(
            password,
            guardian["password_hash"],
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect mobile number or password",
            )

        if not guardian.get(
            "is_active",
            False,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is inactive",
            )

        role = guardian.get(
            "role",
            "guardian",
        )

        return create_access_token(
            guardian["guardian_id"],
            role,
            token_type="guardian",
        )

    # -----------------------------------------------------------------
    # ADMIN LOGIN
    # -----------------------------------------------------------------

    @classmethod
    def login_admin(
        cls,
        username: str,
        password: str,
    ) -> str:

        user = cls.users.get_by_username(
            username
        )

        if not user or not verify_password(
            password,
            user["password"],
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        if not user.get(
            "is_active",
            False,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is inactive",
            )

        if user.get(
            "role",
            user.get("user_type"),
        ) != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        return create_access_token(
            user["user_id"],
            "Admin",
            token_type="admin",
        )

    # -----------------------------------------------------------------
    # DOCTOR LOGIN
    # -----------------------------------------------------------------

    @classmethod
    def login_doctor(
        cls,
        staff_id: str,
        password: str,
    ):

        doctor = cls.doctors.get_by_staff_id(
            staff_id.strip().upper()
        )

        if not doctor or not verify_password(
            password,
            doctor["password_hash"],
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect staff ID or password",
            )

        if not doctor.get(
            "is_active",
            False,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is inactive",
            )

        return doctor

    # -----------------------------------------------------------------
    # DOCTOR TOKEN
    # -----------------------------------------------------------------

    @classmethod
    def doctor_token(
        cls,
        doctor,
    ) -> str:

        return create_access_token(
            doctor["doctor_id"],
            doctor.get(
                "role",
                "doctor",
            ),
            token_type="doctor",
        )

    # -----------------------------------------------------------------
    # DOCTOR CHANGE PASSWORD
    # -----------------------------------------------------------------

    @classmethod
    def change_doctor_password(
        cls,
        doctor,
        current_password: str,
        new_password: str,
    ) -> None:

        if not verify_password(
            current_password,
            doctor["password_hash"],
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        cls.doctors.update(
            doctor["doctor_id"],
            {
                "password": hash_password(
                    new_password
                )
            },
        )

# =====================================================================
# PATIENT TREATMENT RECORD SERVICE
# =====================================================================

class TreatmentRecordService:

    @staticmethod
    def create(payload, current_user):

        # -------------------------------------------------------------
        # Validate that the requested patient exists
        # -------------------------------------------------------------
        patient = PatientRepository.get_by_id(
            payload.patient_id
        )

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        role = current_user.get(
            "role",
            current_user.get("user_type"),
        )

        # -------------------------------------------------------------
        # Authorization-aware doctor identification:
        # Doctor → doctor_id comes from the authenticated JWT
        # Admin   → doctor_id comes from the request body
        # -------------------------------------------------------------
        if role == "Doctor":

            doctor_id = current_user["doctor_id"]

        elif role == "Admin":

            doctor_id = payload.doctor_id

            if doctor_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="doctor_id is required for Admin",
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin or Doctor can create treatment records",
            )

        # -------------------------------------------------------------
        # Validate that the selected Doctor exists
        # -------------------------------------------------------------
        doctor = DoctorRepository.get_by_id(
            doctor_id
        )

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
            )

        # -------------------------------------------------------------
        # Generate the next treatment record ID
        # -------------------------------------------------------------
        latest_record = (
            PatientTreatmentRecordRepository
            .get_latest_record()
        )

        if latest_record:
            treatment_record_id = (
                latest_record["treatment_record_id"] + 1
            )
        else:
            treatment_record_id = 100001

        # -------------------------------------------------------------
        # Create timestamps
        # -------------------------------------------------------------
        now = datetime.utcnow()

        # -------------------------------------------------------------
        # Build the treatment record document
        # -------------------------------------------------------------
        record = {
            "treatment_record_id": treatment_record_id,

            "patient_id": patient["patient_id"],
            "patient_name": (
                f'{patient["first_name"]} '
                f'{patient["last_name"]}'
            ),

            "doctor_id": doctor["doctor_id"],
            "doctor_name": (
                f'{doctor["first_name"]} '
                f'{doctor["last_name"]}'
            ),

            "appointment_id": payload.appointment_id,

            "visit_date": payload.visit_date,
            "diagnosis": payload.diagnosis,

            "medications": [
                medication.model_dump()
                for medication in payload.medications
            ],

            "treatment_plan": payload.treatment_plan,
            "follow_up_date": payload.follow_up_date,
            "clinical_notes": payload.clinical_notes,

            "record_status": "active",

            "created_at": now,
            "updated_at": now,
        }

        # -------------------------------------------------------------
        # Save treatment record in MongoDB
        # -------------------------------------------------------------
        return PatientTreatmentRecordRepository.add(
            record
        )
    #####################################################################
    @staticmethod
    def get_patient_history(
        patient_id: int,
        current_user,
    ):
        # -------------------------------------------------------------
        # Validate that the requested patient exists
        # -------------------------------------------------------------
        patient = PatientRepository.get_by_id(
            patient_id
        )

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        role = current_user.get(
            "role",
            current_user.get("user_type"),
        )

        # -------------------------------------------------------------
        # Authorization: Admin can view any patient's records
        # -------------------------------------------------------------
        if role == "Admin":
            pass

        # -------------------------------------------------------------
        # Authorization: Doctor can view any patient's records
        # -------------------------------------------------------------
        elif role == "Doctor":
            pass

        # -------------------------------------------------------------
        # Authorization: Guardian can view only their child's records
        # -------------------------------------------------------------
        elif role == "Guardian":

            guardian_id = current_user["guardian_id"]

            linked_patient = PatientRepository.get_for_guardian(
                patient_id,
                guardian_id,
            )

            if not linked_patient:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to view this patient's records",
                )

        # -------------------------------------------------------------
        # Authorization: Patient can view only their own records
        # -------------------------------------------------------------
        elif role == "Patient":

            if current_user["patient_id"] != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own treatment records",
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view treatment records",
            )

        # -------------------------------------------------------------
        # Fetch treatment history from MongoDB
        # -------------------------------------------------------------
        return PatientTreatmentRecordRepository.list_for_patient(
            patient_id
        )
    #########################################################################
    @staticmethod
    def get_latest_patient_record(
        patient_id: int,
        current_user,
    ):
        # -------------------------------------------------------------
        # Validate that the requested patient exists
        # -------------------------------------------------------------
        patient = PatientRepository.get_by_id(
            patient_id
        )

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        role = current_user.get(
            "role",
            current_user.get("user_type"),
        )

        # -------------------------------------------------------------
        # Authorization: Admin can view any patient's latest record
        # -------------------------------------------------------------
        if role == "Admin":
            pass

        # -------------------------------------------------------------
        # Authorization: Doctor can view any patient's latest record
        # -------------------------------------------------------------
        elif role == "Doctor":
            pass

        # -------------------------------------------------------------
        # Authorization: Guardian can view only their child's record
        # -------------------------------------------------------------
        elif role == "Guardian":

            guardian_id = current_user["guardian_id"]

            linked_patient = PatientRepository.get_for_guardian(
                patient_id,
                guardian_id,
            )

            if not linked_patient:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to view this patient's records",
                )

        # -------------------------------------------------------------
        # Authorization: Patient can view only their own record
        # -------------------------------------------------------------
        elif role == "Patient":

            if current_user["patient_id"] != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own treatment records",
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view treatment records",
            )

        # -------------------------------------------------------------
        # Fetch latest treatment record from MongoDB
        # -------------------------------------------------------------
        record = (
            PatientTreatmentRecordRepository
            .get_latest_for_patient(patient_id)
        )

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No treatment records found for this patient",
            )

        return record

    ##########################################################################
    @staticmethod
    def get_doctor_records(
        doctor_id: int,
        current_user,
    ):
        role = current_user.get(
            "role",
            current_user.get("user_type"),
        )

        # -------------------------------------------------------------
        # Authorization: Admin can view any doctor's records
        # -------------------------------------------------------------
        if role == "Admin":
            pass

        # -------------------------------------------------------------
        # Authorization: Doctor can view only their own records
        # -------------------------------------------------------------
        elif role == "Doctor":

            authenticated_doctor_id = current_user["doctor_id"]

            if authenticated_doctor_id != doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own treatment records",
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin or Doctor can view doctor treatment records",
            )

        # -------------------------------------------------------------
        # Validate that the requested Doctor exists
        # -------------------------------------------------------------
        doctor = DoctorRepository.get_by_id(
            doctor_id
        )

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
            )

        # -------------------------------------------------------------
        # Fetch treatment records for the Doctor
        # -------------------------------------------------------------
        return PatientTreatmentRecordRepository.list_for_doctor(
            doctor_id
        )