"""_summary_"""
import unittest
import report_app


class TestURLs(unittest.TestCase):
    """_summary_

    Args:
        unittest (_type_): _description_
    """

    def setUp(self):
        app = report_app.app
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()

    def tearDown(self):
        self.ctx.pop()

    def test_index(self):
        """_summary_"""
        assert self.client.get("/index").status_code == 200

    def test_default(self):
        """_summary_"""
        assert self.client.get("/").status_code == 200

    def test_home_with_no_auth(self):
        """_summary_"""
        assert self.client.get("/home").status_code == 302
        assert self.client.get("/home").headers.get("location") == "/index"

    def test_start_with_no_auth(self):
        """_summary_"""
        assert self.client.get("/start").status_code == 302
        assert self.client.get("/start").headers.get("location") == "/index"

    def test_login_with_no_auth(self):
        """_summary_"""
        assert self.client.get("/login").status_code == 302

    def test_callback_server_error(self):
        """_summary_"""
        assert self.client.get("/callback").status_code == 500

    def test_logout_with_no_auth(self):
        """_summary_"""
        assert self.client.get("/logout").status_code == 302


if __name__ == "__main__":
    unittest.main()