import os
import sqlalchemy
from databases import Database
from app.settings import settings
from sqlalchemy.orm import sessionmaker

basedir = os.path.abspath(os.path.dirname(__file__))


DATABASE_URL = settings.DATABASE_URI or "sqlite:///" + os.path.join(
    basedir, "data-dev.sqlite"
)

database = Database(DATABASE_URL)
sqlalchemy_engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlalchemy_engine)


def get_database() -> Database:
    return database


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
