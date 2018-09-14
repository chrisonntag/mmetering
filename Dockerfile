FROM python:3.6

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /mmetering_server/requirements.txt
RUN pip install -r /mmetering_server/requirements.txt

COPY . /mmetering_server/
WORKDIR /mmetering_server/

EXPOSE 8000