FROM python:3.12.0a7-slim

RUN addgroup --gid 1017 --system appgroup \
  && adduser --system --uid 1017 --group appgroup

RUN apt update -y && apt dist-upgrade -y && apt install -y

WORKDIR /home/operations-engineering-reports

COPY requirements.txt requirements.txt
COPY report_app report_app
COPY operations_engineering_reports.py operations_engineering_reports.py

RUN pip3 install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 4567

USER 1017

ENTRYPOINT FLASK_APP=operations_engineering_reports flask run --host=0.0.0.0 --port=4567
