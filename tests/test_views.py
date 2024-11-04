import os
import unittest
from unittest.mock import MagicMock, patch

from flask import current_app

import report_app
from report_app.main.views import (_is_request_correct,
                                   display_badge_if_compliant,
                                   search_public_repositories)


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

        self.test_public_repository = {
            'name': 'test-public-repository',
            'data':
                {
                    'is_private': False,
                    'name': 'test-public-repository',
                    'report':
                        {
                            'requires_approving_reviews': True
                        },
                    'default_branch': 'master',
                    'infractions': ["infractions"],
                    'last_push': '2023-05-24T00:45:49Z',
                    'status': False,
                    'url': ''
                },
            'stored_at': '19-06-2023 08:49:32'
        }
        self.test_private_repository = {
            'name': 'test-private-repository',
            'data':
                {
                    'is_private': True,
                    'name': 'test-private-repository',
                    'report':
                        {
                            'requires_approving_reviews': True
                        },
                    'default_branch': 'master',
                    'infractions': [],
                    'last_push': '2023-05-24T00:45:49Z',
                    'status': False,
                    'url': ''
                },
            'stored_at': '19-06-2023 08:49:32'
        }

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

    @patch('report_app.main.views.ReportDatabase')
    def test_display_badge_if_noncompliant(self, mock_report_database):
        repository_name = "test_public_repository"
        mock_report_database.return_value = MagicMock()
        mock_report_database.return_value.get_repository_report.return_value = self.test_public_repository

        response = display_badge_if_compliant(repository_name)

        self.assertEqual(
            response,
            {
                "schemaVersion": 1,
                "label": "MoJ Compliant",
                "message": "FAIL",
                "color": "d4351c",
                "style": "for-the-badge",
                "isError": "true",
            },
        )

        mock_report_database.assert_called_once_with(os.getenv("DYNAMODB_TABLE_NAME"))

        mock_report_database.return_value.get_repository_report.assert_called_once_with(repository_name)

    @patch('report_app.main.views.ReportDatabase')
    def test_display_badge_if_compliant(self, mock_report_database):
        repository = self.test_public_repository
        repository["name"] = "test_public_repository_pass"
        repository["data"]["infractions"] = []
        repository["data"]["status"] = True
        mock_report_database.return_value = MagicMock()
        mock_report_database.return_value.get_repository_report.return_value = repository

        response = display_badge_if_compliant(repository["name"])

        self.assertEqual(
            response,
            {
                "schemaVersion": 1,
                "label": "MoJ Compliant",
                "message": "PASS",
                "color": "005ea5",
                "labelColor": "231f20",
                "style": "for-the-badge",
            },
        )

        mock_report_database.assert_called_once_with(os.getenv("DYNAMODB_TABLE_NAME"))

        mock_report_database.return_value.response = display_badge_if_compliant(repository["name"])

    @patch('report_app.main.views.ReportDatabase')
    def test_public_github_repositories_returns_expected_behaviour(self, mock_report_database):
        mock_report_database.return_value = MagicMock()
        mock_report_database.return_value.get_all_public_repository_reports.return_value = [
            self.test_public_repository
        ]

        response = self.client.get(self.public_landing_endpoint)

        self.assertEqual(response.status_code, 200)

        mock_report_database.assert_called_once_with(os.getenv("DYNAMODB_TABLE_NAME"))

    @patch('report_app.main.views.ReportDatabase')
    def test_private_github_repositories_returns_expected_behaviour(self, mock_report_database):
        mock_report_database.return_value = MagicMock()
        mock_report_database.return_value.get_all_private_repository_reports.return_value = [
            self.test_private_repository
        ]

        response = self.client.get(self.private_landing_page)

        self.assertEqual(response.status_code, 302)

    @patch('report_app.main.views.ReportDatabase')
    def test_search_public_repositories(self, mock_report_database):
        mock_public_reports = [
            {"name": "mock_repository_1"},
            {"name": "mock_repository_2"},
        ]

        mock_report_database.return_value = MagicMock()
        mock_report_database.return_value.get_all_public_repositories.return_value = mock_public_reports

        response = self.client.get("/search-public-repositories", query_string={"q": "mock"})

        self.assertIn("2 results found", response.data.decode("utf-8"))

        mock_report_database.assert_called_once_with(os.getenv("DYNAMODB_TABLE_NAME"))
        mock_report_database.return_value.get_all_public_repositories.assert_called_once_with()

    @patch('report_app.main.report_database.ReportDatabase.__new__')
    def test_public_compliance_report(self, mock_report_database):
        mock_report_database.return_value = MagicMock()
        mock_report_database.return_value.get_all_public_repositories.return_value = [
            {"name": "test_passing", "data": {"status": True}},
            {"name": "test_failing", "data": {"status": False}},
        ]

        response = self.client.post("/api/public-compliance-report", json={
            "repository_names": ["test_passing", "test_failing", "test_non_public_or_missing"] 
        })

        self.assertEqual(response.json, {'mock_repository_1': 'PASS', 'mock_repository_2': 'FAIL'})

        mock_report_database.assert_called_once_with(os.getenv("DYNAMODB_TABLE_NAME"))
        mock_report_database.return_value.get_all_public_repositories.assert_called_once_with()

if __name__ == "__main__":
    unittest.main()
