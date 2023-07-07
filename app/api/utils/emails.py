from fastapi import BackgroundTasks
from fastapi_mail import MessageSchema, FastMail, MessageType
from app.core.config import settings
from app.db.managers.accounts import otp_manager


async def sort_email(db, user, type):
    template_file = "welcome.html"
    subject = "Account verified"
    data = {"template_file": template_file, "subject": subject}

    # Sort different templates and subject for respective email types
    if type == "activate":
        template_file = "email-activation.html"
        subject = "Activate your account"
        otp = (await otp_manager.create(db, {"user_id": user.id})).code
        data = {"template_file": template_file, "subject": subject, "otp": otp}

    elif type == "reset":
        template_file = "password-reset.html"
        subject = "Reset your password"
        otp = (await otp_manager.create(db, {"user_id": user.id})).code
        data = {"template_file": template_file, "subject": subject, "otp": otp}

    elif type == "reset-success":
        template_file = "password-reset-success.html"
        subject = "Password reset successfully"
        data = {"template_file": template_file, "subject": subject}

    return data


async def send_email(background_tasks: BackgroundTasks, db, user, type):
    email_data = await sort_email(db, user, type)
    template_file = email_data["template_file"]
    subject = email_data["subject"]

    context = {"name": user.first_name}
    otp = email_data.get("otp")
    if otp:
        context["otp"] = otp

    msg = MessageSchema(
        subject=subject,
        recipients=[user.email],
        template_body=context,
        subtype=MessageType.html,
    )

    fm = FastMail(settings.EMAIL_CONFIG)
    background_tasks.add_task(fm.send_message, msg, template_name=template_file)
