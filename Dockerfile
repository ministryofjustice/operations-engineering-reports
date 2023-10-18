FROM python:3.11.5-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_ROOT_USER_ACTION=ignore

RUN addgroup --gid 1017 --system appgroup \
  && adduser --system --uid 1017 --group appgroup

RUN apt update -y && apt dist-upgrade -y && apt install -y

WORKDIR /home/operations-engineering-reports

COPY . /home/operations-engineering-reports

RUN pip install --no-cache-dir -r requirements.txt


USER 1017
EXPOSE 4567
ENTRYPOINT gunicorn operations_engineering_reports:app \
  --bind 0.0.0.0:4567 \
  --timeout 120

