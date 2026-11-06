"""
Pedia Centre API smoke test.

Logs in as a guardian, an admin and a doctor, walks through the real booking
flow, and checks that protected endpoints reject people who should not get in.

Run from the backend folder, with the venv active and the server running:

    python -m pip install requests

    $env:ADMIN_USERNAME = "your-admin-username"
    $env:ADMIN_PASSWORD = "your-admin-password"
    python tests/api_smoke_test.py

Optional environment variables:
    API_BASE          default http://127.0.0.1:8000/api/v1
    GUARDIAN_MOBILE   default 9000000001
    GUARDIAN_PASSWORD default TestPassword123
    DOCTOR_STAFF_ID   only used when ADMIN_* is not set
    DOCTOR_PASSWORD   default DoctorTest@123

The test creates data: one guardian with one child, one doctor (with weekly
availability), one appointment, one treatment record and one temporary user
(deleted at the end). Test names start with "Smoke" so you can find them.
"""

import os
import random
import string
import sys
from datetime import date, datetime, timedelta

import requests

BASE = os.getenv("API_BASE", "http://127.0.0.1:8000/api/v1")
SEED_MOBILE = os.getenv("GUARDIAN_MOBILE", "9000000001")
SEED_PASSWORD = os.getenv("GUARDIAN_PASSWORD", "TestPassword123")
ADMIN_USER = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "")
DOCTOR_STAFF_ID = os.getenv("DOCTOR_STAFF_ID", "")
DOCTOR_PASS = os.getenv("DOCTOR_PASSWORD", "DoctorTest@123")

results = []


def rnd(n, chars=string.digits):
    return "".join(random.choices(chars, k=n))


