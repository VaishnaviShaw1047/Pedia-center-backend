from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth,
    doctors,
    appointments,
    registration,
    patients,
    users,
)


# This creates your FastAPI application object.
# You can think of app as the central container for your entire API.

app = FastAPI(title="Pedia Centre API")


# Organize the API endpoints in Swagger documentation.
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(doctors.router, prefix="/api/v1", tags=["doctors"])
app.include_router(appointments.router, prefix="/api/v1", tags=["appointments"])
app.include_router(registration.router, prefix="/api/v1", tags=["registration"])
app.include_router(patients.router, prefix="/api/v1", tags=["patients"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])




# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Pedia Centre API is running"}