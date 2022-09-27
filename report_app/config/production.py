""" Config values to be used in production """

from os import environ

APP_SECRET_KEY = environ.get("APP_SECRET_KEY")
AUTH0_CLIENT_ID = environ.get("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = environ.get("AUTH0_CLIENT_SECRET")
AUTH0_DOMAIN = environ.get("AUTH0_DOMAIN")
MAIL_FROM_EMAIL = "operations-engineering@digital.justice.gov.uk"
PORT = 4567
SSL_REDIRECT = False
