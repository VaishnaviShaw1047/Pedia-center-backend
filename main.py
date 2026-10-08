from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_NAME, CORS_ORIGINS
from app.routers import (
    auth,
    doctors,
    appointments,
    registration,
    patients,
    treatment_records,
    users,
)


# This creates your FastAPI application object.
# You can think of app as the central container for your entire API.

app = FastAPI(title=APP_NAME)


# Organize the API endpoints in Swagger documentation.
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(doctors.router, prefix="/api/v1", tags=["doctors"])
app.include_router(appointments.router, prefix="/api/v1", tags=["appointments"])
app.include_router(registration.router, prefix="/api/v1", tags=["registration"])
app.include_router(patients.router, prefix="/api/v1", tags=["patients"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(
    treatment_records.router,
    prefix="/api/v1",
    tags=["treatment-records"],
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Pedia Centre API is running"}