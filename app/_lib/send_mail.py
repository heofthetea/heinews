# use this quickly slapped together module to send emails

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
        add_charset('utf-8', SHORTEST, QP, 'utf-8')
        message = MIMEText(content, "plain", _charset="utf-8")
        message["Subject"] = subject
        message["From"] = from_email
        message["Bcc"] = recipients if isinstance(recipients, str) == 1 else ','.join(recipients)
        

        server = SMTP(smtp, port)
        server.starttls()
        server.login(from_email, password)

        server.send_message(message)
        server.close()
        return True

    except Exception as e:
        print(str(e))
        False

if __name__ == "__main__":
    send_mail(
        from_email="emil.schlaeger@gmx.de", 
        password="", 
        recipients=("fyoug8gle@gmail.com", "emilschlaeger888@gmail.com"), 
        subject="test test",
        content="test\nhttps://youtube.com",
        smtp="mail.gmx.net"
    )
    

    

