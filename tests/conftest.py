import pytest


@pytest.fixture
def app():
    from report_app import create_app
    return create_app()


@pytest.fixture
def client(app):
    app.index = "/index"
    return app.test_client()
