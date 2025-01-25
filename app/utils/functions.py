from datetime import datetime, timedelta, timezone
from typing import List, Tuple, cast
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models.models import User
from app.db.database import get_db
from app.schema.user_schema import UserFromDB, AccessToken
from app.settings import settings
import secrets
import jwt

# OAuth instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token")


async def pagination(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=0),
) -> Tuple[int, int]:
    capped_limit = min(100, limit)
    return (skip, capped_limit)


def generate_salt():
    """Generates a cryptographically secure random salt."""
    return secrets.token_urlsafe(32)


def get_user_or_404(user_id: int, db: Session = Depends(get_db)) -> UserFromDB:
    user: User = db.query(User).filter_by(id=user_id).one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found!"
        )

    user = cast(UserFromDB, user.__dict__)

    return user


def get_all_users(
    pagination: Tuple[int, int] = Depends(pagination), db: Session = Depends(get_db)
) -> List[UserFromDB]:
    skip, limit = pagination
    users = db.query(User).offset(skip).limit(limit).all()

    users_list = [
        UserFromDB(
            id=user.id,
            name=user.name,
            last_name=user.last_name,
            email=user.email,
            email_confirm=user.email_confirm,
        )
        for user in users
    ]
    return users_list


def get_user_by_email_or_404(email: str, db: Session) -> User:
    user = db.query(User).filter_by(email=email).one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user email not found!"
        )
    return user


def create_jwt_token(data: dict) -> AccessToken:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return AccessToken(access_token=encoded_jwt)


def decode_jwt_token(token: str):
    try:
        decoded_jwt = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_jwt

    except jwt.ExpiredSignatureError:
        # return {"error": "Token has expired"}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired"
        )

    except jwt.InvalidTokenError:
        # return {"error": "Invalid token"}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_email: str = payload.get("sub")

        if user_email is None:
            raise credentials_exception
        user = get_user_by_email_or_404(email=user_email, db=db)

        if user is None:
            raise credentials_exception
        return user

    except jwt.PyJWTError:
        raise credentials_exception
