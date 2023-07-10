import unittest
from unittest.mock import MagicMock, patch

import boto3
from flask import current_app
from moto import mock_dynamodb

import report_app


class TestAuth0Authentication(unittest.TestCase):
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


@patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'TEST_TABLE'})
@patch.dict('os.environ', {'DYNAMODB_REGION': 'eu-west-2'})
@patch.dict('os.environ', {'DYNAMODB_ACCESS_KEY_ID': 'FAKE'})
@patch.dict('os.environ', {'DYNAMODB_SECRET_ACCESS_KEY': 'FAKE'})
class TestGitHubReports(unittest.TestCase):
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

        self.dyanmodb = mock_dynamodb()
        self.dyanmodb.start()
        boto3.resource('dynamodb', region_name='eu-west-2').create_table(
            TableName='TEST_TABLE',
            KeySchema=[
                {
                    'AttributeName': 'name',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

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

        boto3.resource('dynamodb', region_name='eu-west-2').Table('TEST_TABLE').put_item(
            Item=self.test_public_repository)
        boto3.resource('dynamodb', region_name='eu-west-2').Table('TEST_TABLE').put_item(
            Item=self.test_private_repository)

    @patch('report_app.main.views.__is_request_correct', return_value=False)
    def test_bad_request(self, mock_is_request_correct):
        response = self.client.post(self.update_endpoint, json=None)
        self.assertEqual(response.status_code, 400)

    @patch('report_app.main.views.__is_request_correct', return_value=True)
    def test_no_json(self, mock_is_request_correct):
        response = self.client.post(self.update_endpoint, json=None)
        self.assertEqual(response.status_code, 415)

    @patch('report_app.main.views.__is_request_correct', return_value=True)
    @patch('report_app.main.repository_report.RepositoryReport')
    @patch('report_app.main.report_database.ReportDatabase')
    def test_update_all_github_reports(self, mock_db_context, mock_report, mock_is_request_correct):
        mock_db_context.return_value.add_repository_report.return_value = None

        mock_report.return_value.update_all_github_reports.return_value = None
        response = self.client.post(self.update_endpoint, json=['{"name": "{test-public-repository}"}'])
        self.assertIn("GitHub reports updated", response.json['message'])
        self.assertEqual(response.status_code, 200)

    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': ''})
    @patch.dict('os.environ', {'DYNAMODB_REGION': ''})
    @patch.dict('os.environ', {'DYNAMODB_ACCESS_KEY_ID': ''})
    @patch.dict('os.environ', {'DYNAMODB_SECRET_ACCESS_KEY': ''})
    def test_no_db_failure(self):
        with self.assertRaises(ValueError):
            self.client.get('/api/v2/compliant-repository/test')

    @patch('report_app.main.report_database.ReportDatabase')
    def test_no_repository_failure(self, mock_from_context):
        mock_from_context.return_value.get_repository_report.return_value = None
        response = self.client.get('/api/v2/compliant-repository/test')
        self.assertEqual(response.status_code, 404)

    def test_private_repostitory_failure(self):
        response = self.client.get('/api/v2/compliant-repository/test-private-repository')
        self.assertEqual(response.status_code, 403)

    def test_compliant_repository(self):
        response = self.client.get('/api/v2/compliant-repository/test-public-repository')
        self.assertEqual(response.status_code, 200)

    def test_display_individual_public_report(self):
        response = self.client.get('/public-report/test-public-repository')
        self.assertEqual(response.status_code, 200)

    def test_fail_display_individual_public_report(self):
        response = self.client.get('/public-report/obviously-not-a-repo')
        self.assertEqual(response.status_code, 404)

    def test_display_individual_private_report(self):
        response = self.client.get('/private-report/test-private-repository')
        #  Requires authentication
        self.assertEqual(response.status_code, 302)

    def test_search_public_repositories(self):
        response = self.client.get('/search-public-repositories', query_string={'q': 'repo'})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test-public-repository', response.data)

    def test_search_results_public_repositories(self):
        response = self.client.get('/search-results-public', query_string={'q': 'repo'})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test-public-repository', response.data)

    def test_search_private_repositories(self):
        response = self.client.get('/search-private-repositories', query_string={'q': 'repo'})

        self.assertEqual(response.status_code, 302)

    def test_search_results_private_repositories(self):
        response = self.client.get('/search-results-private', query_string={'q': 'repo'})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test-private-repository', response.data)

    def test_bad_search_public_repositories(self):
        bad_request = 'zzz'
        response = self.client.get('/search-public-repositories', query_string={'q': bad_request})

        self.assertNotIn(b'${bad_request}', response.data)

    def test_public_github_repositories(self):
        response = self.client.get(self.public_landing_endpoint)
        self.assertEqual(response.status_code, 200)

    def test_successful_public_github_repositories_return(self):
        response = self.client.get(self.public_landing_endpoint)
        self.assertEqual(response.status_code, 200)

    def test_successful_private_github_repositories_return(self):
        response = self.client.get(self.private_landing_page)
        self.assertEqual(response.status_code, 302)

    def test_display_compliant_public_repositories(self):
        response = self.client.get("/compliant-public-repositories.html")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'test-public-repository', response.data)

    def test_display_compliant_private_repositories(self):
        response = self.client.get("/compliant-private-repositories.html")
        self.assertEqual(response.status_code, 302)

    def test_display_noncompliant_public_repositories(self):
        response = self.client.get("/non-compliant-public-repositories.html")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test-public-repository', response.data)
        self.assertNotIn(b'test-private-repository', response.data)

    def test_display_noncompliant_private_repositories(self):
        response = self.client.get("/non-compliant-private-repositories.html")
        self.assertEqual(response.status_code, 302)

    def test_display_all_public_repositories(self):
        response = self.client.get("/all-public-repositories.html")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test-public-repository', response.data)
        self.assertNotIn(b'test-private-repository', response.data)

    def test_display_all_private_repositories(self):
        response = self.client.get("/all-private-repositories.html")
        self.assertEqual(response.status_code, 302)

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Non-compliant reports:</b> 2', response.data)


if __name__ == "__main__":
    unittest.main()
