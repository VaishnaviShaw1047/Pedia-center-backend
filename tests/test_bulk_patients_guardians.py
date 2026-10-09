
from datetime import date, timedelta

from fastapi.testclient import TestClient
from main import app


TOTAL_RECORDS = 400
client = TestClient(app)

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Arjun", "Ishaan",
    "Rohan", "Kabir", "Dev", "Krishna", "Reyansh",
    "Ananya", "Diya", "Aadhya", "Ira", "Saanvi",
    "Myra", "Kiara", "Anika", "Riya", "Meera",
    "Priya", "Sneha", "Rahul", "Amit", "Neha",
    "Soham", "Tanya", "Ishita", "Ritwik", "Pooja",
]

LAST_NAMES = [
    "Sharma", "Chatterjee", "Banerjee", "Mukherjee",
    "Das", "Sen", "Roy", "Ghosh", "Dutta", "Bose",
    "Kapoor", "Mehta", "Verma", "Reddy", "Patel",
    "Malhotra", "Iyer", "Nair", "Jain", "Sinha",
]

STREETS = [
    "Lake View Road", "Park Street", "Green Park Road",
    "Riverside Avenue", "Station Road", "College Road",
    "Garden Lane", "Central Avenue",
]

LOCATIONS = [
    ("Kolkata", "West Bengal", "Bengali", "700"),
    ("Howrah", "West Bengal", "Bengali", "711"),
    ("Bhubaneswar", "Odisha", "Odia", "751"),
    ("Patna", "Bihar", "Hindi", "800"),
    ("Ranchi", "Jharkhand", "Hindi", "834"),
    ("Guwahati", "Assam", "Assamese", "781"),
    ("Lucknow", "Uttar Pradesh", "Hindi", "226"),
    ("Jaipur", "Rajasthan", "Hindi", "302"),
]

BLOOD_GROUPS = [
    "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"
]

ALLERGIES = [
    "None reported",
    "Pollen allergy reported",
    "Dust allergy reported",
    "Peanut allergy reported",
    "Dairy sensitivity reported",
]

CONDITIONS = [
    "None reported",
    "Asthma reported by guardian",
    "Seasonal allergies reported",
    "Eczema reported by guardian",
    "No known chronic conditions reported",
]

MEDICATIONS = [
    "None reported",
    "Medication history not verified",
    "Fictional test medication entry",
    "Fictional vitamin supplement entry",
]


IMMUNIZATIONS = [
    "Up to date",
    "Pending review",
    "Partially done",
    "Not verified",
    "Unknown",
]

REFERRALS = [
    "Self-referred",
    "Family physician",
    "Community health centre",
    "Pediatric clinic referral",
    "Hospital outpatient department",
]


def unique_name(i: int):
    """Generate distinct first-name and surname combinations."""
    first = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
    last = LAST_NAMES[((i - 1) // len(FIRST_NAMES)) % len(LAST_NAMES)]
    return first, last


def make_registration_payload(i: int):
    guardian_first, guardian_last = unique_name(i)

    # Offset child names so guardian and child names vary independently.
    child_first, child_last = unique_name(i + 173)

    city, state, language, postal_prefix = LOCATIONS[
        (i - 1) % len(LOCATIONS)
    ]

    # Synthetic 10-digit numbers. Use only in a test database.
    mobile_number = f"9{i:09d}"

    dob = date(2012, 1, 1) + timedelta(days=(i * 29) % 3650)

    return {
        "first_name": guardian_first,
        "last_name": guardian_last,
        "relationship_to_child": "Mother" if i % 2 else "Father",
        "mobile_number": mobile_number,
        "password": "TestPassword123",
        "email": f"guardian{i:03d}@example.com",
        "address_line1": (
            f"{10 + i} {STREETS[(i - 1) % len(STREETS)]}"
        ),
        "address_line2": f"Apartment {1 + i % 20}",
        "city": city,
        "state": state,
        "pincode": f"{postal_prefix}{i % 1000:03d}",
        "preferred_language": language,
        "terms_accepted": True,
        "health_data_consent": True,
        "children": [
            {
                "first_name": child_first,
                "last_name": child_last,
                "date_of_birth": dob.isoformat(),
                "gender": "Male" if i % 2 else "Female",
                "abha_id": None,
                "aadhaar_number": None,
                "blood_group": BLOOD_GROUPS[(i - 1) % len(BLOOD_GROUPS)],
                "known_allergies": ALLERGIES[
                    (i - 1) % len(ALLERGIES)
                ],
                "existing_conditions": CONDITIONS[
                    (i - 1) % len(CONDITIONS)
                ],
                "current_medications": MEDICATIONS[
                    (i - 1) % len(MEDICATIONS)
                ],
                "immunization_status": IMMUNIZATIONS[
                    (i - 1) % len(IMMUNIZATIONS)
                ],
                "referred_by": REFERRALS[
                    (i - 1) % len(REFERRALS)
                ],
            }
        ],
    }


def test_create_400_unique_guardians_and_patients():
    guardian_ids = set()
    patient_ids = set()
    mrns = set()
    mobile_numbers = set()
    guardian_names = set()
    patient_names = set()

    for i in range(1, TOTAL_RECORDS + 1):
        payload = make_registration_payload(i)
        child = payload["children"][0]

        response = client.post(
            "/api/v1/registration",
            json=payload,
        )

        assert response.status_code == 201, (
            f"Registration {i} failed: "
            f"{response.status_code} - {response.text}"
        )

        data = response.json()

        assert len(data["patients"]) == 1, (
            f"Expected one patient for registration {i}"
        )

        patient = data["patients"][0]

        guardian_id = data["guardian_id"]
        patient_id = patient["patient_id"]
        mrn = patient["mrn"]

        guardian_name = (
            payload["first_name"],
            payload["last_name"],
        )
        patient_name = (
            child["first_name"],
            child["last_name"],
        )

        assert guardian_id not in guardian_ids, (
            f"Duplicate guardian ID: {guardian_id}"
        )
        assert patient_id not in patient_ids, (
            f"Duplicate patient ID: {patient_id}"
        )
        assert mrn not in mrns, f"Duplicate MRN: {mrn}"
        assert payload["mobile_number"] not in mobile_numbers
        assert guardian_name not in guardian_names
        assert patient_name not in patient_names

        guardian_ids.add(guardian_id)
        patient_ids.add(patient_id)
        mrns.add(mrn)
        mobile_numbers.add(payload["mobile_number"])
        guardian_names.add(guardian_name)
        patient_names.add(patient_name)

        if i % 50 == 0:
            print(f"Registered {i}/{TOTAL_RECORDS}")

    assert len(guardian_ids) == TOTAL_RECORDS
    assert len(patient_ids) == TOTAL_RECORDS
    assert len(mrns) == TOTAL_RECORDS
    assert len(mobile_numbers) == TOTAL_RECORDS
    assert len(guardian_names) == TOTAL_RECORDS
    assert len(patient_names) == TOTAL_RECORDS

    print(f"\nSuccessfully created {TOTAL_RECORDS} guardians.")
    print(f"Successfully created {TOTAL_RECORDS} patients.")
    print("Guardian and patient names are unique within this batch.")
    print("Guardian IDs, patient IDs, and MRNs are unique within this batch.")