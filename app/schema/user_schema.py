from typing import Optional
from pydantic import BaseModel, EmailStr, ValidationError, validator
import re


class Message(BaseModel):
    message: str

    class Config:
        schema_extra = {
            "example": {
                "message": "A descriptive message from the server as result of your request"
            }
        }


class BaseUser(BaseModel):
    name: str
    last_name: str
    email: EmailStr

    @validator("name")
    @classmethod
    def name_to_lower(cls, name: str):
        return name.lower().strip()

    @validator("last_name")
    @classmethod
    def last_name_to_lower(cls, last_name: str):
        return last_name.lower().strip()

    @validator("email")
    @classmethod
    def validate_email(cls, email: EmailStr):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise ValidationError(f"Check email: {email} provided")
        return email.lower().strip()


class UserCreate(BaseUser):
    password: str

    @validator("password")
    @classmethod
    def validate_password(cls, password):
        special_char = r'[!@#$%^&*(),.?":{}|<>]'
        check_upper_letter = r"(?=.*[A-Z])"

        if len(password) < 8:
            raise ValueError("password must be at least 8 characters")

        elif not re.search(special_char, password):
            raise ValueError("password must contain at least one special characters")

        elif not re.search(check_upper_letter, password):
            raise ValueError("password must contain at least one upper case letter")

        return password

    class Config:
        schema_extra = {
            "example": {
                "name": "John",
                "last_name": "Doe",
                "email": "johnDoen@fastapi.com",
                "password": "********",
            }
        }


class UserFromDB(BaseUser):
    id: int
    email_confirm: bool

    class Config:
        schema_extra = {
            "example": {
                "id": "123",
                "name": "John",
                "last_name": "Doe",
                "email": "johnDoen@fastapi.com",
                "email_confrim": False,
            }
        }


class UserUpdate(BaseModel):
    name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "name": "John",
                "last_name": "Doe",
                "email": "johnDoen@fastapi.com",
                "password": "********",
            }
        }

    @validator("name")
    @classmethod
    def name_to_lower(cls, name: str):
        return name.lower().strip()

    @validator("last_name")
    @classmethod
    def last_name_to_lower(cls, last_name: str):
        return last_name.lower().strip()


class UserCredentials(BaseModel):
    email: EmailStr
    password: str

    @validator("email")
    @classmethod
    def validate_email(cls, email: EmailStr):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise ValidationError(f"Check email: {email} provided")
        return email.lower().strip()

    class Config:
        schema_extra = {
            "example": {
                "email": "johnDoen@fastapi.com",
                "password": "********",
            }
        }


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
