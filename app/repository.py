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
    PatientTreatmentRecordRepository
"""

from datetime import datetime, time

from app.mongodb import (
    users_collection,
    guardians_collection,
    patients_collection,
    doctors_collection,
    appointments_collection,
)


# =====================================================================
#  GUARDIAN
# =====================================================================
class GuardianRepository:

    @staticmethod
    def get_by_mobile(mobile_number: str):
        return guardians_collection.find_one(
            {"mobile_number": mobile_number},
            {"_id": 0},
        )

    @staticmethod
    def get_by_id(guardian_id: int):
        return guardians_collection.find_one(
            {"guardian_id": guardian_id},
            {"_id": 0},
        )

    @staticmethod
    def add(guardian: dict):
        guardians_collection.insert_one(guardian)
        return guardian

    @staticmethod
    def update(guardian_id: int, update_data: dict):
        guardians_collection.update_one(
            {"guardian_id": guardian_id},
            {"$set": update_data},
        )

        return GuardianRepository.get_by_id(guardian_id)

    @staticmethod
    def delete(guardian_id: int):
        return guardians_collection.delete_one(
            {"guardian_id": guardian_id},
        )

    @staticmethod
    def commit():
        pass

    @staticmethod
    def rollback():
        pass


# =====================================================================
#  PATIENT
# =====================================================================
class PatientRepository:

    @staticmethod
    def add(patient: dict):
        patients_collection.insert_one(patient)
        return patient

    @staticmethod
    def get_by_mrn(mrn: str):
        return patients_collection.find_one(
            {"mrn": mrn},
            {"_id": 0},
        )

    @staticmethod
    def get_for_guardian(
        patient_id: int,
        guardian_id: int,
    ):
        return patients_collection.find_one(
            {
                "patient_id": patient_id,
                "guardian_id": guardian_id,
                "is_active": True,
            },
            {"_id": 0},
        )

    @staticmethod
    def build_list_query(search: str | None):
        query = {
            "is_active": True
        }

    @staticmethod
    def build_list_query(search: str | None):
        query = {
            "is_active": True
        }

    @staticmethod
    def build_list_query(search: str | None):
        query = {
            "is_active": True
        }

        if search:
            search = search.strip()

            query["$or"] = [
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}},
                {"mrn": {"$regex": search, "$options": "i"}},
                {
                    "guardian_mobile_number": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
            ]

        return query

    @staticmethod
    def count(query) -> int:
        return patients_collection.count_documents(query)

    @staticmethod
    def page(
        query,
        page: int,
        page_size: int,
    ):
        return list(
            patients_collection.find(
                query,
                {"_id": 0},
            )
            .sort("patient_id", -1)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )

    @staticmethod
    def update(
        patient_id: int,
        update_data: dict,
    ):
        patients_collection.update_one(
            {"patient_id": patient_id},
            {"$set": update_data},
        )

        return patients_collection.find_one(
            {"patient_id": patient_id},
            {"_id": 0},
        )

    @staticmethod
    def delete(patient_id: int):
        return patients_collection.delete_one(
            {"patient_id": patient_id}
        )

    @staticmethod
    def commit():
        pass

    @staticmethod
    def refresh(patient):
        return patient


# =====================================================================
#  DOCTOR (and embedded availability)
# =====================================================================
class DoctorRepository:

    @staticmethod
    def get_by_registration_no(registration_no: str):
        return doctors_collection.find_one(
            {"registration_no": registration_no},
            {"_id": 0},
        )

    @staticmethod
    def get_by_id(doctor_id: int):
        return doctors_collection.find_one(
            {"doctor_id": doctor_id},
            {"_id": 0},
        )

    @staticmethod
    def get_active_by_id(doctor_id: int):
        return doctors_collection.find_one(
            {
                "doctor_id": doctor_id,
                "is_active": True,
            },
            {"_id": 0},
        )

    @staticmethod
    def get_by_staff_id(staff_id: str):
        return doctors_collection.find_one(
            {"staff_id": staff_id},
            {"_id": 0},
        )

    @staticmethod
    def search(
        specialty: str | None = None,
        language: str | None = None,
        max_fee: int | None = None,
        day: str | None = None,
        text: str | None = None,
    ):
        query = {"is_active": True}

        if specialty:
            query["specialty"] = {
                "$regex": specialty.strip(),
                "$options": "i",
            }

        if language:
            query["languages"] = {
                "$regex": language.strip(),
                "$options": "i",
            }

        if max_fee is not None:
            query["consultation_fee"] = {"$lte": max_fee}

        if day:
            query["available_days"] = {
                "$regex": day.strip(),
                "$options": "i",
            }

        if text:
            term = text.strip()

            query["$or"] = [
                {
                    "first_name": {
                        "$regex": term,
                        "$options": "i",
                    }
                },
                {
                    "last_name": {
                        "$regex": term,
                        "$options": "i",
                    }
                },
                {
                    "specialty": {
                        "$regex": term,
                        "$options": "i",
                    }
                },
            ]

        return list(
            doctors_collection.find(
                query,
                {"_id": 0},
            )
            .sort("experience_years", -1)
        )

    @staticmethod
    def specialty_counts():
        pipeline = [
            {
                "$match": {
                    "is_active": True,
                }
            },
            {
                "$group": {
                    "_id": "$specialty",
                    "doctor_count": {
                        "$sum": 1,
                    },
                }
            },
            {
                "$sort": {
                    "_id": 1,
                }
            },
        ]

        return [
            {
                "specialty": item["_id"],
                "doctor_count": item["doctor_count"],
            }
            for item in doctors_collection.aggregate(pipeline)
        ]

    @staticmethod
    def add(doctor: dict):
        doctors_collection.insert_one(doctor)
        return doctor

    # ---------- embedded availability ----------

    @staticmethod
    def _time_to_string(value):
        """Convert datetime.time to a BSON-safe HH:MM:SS string."""
        if isinstance(value, time):
            return value.strftime("%H:%M:%S")

        return value

    @staticmethod
    def _time_from_string(value):
        """Convert stored HH:MM[:SS] strings back to datetime.time."""
        if isinstance(value, time):
            return value

        if isinstance(value, str):
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(value, fmt).time()
                except ValueError:
                    continue

        return value

    @staticmethod
    def _normalize_availability(item: dict):
        item = dict(item)

        if "start_time" in item:
            item["start_time"] = DoctorRepository._time_from_string(
                item["start_time"]
            )

        if "end_time" in item:
            item["end_time"] = DoctorRepository._time_from_string(
                item["end_time"]
            )

        return item

    @staticmethod
    def find_overlapping_availability(
        doctor_id: int,
        day_of_week: int,
        start_time,
        end_time,
    ):
        doctor = doctors_collection.find_one(
            {
                "doctor_id": doctor_id,
                "is_active": True,
            },
            {
                "_id": 0,
                "availability": 1,
            },
        )

        if not doctor:
            return None

        for item in doctor.get("availability", []):

            existing_start = DoctorRepository._time_from_string(
                item.get("start_time")
            )

            existing_end = DoctorRepository._time_from_string(
                item.get("end_time")
            )

            if (
                item.get("day_of_week") == day_of_week
                and item.get("is_active", True)
                and existing_start < end_time
                and existing_end > start_time
            ):
                return DoctorRepository._normalize_availability(item)

        return None

    @staticmethod
    def get_availability_for_day(
        doctor_id: int,
        weekday: int,
    ):
        doctor = doctors_collection.find_one(
            {
                "doctor_id": doctor_id,
                "is_active": True,
            },
            {
                "_id": 0,
                "availability": 1,
            },
        )

        if not doctor:
            return []

        availability = [
            DoctorRepository._normalize_availability(item)
            for item in doctor.get("availability", [])
            if (
                item.get("day_of_week") == weekday
                and item.get("is_active", True)
            )
        ]

        return sorted(
            availability,
            key=lambda item: item.get("start_time"),
        )

    @staticmethod
    def list_availability(doctor_id: int):
        doctor = doctors_collection.find_one(
            {
                "doctor_id": doctor_id,
                "is_active": True,
            },
            {
                "_id": 0,
                "availability": 1,
            },
        )

        if not doctor:
            return []

        availability = [
            DoctorRepository._normalize_availability(item)
            for item in doctor.get("availability", [])
            if item.get("is_active", True)
        ]

        return sorted(
            availability,
            key=lambda item: (
                item.get("day_of_week", 0),
                item.get("start_time"),
            ),
        )

    @staticmethod
    def add_availability(
        doctor_id: int,
        availability: dict,
    ):
        availability = dict(availability)

        # Generate availability ID
        doctor = doctors_collection.find_one(
            {"doctor_id": doctor_id},
            {
                "_id": 0,
                "availability": 1,
            },
        )

        existing = doctor.get("availability", []) if doctor else []

        next_availability_id = (
            max(
                (
                    item.get("availability_id", 0)
                    for item in existing
                ),
                default=0,
            )
            + 1
        )

        availability["availability_id"] = next_availability_id
        availability["doctor_id"] = doctor_id

        # Convert datetime.time to MongoDB-safe strings
        if "start_time" in availability:
            availability["start_time"] = (
                DoctorRepository._time_to_string(
                    availability["start_time"]
                )
            )

        if "end_time" in availability:
            availability["end_time"] = (
                DoctorRepository._time_to_string(
                    availability["end_time"]
                )
            )

        doctors_collection.update_one(
            {"doctor_id": doctor_id},
            {
                "$push": {
                    "availability": availability
                }
            },
        )

        return DoctorRepository._normalize_availability(
            availability
        )

    # ---------- appointments ----------

    @staticmethod
    def booked_times_on(
        doctor_id: int,
        day_start,
        day_end,
    ) -> set:
        rows = appointments_collection.find(
            {
                "doctor_id": doctor_id,
                "scheduled_at": {
                    "$gte": day_start,
                    "$lte": day_end,
                },
                "status": {
                    "$in": [
                        "requested",
                        "confirmed",
                    ],
                },
            },
            {
                "_id": 0,
                "scheduled_at": 1,
            },
        )

        return {
            row["scheduled_at"]
            for row in rows
            if row.get("scheduled_at") is not None
        }

    @staticmethod
    def commit():
        pass

    @staticmethod
    def refresh(obj):
        return obj


# =====================================================================
#  APPOINTMENT
# =====================================================================
class AppointmentRepository:

    @staticmethod
    def get_active_doctor(doctor_id: int):
        return DoctorRepository.get_active_by_id(doctor_id)

    @staticmethod
    def get_patient_for_guardian(
        patient_id: int,
        guardian_id: int,
    ):
        return PatientRepository.get_for_guardian(
            patient_id,
            guardian_id,
        )

    @staticmethod
    def get_availability_rules(
        doctor_id: int,
        weekday: int,
    ):
        return DoctorRepository.get_availability_for_day(
            doctor_id,
            weekday,
        )

    # ---------- conflict checks ----------

    @staticmethod
    def find_slot_conflict(
        doctor_id: int,
        when: datetime,
    ):
        return appointments_collection.find_one(
            {
                "doctor_id": doctor_id,
                "scheduled_at": when,
                "status": {
                    "$in": [
                        "requested",
                        "confirmed",
                    ],
                },
            },
            {"_id": 0},
        )

    @staticmethod
    def find_same_day_for_patient(
        patient_id: int,
        day: datetime,
    ):
        day_start = datetime.combine(
            day.date(),
            time.min,
        )

        day_end = datetime.combine(
            day.date(),
            time.max,
        )

        return appointments_collection.find_one(
            {
                "patient_id": patient_id,
                "scheduled_at": {
                    "$gte": day_start,
                    "$lte": day_end,
                },
                "status": {
                    "$in": [
                        "requested",
                        "confirmed",
                    ],
                },
            },
            {"_id": 0},
        )

    # ---------- reads ----------

    @staticmethod
    def _with_related_data(
        appointment: dict | None,
    ):
        """
        Add doctor and patient information to an appointment response.

        MongoDB does not perform SQLAlchemy joinedload, so the repository
        resolves the related doctor and patient documents explicitly.
        """

        if not appointment:
            return None

        appointment = dict(appointment)

        # Get related doctor
        doctor = doctors_collection.find_one(
            {
                "doctor_id": appointment.get("doctor_id"),
            },
            {"_id": 0},
        )

        # Get related patient
        patient = patients_collection.find_one(
            {
                "patient_id": appointment.get("patient_id"),
            },
            {"_id": 0},
        )

        # Keep the complete related documents
        appointment["doctor"] = doctor
        appointment["patient"] = patient

        # Add fields expected by AppointmentResponse
        appointment["doctor_name"] = (
            f"{doctor['first_name']} {doctor['last_name']}"
            if doctor
            else None
        )

        appointment["patient_name"] = (
            f"{patient['first_name']} {patient['last_name']}"
            if patient
            else None
        )

        appointment["mrn"] = (
            patient.get("mrn")
            if patient
            else None
        )

        return appointment

    @staticmethod
    def add(appointment: dict):
        appointments_collection.insert_one(
            appointment
        )

        return appointment

    @staticmethod
    def get_by_ref_for_guardian(
        ref: str,
        guardian_id: int,
    ):
        appointment = appointments_collection.find_one(
            {
                "appointment_ref": ref,
                "guardian_id": guardian_id,
            },
            {"_id": 0},
        )

        return AppointmentRepository._with_related_data(
            appointment
        )

    @staticmethod
    def list_for_guardian(
        guardian_id: int,
        upcoming_only: bool,
    ):
        query = {
            "guardian_id": guardian_id,
        }

        if upcoming_only:
            query.update(
                {
                    "scheduled_at": {
                        "$gte": datetime.now(),
                    },
                    "status": {
                        "$in": [
                            "requested",
                            "confirmed",
                        ],
                    },
                }
            )

        appointments = list(
            appointments_collection.find(
                query,
                {"_id": 0},
            ).sort(
                "scheduled_at",
                1,
            )
        )

        return [
            AppointmentRepository._with_related_data(item)
            for item in appointments
        ]

    # ---------- writes ----------

    @staticmethod
    def commit():
        pass

    @staticmethod
    def rollback():
        pass

    @staticmethod
    def refresh(
        appointment: dict,
    ):
        if not appointment:
            return appointment

        appointment_id = appointment.get(
            "appointment_id"
        )

        if appointment_id is None:
            return appointment

        refreshed = appointments_collection.find_one(
            {
                "appointment_id": appointment_id,
            },
            {"_id": 0},
        )

        return (
            AppointmentRepository._with_related_data(refreshed)
            if refreshed
            else appointment
        )


# =====================================================================
#  USER
# =====================================================================
class UserRepository:

    @staticmethod
    def get_by_id(user_id: int):
        return users_collection.find_one(
            {"user_id": user_id},
            {"_id": 0},
        )

    @staticmethod
    def get_by_username(username: str):
        return users_collection.find_one(
            {"username": username},
            {"_id": 0},
        )

    @staticmethod
    def list_users(
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        query = {}

        if search:
            search = search.strip()

            query = {
                "$or": [
                    {
                        "first_name": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "last_name": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "username": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                ]
            }

        total = users_collection.count_documents(
            query
        )

        users = list(
            users_collection.find(
                query,
                {"_id": 0},
            )
            .sort(
                "user_id",
                -1,
            )
            .skip(
                (page - 1) * page_size
            )
            .limit(page_size)
        )

        return total, users

    @staticmethod
    def adduser(user: dict):
        users_collection.insert_one(user)
        return user

    @staticmethod
    def update_user(
        user_id: int,
        update_data: dict,
    ):
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data},
        )

        return UserRepository.get_by_id(
            user_id
        )

    @staticmethod
    def delete_user(user_id: int):
        return users_collection.delete_one(
            {"user_id": user_id}
        )

    @staticmethod
    def commit():
        pass

    @staticmethod
    def rollback():
        pass