FROM python:3.12.3-alpine3.18

RUN addgroup -S appgroup && adduser -S appuser -G appgroup -u 1051

RUN apk add --no-cache --no-progress \
  libffi-dev \
  build-base \
  curl \
  && apk update \
  && apk upgrade --no-cache --available

WORKDIR /app/operations-engineering-reports

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
COPY report_app report_app
COPY operations_engineering_reports.py operations_engineering_reports.py

RUN pip3 install --no-cache-dir pipenv==2024.1.0 \
  && pipenv install --system --deploy --ignore-pipfile

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

USER 1051

EXPOSE 4567

HEALTHCHECK --interval=60s --timeout=30s CMD curl -I -XGET http://localhost:4567 || exit 1

ENTRYPOINT gunicorn operations_engineering_reports:app \
  --bind 0.0.0.0:4567 \
  --timeout 120
