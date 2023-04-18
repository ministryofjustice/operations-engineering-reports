import os
from flask import Flask


def create_app(test_config=None):
    # Create and configure an app using the application factory pattern.
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )
    if os.environ.get("FLASK_CONFIGURATION") == "development":
        app.config.from_object("report_app.config.development")
    else:
        app.config.from_object("report_app.config.production")

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello. Temp page.
    @app.route("/hello")
    def hello():
        return "Hello, World!"

    return app
