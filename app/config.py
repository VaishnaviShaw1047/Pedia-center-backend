import os
from dotenv import load_dotenv

load_dotenv()

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

# Application configuration
APP_NAME = os.getenv(
    "APP_NAME",
    "Pedia Centre API",
)

# CORS configuration
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:4200",
).split(",")

# Treatment record configuration
TREATMENT_RECORD_START_ID = int(
    os.getenv("TREATMENT_RECORD_START_ID", "100001")
)