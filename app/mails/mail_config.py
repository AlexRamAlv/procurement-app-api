from fastapi import HTTPException, status
from app.settings import mail_config
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
import os


async def send_email(
    emails, subject: str, confirm_url: str, reset_password: bool = False
):
    config_to_send_mails = ConnectionConfig(
        MAIL_USERNAME=mail_config.MAIL_USERNAME,
        MAIL_PASSWORD=mail_config.MAIL_PASSWORD,
        MAIL_FROM=mail_config.MAIL_FROM,
        MAIL_PORT=mail_config.MAIL_PORT,
        MAIL_SERVER=mail_config.MAIL_SERVER,
        MAIL_STARTTLS=mail_config.MAIL_STARTTLS,
        MAIL_SSL_TLS=mail_config.MAIL_SSL_TLS,
        USE_CREDENTIALS=mail_config.USE_CREDENTIALS,
        VALIDATE_CERTS=mail_config.VALIDATE_CERTS,
    )
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_to_use = (
        "ConfirmAccount.html" if not reset_password else "ResetPassword.html"
    )

    template_path = os.path.join(base_dir, template_to_use)

    with open(template_path, "r") as file:
        html = file.read()

    html = html.replace("{{url}}", confirm_url)
    body = html.replace("{{email}}", emails)
    message = MessageSchema(
        subject=f"{mail_config.MAIL_SUBJECT_PREFIX} {subject}",
        recipients=[emails],
        body=body,
        subtype="html",
    )

    fast_mail = FastMail(config_to_send_mails)
    try:
        await fast_mail.send_message(message)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Error! Email could not be sent",
        )
