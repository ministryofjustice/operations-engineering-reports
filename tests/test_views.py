from unittest.mock import patch, MagicMock
import os
import unittest
from moto import mock_dynamodb
import boto3
from flask import current_app

import report_app


class TestAuth0Authentication(unittest.TestCase):
    def setUp(self) -> None:
        app = report_app.app
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()
        self.auth0_mock = MagicMock()

        os.environ['AUTH0_DOMAIN'] = 'fake'
        os.environ['AUTH0_CLIENT_ID'] = 'FAKE'
        os.environ['AUTH0_CLIENT_SECRET'] = 'FAKE'

    def tearDown(self) -> None:
        self.ctx.pop()
        os.unsetenv('AUTH0_DOMAIN')
        os.unsetenv('AUTH0_CLIENT_ID')
        os.unsetenv('AUTH0_CLIENT_SECRET')

    def test_login_redirect(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 302)
        self.assertIn('auth0.com', response.headers['Location'])
        self.assertIn('response_type=code', response.headers['Location'])
        self.assertIn('client_id', response.headers['Location'])

    def test_login_auth0_not_found(self):
        with patch.dict(current_app.extensions, {}, clear=True):
            response = self.client.get('/login')
            self.assertEqual(response.status_code, 500)

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
        self.assertIn('auth0', response.headers['Location'])


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
        self.assertEqual(response.data, b'{"message":"GitHub reports updated"}\n')
        self.assertEqual(response.status_code, 200)

    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': ''})
    @patch.dict('os.environ', {'DYNAMODB_REGION': ''})
    @patch.dict('os.environ', {'DYNAMODB_ACCESS_KEY_ID': ''})
    @patch.dict('os.environ', {'DYNAMODB_SECRET_ACCESS_KEY': ''})
    def test_no_db(self):
        with self.assertRaises(ValueError):
            self.client.get('/api/v2/compliant-repository/test')

    @patch('report_app.main.report_database.ReportDatabase')
    def test_no_repository(self, mock_from_context):
        mock_from_context.return_value.get_repository_report.return_value = None
        response = self.client.get('/api/v2/compliant-repository/test')
        self.assertEqual(response.status_code, 404)

    def test_private_repository(self):
        response = self.client.get('/api/v2/compliant-repository/test-private-repository')
        self.assertEqual(response.status_code, 403)

    def test_compliant_repository(self):
        response = self.client.get('/api/v2/compliant-repository/test-public-repository')
        self.assertEqual(response.status_code, 200)

    def test_non_compliant_repository(self):
        response = self.client.get('/api/v2/compliant-repository/test-public-repository')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data, b'{"color":"d4351c","isError":"true","label":"MoJ Compliant","message":"FAIL",'
                                        b''b'"schemaVersion":1,"style":"for-the-badge"}\n')

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

    def test_search_private_repositories(self):
        response = self.client.get('/search-private-repositories', query_string={'q': 'repo'})

        self.assertEqual(response.status_code, 302)

    def test_bad_search_public_repositories(self):
        bad_request = 'zzz'
        response = self.client.get('/search-public-repositories', query_string={'q': bad_request})

        self.assertNotIn(b'${bad_request}', response.data)

    def test_public_github_repositories(self):
        response = self.client.get(self.public_landing_endpoint)
        self.assertEqual(response.status_code, 200)

    def test_successful_public_github_repositories_return(self):
        response = self.client.get(self.public_landing_endpoint)
        self.assertIn(b'0 are <a href="/compliant', response.data)
        self.assertIn(b'1 are <a href="/non-compliant', response.data)

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
