"""Flask App"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from jinja2 import ChoiceLoader, PackageLoader, PrefixLoader
from report_app.main.views import (
    main,
    server_forbidden,
    page_not_found,
    unknown_server_error,
)


app = Flask(__name__, instance_relative_config=True)

# Config folder file mapping
config = {
    "development": "report_app.config.development",
    "production": "report_app.config.production",
}

# Set config, logging level and AWS DynamoDB table name
if os.getenv("FLASK_CONFIGURATION", "production") == "development":
    app.config.from_object(config["development"])
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    logging.info("Running in Development mode.")
else:
    app.config.from_object(config["production"])
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.info("Running in Production mode.")

# Load sensitive settings from instance/config.py
app.config.from_pyfile("config.py", silent=True)

logging.info("App Setup")

app.secret_key = app.config.get("APP_SECRET_KEY")

app.register_blueprint(main)

app.jinja_loader = ChoiceLoader(
    [
        PackageLoader("report_app"),
        PrefixLoader({"govuk_frontend_jinja": PackageLoader("govuk_frontend_jinja")}),
    ]
)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

app.register_error_handler(403, server_forbidden)
app.register_error_handler(404, page_not_found)
app.register_error_handler(500, unknown_server_error)

# Security and Protection extenstions
CORS(app)
