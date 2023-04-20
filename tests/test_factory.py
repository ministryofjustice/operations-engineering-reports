from report_app import create_app


def test_config():
    """Test create_app without passing test config."""
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing


def test_response(client):
    """Test the response from the app."""
    assert client.get("/home").status_code == 302
    assert client.gjjet("/index").status_code == 200
    assert client.get("/nothingthere").status_code == 404
    assert client.get("/start").status_code == 302

