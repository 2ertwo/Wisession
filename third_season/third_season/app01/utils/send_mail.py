import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from thirdSeason import settings


class MailSend:
    def __init__(self, mail_host, mail_user, mail_pass, sender):
        self.mail_host = mail_host
        self.mail_user = mail_user
        self.mail_pass = mail_pass
        self.sender = sender

    def send_txt(self, targets, content, subject, to):
        part_html = MIMEText(content, 'plain', 'utf-8')
        message = MIMEMultipart()
        message['From'] = self.sender
        message['Subject'] = subject
        message['To'] = to
        message.attach(part_html)
        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(self.mail_host, 25)
            smtpObj.login(self.mail_user, self.mail_pass)
            smtpObj.sendmail(
                self.sender, targets, message.as_string())
            print('success')
            smtpObj.quit()
        except smtplib.SMTPException as e:
            print('error', e)
            return e.__str__()


MS_obj = MailSend(mail_host=settings.MAIL_HOST, mail_user=settings.MAIL_USER, mail_pass=settings.MAIL_PASS,
                  sender=settings.SENDER)
