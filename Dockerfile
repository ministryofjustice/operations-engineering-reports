FROM python:3.10.6-slim

RUN addgroup -gid 1000 --system appgroup && adduser -uid 1000 --system appuser

RUN apt update -y && apt dist-upgrade -y && apt install -y

WORKDIR /home/operations-engineering-reports

COPY requirements.txt requirements.txt
COPY report_app report_app
COPY operations_engineering_reports.py operations_engineering_reports.py

RUN pip3 install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 4567

USER appuser

ENTRYPOINT FLASK_APP=operations_engineering_reports flask run --host=0.0.0.0 --port=4567
