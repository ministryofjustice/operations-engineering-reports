from flask import Flask

from app.clients.db_client import DBClient
from app.routes.api_route import create_api_route
from app.services.user_service import UserService


def create_app(db_client: DBClient = None):
    app = Flask(__name__, instance_relative_config=True)

    db_client = db_client or DBClient(app)
    reports_service = ReportsService(db_client)
    app.register_blueprint(create_api_route(reports_service))

    return app
