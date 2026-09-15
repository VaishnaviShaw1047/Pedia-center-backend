from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import Base, engine
from app.routers import registration, patients
from app.routers import registration, patients, auth

app = FastAPI(title="Pedia Centre API")
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(registration.router, prefix="/api/v1", tags=["registration"])
app.include_router(patients.router, prefix="/api/v1", tags=["patients"])


@app.get("/")
def read_root():
    return {"message": "Pedia Centre API is running"}