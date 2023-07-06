from jinja2 import Environment, PackageLoader
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .threads import EmailThread
from app.core.config import settings
from app.db.managers.accounts import otp_manager

env = Environment(loader=PackageLoader("app", "templates"))


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


async def send_email(db, user, type):
    email_data = await sort_email(db, user, type)
    template_file = email_data["template_file"]
    subject = email_data["subject"]

    context = {"name": user.first_name}
    otp = email_data.get("otp")
    if otp:
        context["otp"] = otp

    # Render the email template using jinja
    template = env.get_template(template_file)
    html = template.render(context)

    # Create a message with the HTML content
    message = MIMEMultipart()
    message["From"] = settings.MAIL_SENDER_EMAIL
    message["To"] = user.email
    message["Subject"] = subject
    message.attach(MIMEText(html, "html"))

    # Send email in background
    EmailThread(message).start()
