from report_app import create_app


def test_config():
    """Test create_app without passing test config."""
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing


def test_home_with_no_auth(client):
    """_summary_"""
    assert client.get("/home").status_code == 302
    assert client.get("/home").headers.get("location") == "/index"


def test_start_with_no_auth(client):
    """_summary_"""
    assert client.get("/start").status_code == 302
    assert client.get("/start").headers.get("location") == "/index"


def test_login_with_no_auth(client):
    """_summary_"""
    assert client.get("/login").status_code == 500


def test_callback_server_error(client):
    """_summary_"""
    assert client.get("/callback").status_code == 500


def test_logout_with_no_auth(client):
    """_summary_"""
    assert client.get("/logout").status_code == 500
