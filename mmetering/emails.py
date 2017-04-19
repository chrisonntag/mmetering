from django.conf import settings
from mmetering.filegenerator import XLS
from datetime import datetime
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import render_to_string


def send_contact_email(name, email, message):
    c = Context({'name': name, 'email': email, 'message': message})

    email_subject = render_to_string(
        'mmetering/email/email_subject.txt', c).replace('\n', '')
    email_body = render_to_string('mmetering/email/email_body.txt', c)

    email = EmailMessage(
        email_subject, email_body, email,
        [settings.DEFAULT_FROM_EMAIL], [],
        headers={'Reply-To': email}
    )
    return email.send(fail_silently=False)


def send_attachment_email():
    email_subject = render_to_string(
        'mmetering/email/email_subject.txt').replace('\n', '')
    email_body = render_to_string('mmetering/email/email_body.txt')

    email = EmailMessage(
        email_subject, email_body, 'noreply@mmetering.chrisonntag.com',
        [settings.DEFAULT_FROM_EMAIL], []
    )

    # get the excel file until today as a HttpResponse object
    xls = XLS(None)
    httpresponse = xls.getFileUntil(datetime.today())

    # save the content of the response as a file
    filename = "mmetering%s.xlsx" % str(datetime.today())
    with open("/Users/christoph/Desktop/" + filename, 'wb') as excel_file:
        excel_file.write(httpresponse.content)
        excel_file.close()

    # attach file to the email
    with open("/Users/christoph/Desktop/" + filename, 'rb') as excel_file:
        email.attach(excel_file.name, excel_file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        excel_file.close()

    return email.send(fail_silently=False)
