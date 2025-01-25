from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Decaltative base to metadata
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    last_name = Column(String(30))
    email = Column(String(50))
    password_hash = Column(String(50))
    email_confirm = Column(String(50), default=False)
    creation_date = Column(DateTime, default=datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password: str):
        hahsed_password = pwd_context.hash(password)
        self.password_hash = hahsed_password

    def verify_password(self, password: str) -> bool:
        is_valid = pwd_context.verify(password, self.password_hash)
        if is_valid:
            return is_valid
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user credentials!",
            )
