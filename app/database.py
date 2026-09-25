from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

connect_args = {"check_same_thread": False} 
# If I'm using SQLite, give SQLite this extra configuration. Otherwise, give no extra configuration.
# "is commonly used with web applications such as FastAPI because requests can involve different threads.

engine = create_engine(DATABASE_URL)
# creates the connection between your Python application and the database.

DbSessionContext = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# creates database sessions that you use to execute queries.

Base = declarative_base()
# creates a base class that your database models will inherit from.


def get_db():
    dbContext = DbSessionContext()
    try:
        yield dbContext
    finally:
        dbContext.close()