def call(method, path, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        return requests.request(
            method, f"{BASE}{path}", headers=headers, timeout=20, **kwargs
        )
    except requests.RequestException as exc:
        print(f"  !! request failed: {exc}")
        return None


def data(resp):
    try:
        return resp.json()
    except Exception:
        return None


def check(name, resp, ok=(200,)):
    status = resp.status_code if resp is not None else "no response"
    passed = resp is not None and resp.status_code in ok
    results.append((name, passed))
    print(f"  [{'PASS' if passed else 'FAIL'}] {name} -> {status}")
    if not passed and resp is not None:
        print(f"         {resp.text[:200]}")
    return resp


def record(name, passed):
    results.append((name, passed))
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")


def denied(name, method, path, token=None, **kwargs):
    """The request must be refused with 401 or 403."""
    resp = call(method, path, token=token, **kwargs)
    check(name, resp, ok=(401, 403))


def section(title):
    print(f"\n=== {title} ===")


def doctor_payload(temp_password):
    return {
        "first_name": "Smoke",
        "last_name": "Doctor" + rnd(3),
        "registration_no": "SMK" + rnd(8),
        "qualification": "MBBS, MD",
        "specialty": "Pediatrics",
        "experience_years": 5,
        "languages": "English,Bengali",
        "consultation_fee": 500,
        "available_days": "Mon,Tue,Wed,Thu,Fri",
        "mobile_number": None,
        "email": None,
        "temporary_password": temp_password,
    }


def find_slot(doctor_ids):
    for doctor_id in doctor_ids:
        for offset in range(1, 15):
            day = (date.today() + timedelta(days=offset)).isoformat()
            resp = call("GET", f"/doctors/{doctor_id}/slots", params={"date": day})
            if resp is not None and resp.status_code == 200:
                slots = (data(resp) or {}).get("slots", [])
                if slots:
                    return doctor_id, day, slots[0]
    return None


def run():
    # ------------------------------------------------------------------
    section("Public endpoints")
    check("GET /doctors/specialties", call("GET", "/doctors/specialties"))
    resp = check("GET /doctors/available", call("GET", "/doctors/available"))
    doctors = data(resp) or []
    if doctors:
        check("GET /doctors/{id}", call("GET", f"/doctors/{doctors[0]['doctor_id']}"))

    # ------------------------------------------------------------------
    section("Guardian registration and login")
    check(
        "Wrong password is rejected",
        call("POST", "/auth/login", json={"mobile_number": SEED_MOBILE, "password": "wrong-password"}),
        ok=(400, 401),
    )
    check(
        "Seeded guardian can log in",
        call("POST", "/auth/login", json={"mobile_number": SEED_MOBILE, "password": SEED_PASSWORD}),
    )

    mobile = "9" + rnd(9)
    password = "Smoke@" + rnd(6)
    registration = {
        "first_name": "Smoke",
        "last_name": "Parent",
        "relationship_to_child": "Mother",
        "mobile_number": mobile,
        "email": f"smoke.{rnd(8)}@example.com",
        "password": password,
        "address_line1": "12 Park Street",
        "city": "Kolkata",
        "state": "West Bengal",
        "pincode": "700016",
        "preferred_language": "English",
        "terms_accepted": True,
        "health_data_consent": True,
        "children": [
            {
                "first_name": "Smoke",
                "last_name": "Child",
                "date_of_birth": "2020-05-10",
                "gender": "Male",
            }
        ],
    }
    check("POST /registration", call("POST", "/registration", json=registration), ok=(201,))

    resp = check(
        "New guardian can log in",
        call("POST", "/auth/login", json={"mobile_number": mobile, "password": password}),
    )
    g_token = (data(resp) or {}).get("access_token")
    if not g_token:
        print("\nCannot continue without a guardian token.")
        return

    check("GET /auth/me", call("GET", "/auth/me", token=g_token))
    resp = check("GET /patients/mine", call("GET", "/patients/mine", token=g_token))
    children = data(resp) or []
    if not children:
        print("\nNo child found for the new guardian, cannot continue.")
        return
    patient = children[0]

    # ------------------------------------------------------------------
    admin_token = None
    new_doctor = None
    doctor_staff_id = DOCTOR_STAFF_ID
    doctor_password = DOCTOR_PASS

    if ADMIN_USER and ADMIN_PASS:
        section("Admin: login and doctor setup")
        resp = check(
            "POST /auth/admin-login",
            call("POST", "/auth/admin-login", json={"username": ADMIN_USER, "password": ADMIN_PASS}),
        )
        admin_token = (data(resp) or {}).get("access_token")

        if admin_token:
            check("GET /doctors", call("GET", "/doctors", token=admin_token))

            temp_password = "Temp@" + rnd(6)
            resp = check(
                "POST /doctors",
                call("POST", "/doctors", token=admin_token, json=doctor_payload(temp_password)),
                ok=(201,),
            )
            new_doctor = data(resp)

            if new_doctor:
                doctor_id = new_doctor["doctor_id"]
                every_day_ok = True
                for day_of_week in range(7):
                    r = call(
                        "POST",
                        f"/doctors/{doctor_id}/availability",
                        token=admin_token,
                        json={
                            "day_of_week": day_of_week,
                            "start_time": "09:00",
                            "end_time": "12:00",
                            "slot_minutes": 30,
                        },
                    )
                    every_day_ok = every_day_ok and r is not None and r.status_code == 201
                record("POST /doctors/{id}/availability (7 days)", every_day_ok)
                check(
                    "GET /doctors/{id}/availability",
                    call("GET", f"/doctors/{doctor_id}/availability", token=admin_token),
                )
                doctor_staff_id = new_doctor["staff_id"]
                doctor_password = temp_password
    else:
        print("\n(ADMIN_USERNAME / ADMIN_PASSWORD not set: admin checks skipped)")

    # ------------------------------------------------------------------
    section("Guardian: slots and booking")
    candidate_ids = [new_doctor["doctor_id"]] if new_doctor else []
    candidate_ids += [d["doctor_id"] for d in doctors[:10] if d["doctor_id"] not in candidate_ids]
    found = find_slot(candidate_ids)

    appointment = {}
    if not found:
        record("GET /doctors/{id}/slots returns free slots", False)
        print("  No doctor has free slots in the next 14 days (set availability first).")
    else:
        booking_doctor_id, booking_day, booking_slot = found
        record("GET /doctors/{id}/slots returns free slots", True)

        payload = {
            "doctor_id": booking_doctor_id,
            "patient_id": patient["patient_id"],
            "scheduled_at": f"{booking_day}T{booking_slot}:00",
            "reason_for_visit": "API smoke test",
        }
        resp = check("POST /appointments", call("POST", "/appointments", token=g_token, json=payload), ok=(201,))
        appointment = data(resp) or {}

        check(
            "Booking the same slot twice is rejected",
            call("POST", "/appointments", token=g_token, json=payload),
            ok=(400, 409),
        )

        resp = check("GET /appointments", call("GET", "/appointments", token=g_token, params={"upcoming_only": False}))
        refs = [a.get("appointment_ref") for a in (data(resp) or [])]
        record("New appointment appears in the guardian list", appointment.get("appointment_ref") in refs)

    # ------------------------------------------------------------------
    d_token = None
    treatment_saved = False

    if doctor_staff_id:
        section("Doctor")
        resp = check(
            "POST /auth/doctor-login",
            call("POST", "/auth/doctor-login", json={"staff_id": doctor_staff_id, "password": doctor_password}),
        )
        d_token = (data(resp) or {}).get("access_token")

        if d_token:
            resp = check("GET /auth/doctor/me", call("GET", "/auth/doctor/me", token=d_token))
            doctor_id = (data(resp) or {}).get("doctor_id")

            if new_doctor:
                new_password = "Doc@" + rnd(6)
                check(
                    "POST /auth/doctor/change-password",
                    call(
                        "POST",
                        "/auth/doctor/change-password",
                        token=d_token,
                        json={"current_password": doctor_password, "new_password": new_password},
                    ),
                )
                resp = check(
                    "Doctor can log in with the new password",
                    call("POST", "/auth/doctor-login", json={"staff_id": doctor_staff_id, "password": new_password}),
                )
                d_token = (data(resp) or {}).get("access_token") or d_token

            resp = check(
                "GET /doctor/appointments",
                call("GET", "/doctor/appointments", token=d_token, params={"upcoming_only": True}),
            )
            if new_doctor and appointment:
                refs = [a.get("appointment_ref") for a in (data(resp) or [])]
                record("Booked appointment appears in the doctor's schedule", appointment.get("appointment_ref") in refs)

            resp = check("GET /doctor/patients", call("GET", "/doctor/patients", token=d_token))
            if new_doctor and appointment:
                ids = [p.get("patient_id") for p in (data(resp) or [])]
                record("Child appears in the doctor's patient list", patient["patient_id"] in ids)

            record_payload = {
                "patient_id": patient["patient_id"],
                "appointment_id": appointment.get("appointment_id") if new_doctor else None,
                "visit_date": datetime.now().replace(microsecond=0).isoformat(),
                "diagnosis": "Smoke test diagnosis",
                "medications": [
                    {
                        "medication_name": "Paracetamol",
                        "dosage": "5 ml",
                        "frequency": "Twice a day",
                        "duration": "3 days",
                        "instructions": "After food",
                    }
                ],
                "treatment_plan": "Rest and fluids",
                "follow_up_date": None,
                "clinical_notes": "Created by the API smoke test",
            }
            resp = check(
                "POST /treatment-records",
                call("POST", "/treatment-records", token=d_token, json=record_payload),
                ok=(200, 201),
            )
            treatment_saved = resp is not None and resp.status_code in (200, 201)

            check(
                "GET /treatment-records/{patient_id} (doctor)",
                call("GET", f"/treatment-records/{patient['patient_id']}", token=d_token),
            )
            check(
                "GET /treatment-records/{patient_id}/latest",
                call("GET", f"/treatment-records/{patient['patient_id']}/latest", token=d_token),
            )
            if doctor_id:
                check(
                    "GET /treatment-records/doctor/{doctor_id}",
                    call("GET", f"/treatment-records/doctor/{doctor_id}", token=d_token),
                )
    else:
        print("\n(No doctor credentials available: doctor checks skipped)")

    # ------------------------------------------------------------------
    section("Guardian: history and cancel")
    if treatment_saved:
        resp = check(
            "GET /treatment-records/{patient_id} (guardian)",
            call("GET", f"/treatment-records/{patient['patient_id']}", token=g_token),
        )
        record("Guardian can see the new record", len(data(resp) or []) >= 1)

    ref = appointment.get("appointment_ref")
    if ref:
        check("PATCH /appointments/{ref}/cancel", call("PATCH", f"/appointments/{ref}/cancel", token=g_token, json={"reason": "smoke test"}))
        check(
            "Cancelling twice is rejected",
            call("PATCH", f"/appointments/{ref}/cancel", token=g_token, json={"reason": "again"}),
            ok=(400,),
        )

    # ------------------------------------------------------------------
    if admin_token:
        section("Admin: patients, assignment and users")
        check("GET /patients (search)", call("GET", "/patients", token=admin_token, params={"search": patient["mrn"]}))
        check("GET /patients/{mrn}", call("GET", f"/patients/{patient['mrn']}", token=admin_token))
        check(
            "PATCH /patients/{mrn}",
            call("PATCH", f"/patients/{patient['mrn']}", token=admin_token, json={"blood_group": "O+"}),
        )

        if new_doctor:
            check(
                "POST /doctor-assignments/",
                call(
                    "POST",
                    "/doctor-assignments/",
                    token=admin_token,
                    json={"patient_id": patient["patient_id"], "doctor_id": new_doctor["doctor_id"]},
                ),
                ok=(200, 201, 409),
            )

        username = "smoke_" + rnd(6, string.ascii_lowercase)
        user_password = "Smoke@12345"
        resp = check(
            "POST /users",
            call(
                "POST",
                "/users",
                token=admin_token,
                json={
                    "username": username,
                    "password": user_password,
                    "user_type": "Staff",
                    "first_name": "Smoke",
                    "last_name": "User",
                },
            ),
            ok=(200, 201),
        )
        user_id = (data(resp) or {}).get("user_id")

        check("GET /users", call("GET", "/users", token=admin_token, params={"search": username}))
        if user_id:
            check("GET /users/{id}", call("GET", f"/users/{user_id}", token=admin_token))
            check("POST /users/{id} (update)", call("POST", f"/users/{user_id}", token=admin_token, json={"first_name": "Updated"}))
            check(
                "POST /users/{id}/change-password",
                call(
                    "POST",
                    f"/users/{user_id}/change-password",
                    token=admin_token,
                    json={"current_password": user_password, "new_password": "Smoke@67890"},
                ),
            )
            check(
                "POST /users/{id}/reset-password",
                call(
                    "POST",
                    f"/users/{user_id}/reset-password",
                    token=admin_token,
                    json={"current_password": "", "new_password": "Reset@12345"},
                ),
            )
            check("DELETE /users/{id}", call("DELETE", f"/users/{user_id}", token=admin_token))

    # ------------------------------------------------------------------
    section("Permissions and security")
    denied("Anonymous cannot list patients", "GET", "/patients")
    denied("Anonymous cannot list users", "GET", "/users")
    # User 999999 does not exist, so an open endpoint answers 404 and changes nothing.
    denied(
        "Anonymous cannot reset a password",
        "POST",
        "/users/999999/reset-password",
        json={"current_password": "", "new_password": "Whatever@123"},
    )
    denied("Guardian cannot list all patients", "GET", "/patients", token=g_token)
    denied("Guardian cannot list users", "GET", "/users", token=g_token)
    denied("Guardian cannot create a doctor", "POST", "/doctors", token=g_token, json=doctor_payload("Temp@123456"))
    denied("Guardian cannot see a doctor's schedule", "GET", "/doctor/appointments", token=g_token)
    if d_token:
        denied("Doctor cannot list users", "GET", "/users", token=d_token)


def summary():
    failed = [name for name, passed in results if not passed]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    run()
    summary()