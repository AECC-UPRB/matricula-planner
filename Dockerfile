FROM python:2.7-slim

ENV PYTHONUNBUFFERED 1

RUN apt-get update

WORKDIR /app

ADD . /app/

RUN pip install -r requirements.txt