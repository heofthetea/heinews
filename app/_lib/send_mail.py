# use this quickly slapped together module to send emails
# for this website: "Der Mailversand erfolgt über den SMTP-Ausgangsserver mail.belwue.de (Port 25/tcp)."

from smtplib import SMTP
from email.mime.text import MIMEText
from email.charset import add_charset, QP, SHORTEST

"""
(tries to) send a mail from the specified email over the specified smtp server.

@param recipients: if mail is sent to multiple adresses, enter as tuple, if there's only a single recipient use a string instead

@return: True if mail was sent, False if an error occurred
"""
def send_mail(*, from_email: str, password: str, recipients: (str or tuple[str]), subject: str, content: str, smtp: str="smtp.gmail.com", port: int=587) -> bool:
    try:
        print(content)
        return True
        add_charset('utf-8', SHORTEST, QP, 'utf-8')
        message = MIMEText(content, "plain", _charset="utf-8")
        message["Subject"] = subject
        message["From"] = from_email
        message["Bcc"] = recipients if isinstance(recipients, str) else ','.join(recipients)
        

        server = SMTP(smtp, port)
        server.starttls()
        server.login(from_email, password)

        server.send_message(message)
        server.close()
        return True

    except Exception as e:
        print(str(e))
        return False
