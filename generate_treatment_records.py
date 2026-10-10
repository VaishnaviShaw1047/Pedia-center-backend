
from datetime import datetime, timedelta
import random

from app.mongodb import (
    patients_collection,
    doctors_collection,
    appointments_collection,
    treatment_records_collection,
)

# --------------------------------------------------
# CONFIGURATION
# Development/test data only. Not real medical records.
# --------------------------------------------------

random.seed()

NOW = datetime.now()
DAYS_BACK = 180

CLINICAL_SCENARIOS = [
    {
        "diagnosis": "Acute upper respiratory tract infection",
        "medications": [],
        "plan": (
            "Supportive care, adequate fluids, and rest were discussed. "
            "Monitor symptoms and arrange reassessment if they persist "
            "or worsen."
        ),
        "notes": (
            "The child was evaluated for upper respiratory symptoms. "
            "The caregiver received counselling on hydration, rest, "
            "symptom monitoring, and warning signs."
        ),
    },
    {
        "diagnosis": "Viral fever",
        "medications": [
            {
                "medication_name": "Paracetamol",
                "dosage": "Weight-based dose to be determined by clinician",
                "frequency": "As needed for fever or pain, if prescribed",
                "duration": "As directed by the treating clinician",
                "instructions": (
                    "Use only according to the treating clinician's "
                    "instructions."
                ),
            }
        ],
        "plan": (
            "Monitor temperature, hydration, oral intake, and activity. "
            "Arrange clinical review if symptoms persist or worsen."
        ),
        "notes": (
            "The consultation addressed fever and symptom monitoring. "
            "The caregiver received counselling on hydration, temperature "
            "monitoring, and signs requiring reassessment."
        ),
    },
    {
        "diagnosis": "Acute gastroenteritis",
        "medications": [
            {
                "medication_name": "Oral rehydration solution",
                "dosage": "Small, frequent amounts as tolerated",
                "frequency": "As needed to maintain hydration",
                "duration": "As clinically indicated",
                "instructions": (
                    "Follow appropriate oral rehydration guidance and "
                    "monitor for signs of dehydration."
                ),
            }
        ],
        "plan": (
            "Monitor fluid intake, urine output, and general condition. "
            "Arrange reassessment for dehydration, persistent vomiting, "
            "blood in stool, or worsening symptoms."
        ),
        "notes": (
            "The child was assessed for gastrointestinal symptoms. "
            "The caregiver received guidance on fluid replacement, "
            "hydration monitoring, and warning signs."
        ),
    },
    {
        "diagnosis": "Allergic rhinitis",
        "medications": [],
        "plan": (
            "Discuss possible triggers and symptom monitoring. "
            "Review treatment options with a clinician based on the "
            "child's age and clinical assessment."
        ),
        "notes": (
            "The consultation addressed nasal allergy symptoms and "
            "possible triggers. The caregiver received counselling "
            "on symptom monitoring and follow-up."
        ),
    },
    {
        "diagnosis": "Acute pharyngitis",
        "medications": [],
        "plan": (
            "Monitor throat discomfort, fluid intake, and general "
            "condition. Arrange reassessment if symptoms worsen "
            "or swallowing becomes difficult."
        ),
        "notes": (
            "The consultation addressed throat discomfort and associated "
            "symptoms. Supportive care, hydration, and warning signs "
            "were discussed with the caregiver."
        ),
    },
    {
        "diagnosis": "Constipation",
        "medications": [],
        "plan": (
            "Discuss age-appropriate dietary fibre, fluid intake, "
            "and toileting routines. Review persistent symptoms "
            "with the treating clinician."
        ),
        "notes": (
            "The caregiver discussed the child's bowel habits and "
            "dietary routine. Guidance was provided on age-appropriate "
            "nutrition, hydration, and symptom monitoring."
        ),
    },
    {
        "diagnosis": "Dermatitis",
        "medications": [],
        "plan": (
            "Review skin-care practices and potential irritants. "
            "Arrange clinical review for worsening rash, pain, "
            "discharge, or persistent symptoms."
        ),
        "notes": (
            "The consultation addressed a skin complaint. The caregiver "
            "received guidance on gentle skin care, possible irritants, "
            "and symptoms requiring reassessment."
        ),
    },
    {
        "diagnosis": "Routine pediatric follow-up",
        "medications": [],
        "plan": (
            "Review growth, nutrition, activity, and age-appropriate "
            "preventive care. Schedule further review according to "
            "clinical needs."
        ),
        "notes": (
            "A routine pediatric review was documented. The discussion "
            "covered general wellbeing, nutrition, growth monitoring, "
            "and preventive care."
        ),
    },
    {
        "diagnosis": "Nutritional assessment",
        "medications": [],
        "plan": (
            "Review dietary variety, growth measurements, and age-"
            "appropriate nutritional needs. Arrange further assessment "
            "if growth or feeding concerns are identified."
        ),
        "notes": (
            "The consultation focused on nutritional history and general "
            "dietary practices. The caregiver received guidance on "
            "balanced nutrition and appropriate growth monitoring."
        ),
    },
]


