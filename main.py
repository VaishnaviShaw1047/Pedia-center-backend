
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# assemble all the routers from diffrent modules and register them with FASTAPI app instance .
from app.routers import (
    auth,
    doctor_portal,
    doctors,
    appointments,
    registration,
    patients,
    treatment_records,
    users,
    doctor_assign,
)


# create an instance of the FASTAPI CLASS and assign it to variable app.
# Now we can use this app instance to define routes, middleware, and other configurations for our API.
app = FastAPI(title="Pedia Centre API")

# Register API routers
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(doctors.router, prefix="/api/v1", tags=["doctors"])
app.include_router(appointments.router, prefix="/api/v1", tags=["appointments"])
app.include_router(registration.router, prefix="/api/v1", tags=["registration"])
app.include_router(patients.router, prefix="/api/v1", tags=["patients"])
app.include_router(doctor_portal.router, prefix="/api/v1", tags=["doctor portal"])

app.include_router(
    treatment_records.router,
    prefix="/api/v1",
    tags=["treatment-records"],
)

app.include_router(users.router, prefix="/api/v1")

# Doctor assignment router
app.include_router(
    doctor_assign.router,
    prefix="/api/v1",
)

# CORS configuration
# cors middleware is added to the FastAPI app to handle cross-origin requests.
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
# root endpoint of the API , which returns a simple JSON response indicating that the API is running.
def read_root():
    return {"message": "Pedia Centre API is running"}
# root function is defined to handle GET requests to the root endpoint("/").
#  When a request is made to this endpoint, it returns a JSON response with a message indicating that the API is running.
