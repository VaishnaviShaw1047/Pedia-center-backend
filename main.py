from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import Base, engine
from app.routers import auth, doctors, appointments, registration, patients

# This creates your FastAPI application object.
# You can think of app as the central container for your entire API.

app = FastAPI(title="Pedia Centre API")
# tags ?This does not change the URL.
# It's mainly for organizing the automatic Swagger documentation.
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(doctors.router, prefix="/api/v1", tags=["doctors"])
app.include_router(appointments.router, prefix="/api/v1", tags=["appointments"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True, #Allows credentials such as cookies/authentication information to be included where applicable.
    allow_methods=["*"],  #* means all HTTP methods.
    allow_headers=["*"],  #Allows the frontend to send various HTTP headers ex- Authorization , contentype .



)
# Look at all the SQLAlchemy models registered with Base, and create their tables in the database if they don't already exist
Base.metadata.create_all(bind=engine)

app.include_router(registration.router, prefix="/api/v1", tags=["registration"])
app.include_router(patients.router, prefix="/api/v1", tags=["patients"])


@app.get("/")
def read_root():
    return {"message": "Pedia Centre API is running"}
