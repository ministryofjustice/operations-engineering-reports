FROM python:3.12.0-alpine3.18

RUN addgroup -S appgroup && adduser -S appuser -G appgroup -u 1051

RUN \
  apk add \
  --no-cache \
  --no-progress \
  --update \
  --upgrade \
  libcrypto3 \
  libssl3 \
  build-base

WORKDIR /app/operations-engineering-reports

COPY requirements.txt requirements.txt
COPY report_app report_app
COPY operations_engineering_reports.py operations_engineering_reports.py

RUN pip3 install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

USER 1051

EXPOSE 4567

ENTRYPOINT gunicorn operations_engineering_reports:app \
  --bind 0.0.0.0:4567 \
  --timeout 120