def next_numeric_id(collection, field):
    """Return the next available integer ID."""
    values = collection.distinct(field)
    valid_values = [
        value for value in values
        if isinstance(value, int) and not isinstance(value, bool)
    ]
    return max(valid_values, default=0) + 1


def get_patient_name(patient):
    return (
        f'{patient["first_name"]} {patient["last_name"]}'
    ).strip()


def get_doctor_name(doctor):
    return (
        f'{doctor["first_name"]} {doctor["last_name"]}'
    ).strip()


def create_visit_datetime():
    """Generate a past test appointment date and time."""
    visit_date = NOW - timedelta(
        days=random.randint(1, DAYS_BACK)
    )
    return visit_date.replace(
        hour=random.choice([9, 10, 11, 14, 15]),
        minute=random.choice([0, 30]),
        second=0,
        microsecond=0,
    )


def main():
    patients = list(
        patients_collection.find(
            {},
            {
                "_id": 0,
                "patient_id": 1,
                "first_name": 1,
                "last_name": 1,
                "guardian_id": 1,
            },
        ).sort("patient_id", 1)
    )

    doctors = list(
        doctors_collection.find(
            {"is_active": {"$ne": False}},
            {
                "_id": 0,
                "doctor_id": 1,
                "first_name": 1,
                "last_name": 1,
                "is_active": 1,
            },
        ).sort("doctor_id", 1)
    )

    if not patients:
        raise RuntimeError("No patients found.")
    if not doctors:
        raise RuntimeError("No active doctors found.")

    patients = [
        p for p in patients
        if p.get("patient_id") is not None
        and p.get("first_name")
        and p.get("last_name")
    ]

    doctors = [
        d for d in doctors
        if d.get("doctor_id") is not None
        and d.get("first_name")
        and d.get("last_name")
    ]

    if not patients or not doctors:
        raise RuntimeError(
            "Patients or doctors are missing required IDs or names."
        )

    existing_records = list(
        treatment_records_collection.find(
            {},
            {"_id": 0, "patient_id": 1},
        )
    )

    already_recorded = {
        record["patient_id"]
        for record in existing_records
        if record.get("patient_id") is not None
    }

    next_record_id = next_numeric_id(
        treatment_records_collection,
        "treatment_record_id",
    )

    next_appointment_id = next_numeric_id(
        appointments_collection,
        "appointment_id",
    )

    # Index existing appointments by patient and doctor.
    appointment_lookup = {}

    for appointment in appointments_collection.find({}, {"_id": 0}):
        key = (
            appointment.get("patient_id"),
            appointment.get("doctor_id"),
        )
        appointment_lookup.setdefault(key, appointment)

    records_to_insert = []
    appointments_to_insert = []
    skipped = 0

    for patient in patients:
        patient_id = patient["patient_id"]

        # Avoid intentionally creating duplicate records on reruns.
        if patient_id in already_recorded:
            skipped += 1
            continue

        # Choose an existing doctor document.
        doctor = random.choice(doctors)
        doctor_id = doctor["doctor_id"]
        doctor_name = get_doctor_name(doctor)

        key = (patient_id, doctor_id)
        appointment = appointment_lookup.get(key)

        if appointment:
            appointment_id = appointment.get("appointment_id")
            visit_date = appointment.get("scheduled_at")

            if not isinstance(visit_date, datetime):
                visit_date = create_visit_datetime()

        else:
            # Create a linked test appointment.
            appointment_id = next_appointment_id
            next_appointment_id += 1

            visit_date = create_visit_datetime()

            appointment_document = {
                "appointment_id": appointment_id,
                "appointment_ref": (
                    f"APT-TEST-{appointment_id:06d}"
                ),
                "doctor_id": doctor_id,
                "patient_id": patient_id,
                "guardian_id": patient.get("guardian_id"),
                "scheduled_at": visit_date,
                "duration_minutes": 30,
                "status": "completed",
                "reason_for_visit": "Development test consultation",
                "data_type": "DEMO_TEST_DATA",
            }

            appointments_to_insert.append(appointment_document)
            appointment_lookup[key] = appointment_document

        scenario = random.choice(CLINICAL_SCENARIOS)

        created_at = visit_date + timedelta(minutes=30)
        follow_up_date = visit_date + timedelta(
            days=random.choice([7, 10, 14])
        )

        record = {
            "treatment_record_id": next_record_id,
            "patient_id": patient_id,
            "patient_name": get_patient_name(patient),
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "appointment_id": appointment_id,
            "visit_date": visit_date,
            "diagnosis": scenario["diagnosis"],
            "medications": [
                dict(medication)
                for medication in scenario["medications"]
            ],
            "treatment_plan": scenario["plan"],
            "follow_up_date": follow_up_date,
            "clinical_notes": scenario["notes"],
            "record_status": "completed",
            "created_at": created_at,
            "updated_at": created_at,
            "data_type": "DEMO_TEST_DATA",
        }

        records_to_insert.append(record)
        next_record_id += 1

    # Validate references before previewing or inserting.
    doctor_ids = {doctor["doctor_id"] for doctor in doctors}
    patient_ids = {patient["patient_id"] for patient in patients}

    for record in records_to_insert:
        if record["patient_id"] not in patient_ids:
            raise RuntimeError("Invalid patient reference detected.")

        if record["doctor_id"] not in doctor_ids:
            raise RuntimeError("Invalid doctor reference detected.")

        if record["appointment_id"] is None:
            raise RuntimeError("Missing appointment reference detected.")

    print("=" * 55)
    print("TREATMENT RECORD TEST-DATA GENERATOR")
    print("=" * 55)
    print("Patients available:", len(patients))
    print("Active doctors available:", len(doctors))
    print("Existing treatment records:", len(existing_records))
    print("New appointments to create:", len(appointments_to_insert))
    print("New treatment records to create:", len(records_to_insert))
    print("Patients skipped:", skipped)

    if records_to_insert:
        print("\nSAMPLE TREATMENT RECORD:")
        print(records_to_insert[0])

    print(
        "\nNOTE: These records contain fictional development data, "
        "not verified medical histories or prescriptions."
    )

    confirmation = input(
        "\nType CREATE to insert these documents into MongoDB: "
    ).strip()

    if confirmation != "CREATE":
        print("Cancelled. No documents inserted.")
        return

    # Insert appointments first so treatment records can reference them.
    if appointments_to_insert:
        appointments_collection.insert_many(appointments_to_insert)

    if records_to_insert:
        treatment_records_collection.insert_many(records_to_insert)

    print("\nGeneration completed successfully.")
    print("Appointments inserted:", len(appointments_to_insert))
    print("Treatment records inserted:", len(records_to_insert))
    print(
        "Total treatment records now:",
        treatment_records_collection.count_documents({}),
    )
    print(
        "Total appointments now:",
        appointments_collection.count_documents({}),
    )


if __name__ == "__main__":
    main()
