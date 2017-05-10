import os
import getpass
import configparser
from django.conf import settings
from mmetering.filegenerator import XLS
from datetime import datetime
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


def send_contact_email(name, email, message):
    c = Context({'name': name, 'email': email, 'message': message})

    email_subject = render_to_string(
        'mmetering/email/email_subject.txt', c).replace('\n', '')
    email_body = render_to_string('mmetering/email/email_body.txt', c)

    # settings.DEFAULT_TO_EMAIL already is a list
    email = EmailMessage(
        email_subject, email_body, email,
        settings.DEFAULT_TO_EMAIL, [],
        headers={'Reply-To': email}
    )

    logger.info("User sent the contact form")
    return email.send(fail_silently=False)


def send_attachment_email():
    config = configparser.RawConfigParser()
    config.read(os.path.join(settings.BASE_DIR, 'my.cnf'))

    c = Context({
        'name': config.get('object', 'name'),
        'street': config.get('object', 'street'),
        'zip': config.get('object', 'zip'),
        'city': config.get('object', 'city')
    })

    email_subject = render_to_string(
        'mmetering/email/email_meterdata_subject.txt', c).replace('\n', '')
    email_body = render_to_string('mmetering/email/email_meterdata_body.txt', c)

    # settings.DEFAULT_TO_EMAIL already is a list
    email = EmailMessage(
        email_subject, email_body, settings.DEFAULT_FROM_EMAIL,
        settings.DEFAULT_TO_EMAIL, []
    )

    # get the excel file until today as a HttpResponse object
    xls = XLS(None)
    httpresponse = xls.get_file_until(datetime.today())

    user = getpass.getuser()
    savedir = "/home/%s/mmetering-data/" % user
    if not os.path.exists(savedir):
        os.makedirs(savedir)

    # save the content of the response as a file
    filename = "mmetering%s.xlsx" % str(datetime.today())
    with open(savedir + filename, 'wb') as excel_file:
        excel_file.write(httpresponse.content)
        excel_file.close()

    # attach file to the email
    with open(savedir + filename, 'rb') as excel_file:
        email.attach(excel_file.name, excel_file.read(),
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        excel_file.close()

    logger.info("Send mail with current meter data")
    return email.send(fail_silently=False)
