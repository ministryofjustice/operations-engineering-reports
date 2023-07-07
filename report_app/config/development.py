""" Config values to be used during development """
import os

from os import environ

APP_SECRET_KEY = environ.get("APP_SECRET_KEY")
AUTH0_CLIENT_ID = environ.get("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = environ.get("AUTH0_CLIENT_SECRET")
AUTH0_DOMAIN = environ.get("AUTH0_DOMAIN")
FLASK_CONFIGURATION = "development"
DEBUG = True
FLASK_DEBUG = True
MAIL_FROM_EMAIL = "operations-engineering@digital.justice.gov.uk"
PORT = 4567
SSL_REDIRECT = False
TESTING = True

if not APP_SECRET_KEY:
    os.environ["APP_SECRET_KEY"] = "dev"

if not AUTH0_CLIENT_ID:
    os.environ["AUTH0_CLIENT_ID"] = "dev"

if not AUTH0_CLIENT_SECRET:
    os.environ["AUTH0_CLIENT_SECRET"] = "dev"

if not AUTH0_DOMAIN:
    os.environ["AUTH0_DOMAIN"] = "dev"
