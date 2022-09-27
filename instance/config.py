""" Config file to load .env file variables for local development
"""
from os import environ
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

AUTH0_CLIENT_ID = environ.get("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = environ.get("AUTH0_CLIENT_SECRET")
AUTH0_DOMAIN = environ.get("AUTH0_DOMAIN")
APP_SECRET_KEY = environ.get("APP_SECRET_KEY")
ENCRYPTION_KEY = environ.get("ENCRYPTION_KEY")
