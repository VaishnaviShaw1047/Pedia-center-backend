
import random
from datetime import time

from faker import Faker
from pymongo import ASCENDING

from app.mongodb import doctors_collection

fake = Faker("en_IN")
Faker.seed(2026)
random.seed(2026)

SPECIALTIES = [
    "Pediatrics",
    "Neonatology",
    "Pediatric Cardiology",
    "Pediatric Neurology",
    "Pediatric Endocrinology",
    "Pediatric Gastroenterology",
    "Pediatric Pulmonology",
    "Pediatric Nephrology",
    "Pediatric Dermatology",
    "Pediatric Surgery",
]

QUALIFICATIONS = [
    "MBBS, MD (Pediatrics)",
    "MBBS, DCH",
    "MBBS, DNB (Pediatrics)",
    "MBBS, MD",
    "MBBS, MS",
]

LANGUAGES = [
    "English, Hindi",
    "English, Bengali, Hindi",
    "English, Tamil",
    "English, Telugu, Hindi",
    "English, Marathi, Hindi",
    "English, Kannada",
    "English, Gujarati, Hindi",
    "English, Malayalam",
]

DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


def make_availability(days):
    slots = []
    for day in days:
        start_hour = random.choice([9, 10, 11])
        end_hour = random.choice([15, 16, 17, 18])

        slots.append({
            "day_of_week": DAYS.index(day) + 1,
            "start_time": f"{start_hour:02d}:00:00",
            "end_time": f"{end_hour:02d}:00:00",
            "slot_minutes": 30,
            "is_active": True,
        })

    return slots


def main():
    doctors = list(
        doctors_collection.find({}).sort("doctor_id", ASCENDING)
    )

    if len(doctors) != 39:
        raise RuntimeError(
            f"Expected 39 doctors; found {len(doctors)}. No changes made."
        )

    used_names = set()
    used_emails = set()
    updated = 0

    for doctor in doctors:
        # Generate a distinct name for each doctor.
        for _ in range(100):
            first_name = fake.first_name()
            last_name = fake.last_name()
            name_key = (first_name.lower(), last_name.lower())
            if name_key not in used_names:
                used_names.add(name_key)
                break
        else:
            raise RuntimeError("Could not generate unique names.")

        # Unique fictional contact information.
        email = (
            f"doctor{doctor['doctor_id']}."
            f"{first_name.lower()}.{last_name.lower()}@example.com"
        )
        while email in used_emails:
            email = fake.uuid4() + "@example.com"
        used_emails.add(email)

        days = sorted(
            random.sample(DAYS, k=random.randint(3, 5)),
            key=DAYS.index,
        )

        changes = {
            "first_name": first_name,
            "last_name": last_name,
            "registration_no": (
                f"SYNTHETIC-TEST-{doctor['doctor_id']:04d}"
            ),
            "qualification": random.choice(QUALIFICATIONS),
            "specialty": random.choice(SPECIALTIES),
            "experience_years": random.randint(1, 30),
            "languages": random.choice(LANGUAGES),
            "consultation_fee": random.choice(
                [300, 400, 500, 600, 700, 800, 1000]
            ),
            "available_days": ",".join(days),
            "availability": make_availability(days),
        }

        # Preserve doctor_id, staff_id, passwords, email, phone,
        # active status, and any other fields not listed above.
        result = doctors_collection.update_one(
            {"doctor_id": doctor["doctor_id"]},
            {"$set": changes},
        )

        if result.matched_count != 1:
            raise RuntimeError(
                f"Could not update doctor_id={doctor['doctor_id']}"
            )

        updated += result.modified_count
        print(
            f"Updated doctor_id={doctor['doctor_id']}: "
            f"{first_name} {last_name} — {changes['specialty']}"
        )

    print(f"\nFinished. Profiles modified: {updated}")
    print("Doctor IDs and staff IDs were preserved.")
    print("Registration numbers are explicitly synthetic test values.")


if __name__ == "__main__":
    main()
