import os
from fastapi.responses import HTMLResponse
from typing import List, cast
from app.settings import settings
from app.models.models import User
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.mails.mail_config import send_email
from fastapi.security import OAuth2PasswordRequestForm
from app.schema.user_schema import UserCreate, UserFromDB
from app.schema.user_schema import AccessToken, UserUpdate, Message
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.utils.functions import get_current_user, get_user_by_email_or_404
from app.utils.functions import get_user_or_404, create_jwt_token, get_all_users


# Creating users router
router = APIRouter()
# Serializer instance
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


@router.get(
    "/users/me",
    response_model=UserFromDB,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_self_info(user: User = Depends(get_current_user)):
    """
    This endpoint allow to confirm an account by accessing to a link send to the email provided.
    If link is valid the user will be allowed to access, in the other hand, access will be forbidden
    """
    return cast(UserFromDB, user.__dict__)


@router.get(
    "/users",
    response_model=List[UserFromDB],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_users(users: List[UserFromDB] = Depends(get_all_users)):
    """
    This endpoint allow to confirm an account by accessing to a link send to the email provided.
    If link is valid the user will be allowed to access, in the other hand, access will be forbidden
    """
    return users


@router.get(
    "/users/{id}",
    response_model=UserFromDB,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_single_user(id: int, db: Session = Depends(get_db)):
    """
    This endpoint allow to confirm an account by accessing to a link send to the email provided.
    If link is valid the user will be allowed to access, in the other hand, access will be forbidden
    """
    user: UserFromDB = get_user_or_404(id, db)
    return user


@router.get(
    "/users/confirm-email/{token}",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_an_account(token: str, db: Session = Depends(get_db)):
    """
    This endpoint allow to confirm an account by accessing to a link send to the email provided.
    If link is valid the user will be allowed to access, in the other hand, access will be forbidden.
    """
    base_dir = os.path.abspath(os.path.dirname(__file__))
    confirm_email_template = os.path.join(
        base_dir, "templates", "ConfirmationEmail.html"
    )
    not_confirm_email_template = os.path.join(
        base_dir, "templates", "ConfirmationEmailFailed.html"
    )

    try:
        email = serializer.loads(token, salt="email-confirm-salt", max_age=3600)
        user: User = get_user_by_email_or_404(email, db)
        user.email_confirm = True
        db.commit()
        db.refresh(user)

        with open(confirm_email_template, "r") as file:
            html = file.read()

        return html.replace("{{email}}", email)

    except SignatureExpired:
        with open(not_confirm_email_template, "r") as file:
            html = file.read()
        return html.replace("{{msg}}", "Confirmation link has expired")

    except BadSignature:
        with open(not_confirm_email_template, "r") as file:
            html = file.read()
        return html.replace("{{msg}}", "Invalid token provided")


@router.post(
    "/users/get-email-confirmation",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
async def another_email_confirmation_token(
    request: Request,
    user: User = Depends(get_current_user),
):
    # Generate token
    token = serializer.dumps(user.email, salt="email-confirm-salt")
    # Url to confrim
    confirm_url = f"{request.base_url}api/v1/users/confirm-email/{token}"

    # send mail
    await send_email(
        emails=user.email,
        subject="Email Confirmation",
        confirm_url=confirm_url,
    )
    return Message(
        message="Please check your email to confirm your registration with a new token."
    )


@router.post(
    "/users/register", status_code=status.HTTP_201_CREATED, response_model=Message
)
async def create_an_account(
    request: Request,
    user_info_sent: UserCreate,
    db: Session = Depends(get_db),
):
    """
    This endpoint allow to create an account by passing a valid email and password
    """
    # verify if email is in database
    user: User = db.query(User).filter_by(email=user_info_sent.email).one_or_none()
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This email already exists!",
        )
    # Generar token
    token = serializer.dumps(user_info_sent.email, salt="email-confirm-salt")
    # Url to confrim
    confirm_url = f"{request.base_url}api/v1/users/confirm-email/{token}"

    # create a new user
    new_user = User(**user_info_sent.dict())
    db.add(new_user)
    db.commit()

    # Enviar correo
    await send_email(
        emails=user_info_sent.email,
        subject="Email Confirmation",
        confirm_url=confirm_url,
    )

    return Message(message="Please check your email to confirm your registration.")


@router.post("/users/token", response_model=AccessToken)
async def get_authorization_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    This endpoint allow existing user get a token to avoid sending credential on each request
    """
    # Validate user credentials
    user: User = get_user_by_email_or_404(form_data.username, db)
    user.verify_password(form_data.password)
    # if valid user return json with jwt token
    access_token: AccessToken = create_jwt_token(data={"sub": user.email})

    return access_token


@router.post(
    "/users/reset-password", response_model=Message, status_code=status.HTTP_200_OK
)
async def reset_password(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    client_url: str = Header(None),
):
    """
    This endpoint allow existing user update his info
    """

    user: User = db.query(User).filter_by(email=user_update.email).one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This email does not exists!",
        )
    # Get client url
    if client_url is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No url client found!"
        )

    # Generate token
    token = serializer.dumps(user_update.email, salt="email-confirm-salt")
    # Url to confrim
    confirm_url = f"{client_url}/reset-password?token={token}&email={user_update.email}"

    # send mail
    await send_email(
        emails=user_update.email,
        subject="Reset password",
        confirm_url=confirm_url,
        reset_password=True,
    )

    return Message(
        message="Please check your email. We send you a link to reset your password"
    )


@router.put(
    "/users/update/{id}",
    response_model=UserFromDB,
    dependencies=[Depends(get_current_user)],
)
async def update_account(
    id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
):
    """
    This endpoint allow existing user update his info
    """
    user_from_db: UserFromDB = get_user_or_404(id, db)
    user: User = get_user_by_email_or_404(user_from_db.email, db)
    # taking not null values
    update_data = user_update.dict(exclude_unset=True)
    # setting values to update the user
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    user = cast(UserFromDB, user.__dict__)

    return user


@router.patch(
    "/users/update-password/{token}",
    status_code=status.HTTP_200_OK,
    response_model=Message,
)
async def update_password(
    token: str,
    user_update_password: UserUpdate,
    db: Session = Depends(get_db),
):
    """
    This endpoint allow existing user update his password
    """

    try:
        email = serializer.loads(token, salt="email-confirm-salt", max_age=3600)
        user: User = get_user_by_email_or_404(email, db)
        user.password = user_update_password.password

        db.commit()
        db.refresh(user)

        return Message(message="Password reseted successfully!")

    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Confirmation link expired"
        )
    except BadSignature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )


@router.delete(
    "/users/delete/{id}",
    dependencies=[Depends(get_current_user)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_account(
    id: int,
    db: Session = Depends(get_db),
):
    """
    This endpoint is to delete users just by administrators.
    """
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    db.delete(user)
    db.commit()

    return None
