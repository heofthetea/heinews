# use this quickly slapped together module to send emails
# for this website: "Der Mailversand erfolgt über den SMTP-Ausgangsserver mail.belwue.de (Port 25/tcp)."

from smtplib import SMTP
from email.mime.text import MIMEText
from email.charset import add_charset, QP, SHORTEST
from typing import Tuple
from .. import __IN_PRODUCTION__    

log = lambda msg : print(f"send_mail.send_mail -> {msg}")

"""
(tries to) send a mail from the specified email over the specified smtp server.

@param recipients: if mail is sent to multiple adresses, enter as tuple, if there's only a single recipient use a string instead

@return: True if mail was sent, False if an error occurred
"""
def send_mail(*, from_email: str, password: str, recipients: (str or Tuple[str]), subject: str, content: str, smtp: str="smtp.gmail.com", port: int=587) -> bool:
    try:
        if not __IN_PRODUCTION__:
            print(content)
            return True
        add_charset('utf-8', SHORTEST, QP, 'utf-8')
        message = MIMEText(content, "plain", _charset="utf-8")
        message["Subject"] = subject
        message["From"] = from_email
        message["Bcc"] = recipients if isinstance(recipients, str) else ','.join(recipients)
        log("created mail content")
        

        server = SMTP(smtp, port)
        log(f"successfully logged in to server: {smtp}:{port}")
        server.starttls()
        server.login(from_email, password)
        log(f"successfully logged in to {from_email}")

        server.send_message(message)
        log("mail sent successfully")
        server.close()
        log("closed server")
        return True

    except Exception as e:
        log(e)
        return False
