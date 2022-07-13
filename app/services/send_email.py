from pathlib import Path
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic.networks import EmailStr
from app.core.config import (
    MAIL_FROM_NAME,
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_FROM,
    MAIL_PORT,
    MAIL_SERVER,
    WORK_MODE,
)


conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / ".." / "templates" / "email",
)


async def send_email_async(subject: str, email_to: EmailStr, body: dict):
    if WORK_MODE == "prod":
        message = MessageSchema(
            subject=subject,
            recipients=[email_to],  # List of recipients, as many as you can pass
            template_name=body,
            subtype="html",
        )

        fm = FastMail(conf)
        await fm.send_message(message)


async def send_email_in_background(background_tasks: BackgroundTasks, subject: str, email_to: EmailStr, body: dict):
    if WORK_MODE == "prod":
        message = MessageSchema(
            subject=subject,
            recipients=[email_to],
            template_name=body,
            subtype="html",
        )

        fm = FastMail(conf)

        background_tasks.add_task(fm.send_message, message)


def send_email_in_background_with_template(
    background_tasks: BackgroundTasks, subject: str, email_to: EmailStr, body: dict, template_name: str
):
    if WORK_MODE == "dev":
        # print(body)
        message = MessageSchema(subject=subject, recipients=[email_to], template_body=body)

        fm = FastMail(conf)

        background_tasks.add_task(fm.send_message, message, template_name=template_name)
