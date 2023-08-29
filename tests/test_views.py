import unittest
from unittest.mock import MagicMock, patch

from flask import current_app

import report_app
from report_app.main.views import _is_request_correct, update_github_reports


class TestAuth0AuthenticationView(unittest.TestCase):

    def setUp(self) -> None:
        self.app = report_app.app
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()
        self.auth0_mock = MagicMock()

    def test_login(self):
        with patch.dict(current_app.extensions, {'authlib.integrations.flask_client': self.auth0_mock}, clear=True):
            response = self.client.get('/login')
            self.assertEqual(response.status_code, 200)

    def test_callback_token_error(self):
        with patch.dict(current_app.extensions, {'authlib.integrations.flask_client': self.auth0_mock}, clear=True):
            self.auth0_mock.auth0.authorize_access_token.side_effect = KeyError()
            response = self.client.get('/callback')
            self.assertEqual(response.status_code, 500)

    def test_callback_email_error(self):
        with patch.dict(current_app.extensions, {'authlib.integrations.flask_client': self.auth0_mock}, clear=True):
            self.auth0_mock.auth0.authorize_access_token.return_value = {"userinfo": {}}
            response = self.client.get('/callback')
            self.assertEqual(response.status_code, 500)

    def test_callback_not_allowed_email(self):
        with patch.dict(current_app.extensions, {'authlib.integrations.flask_client': self.auth0_mock}, clear=True):
            self.auth0_mock.auth0.authorize_access_token.return_value = {"userinfo": {"email": "email@example.com"}}
            response = self.client.get('/callback')
            self.assertEqual(response.status_code, 302)
            self.assertIn('Location', response.headers)
            self.assertEqual(response.headers['Location'], '/logout')

    def test_callback_allowed_email(self):
        with patch.dict(current_app.extensions, {'authlib.integrations.flask_client': self.auth0_mock}, clear=True):
            self.auth0_mock.auth0.authorize_access_token.return_value = {"userinfo": {"email": "email@justice.gov.uk"}}
            response = self.client.get('/callback')
            self.assertEqual(response.status_code, 302)
            self.assertIn('Location', response.headers)
            self.assertEqual(response.headers['Location'], '/home')

    def test_logout(self):
        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 302)
        self.assertIn('Location', response.headers)
        self.assertIn('v2/logout', response.headers['Location'])


@patch.dict('os.environ', {'AWS_ROLE_ARN': 'arn:aws:iam::000000000000:role/test-role'})
class TestStandardsReportsViews(unittest.TestCase):

    def setUp(self):
        app = report_app.app
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()
        self.index = "/index"
        self.update_endpoint = "/api/v2/update-github-reports"
        self.public_landing_endpoint = "/public-github-repositories.html"
        self.private_landing_page = "/private-github-repositories.html"

    @patch("os.getenv")
    def test_correct_request(self, mock_getenv):
        mock_getenv.return_value = "correct_api_key"

        request = MagicMock()
        request.method = "POST"
        request.headers = {
            "X-API-KEY": "correct_api_key",
            "Content-Type": "application/json"
        }
        expected_result = True

        result = _is_request_correct(request)
        self.assertEqual(result, expected_result)

    @patch("os.getenv")
    def test_incorrect_request(self, mock_getenv):
        mock_getenv.return_value = "correct_api_key"

        request = MagicMock()
        request.method = "POST"
        request.headers = {"X-API-KEY": "incorrect_api_key"}
        expected_result = False

        result = _is_request_correct(request)
        self.assertEqual(result, expected_result)

    @patch('report_app.main.views._is_request_correct', return_value=True)
    @patch('report_app.main.views.RepositoryReport')
    def test_update_github_reports(self, mock_repository_report, mock_is_request_correct):
        request = MagicMock()
        request.method = "POST"
        request.headers = {"X-API-KEY": "correct_api_key"}
        request.json = {"key": "value"}

        mock_is_request_correct.return_value = True
        mock_repository_report.return_value = MagicMock()

        response = self.client.post(self.update_endpoint, json=request.json, headers=request.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"message": "GitHub reports updated"})

        mock_repository_report.return_value.update_all_github_reports.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
