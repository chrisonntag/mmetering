FROM python:3.6

ENV PYTHONUNBUFFERED 1
ENV CELERY_APP mmetering_server
ENV MMETERING_PRODUCTION 1
ENV DJANGO_SETTINGS_MODULE mmetering_server.settings

RUN mkdir mmetering-server
RUN mkdir mmetering-data
RUN mkdir /var/log/mmetering
RUN touch /var/log/mmetering/mmetering_worker.log
RUN touch /var/log/mmetering/mmetering_beat.log
RUN touch /var/log/mmetering/mmetering.log
RUN chmod -R 0777 /var/log/mmetering

COPY ./requirements.txt /mmetering-server/requirements.txt
RUN pip install -r /mmetering-server/requirements.txt

COPY . /mmetering-server/
WORKDIR /mmetering-server/

EXPOSE 8000