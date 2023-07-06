import threading
from app.core.config import settings
import smtplib


class EmailThread(threading.Thread):
    def __init__(self, message):
        # Initialize values
        self.message = message
        threading.Thread.__init__(self)

    def run(self):
        try:
            # Run in background
            message = self.message
            with smtplib.SMTP_SSL(
                host=settings.MAIL_SENDER_HOST, port=settings.MAIL_SENDER_PORT
            ) as server:
                server.login(settings.MAIL_SENDER_EMAIL, settings.MAIL_SENDER_PASSWORD)
                server.sendmail(
                    settings.MAIL_SENDER_EMAIL, message["To"], message.as_string()
                )
        except Exception as e:
            print(f"Email Error - {e}")
