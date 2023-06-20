from unittest.mock import patch, Mock
import unittest
import report_app
from moto import mock_dynamodb
import boto3


class TestFunctionalViews(unittest.TestCase):
    def setUp(self):
        app = report_app.app
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()
        self.index = "/index"

    def tearDown(self):
        self.ctx.pop()

    def test_index(self):
        assert self.client.get(self.index).status_code == 200

    def test_default(self):
        assert self.client.get("/").status_code == 200

    def test_home_with_no_auth(self):
        assert self.client.get("/home").status_code == 302
        assert self.client.get("/home").headers.get("location") == self.index

    def test_start_with_no_auth(self):
        assert self.client.get("/start").status_code == 302
        assert self.client.get("/start").headers.get("location") == self.index

    def test_callback_server_error(self):
        assert self.client.get("/callback").status_code == 500


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
        self.endpoint = "/api/v1/update-github-reports"

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
        response = self.client.post(self.endpoint, json=None)
        self.assertEqual(response.status_code, 400)

    @patch('report_app.main.views.__is_request_correct', return_value=True)
    def test_no_json(self, mock_is_request_correct):
        response = self.client.post(self.endpoint, json=None)
        self.assertEqual(response.status_code, 500)

    @patch('report_app.main.views.__is_request_correct', return_value=True)
    @patch('report_app.main.repository_report.RepositoryReport')
    @patch('report_app.main.report_database.ReportDatabase')
    def test_update_all_github_reports(self, mock_db_context, mock_report, mock_is_request_correct):
        mock_db_context.return_value.add_repository_report.return_value = None

        mock_report.return_value.update_all_github_reports.return_value = None
        response = self.client.post(self.endpoint, json=['{"name": "{test-public-repository}"}'])
        self.assertEqual(response.data, b'ok')
        self.assertEqual(response.status_code, 200)

    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': ''})
    @patch.dict('os.environ', {'DYNAMODB_REGION': ''})
    @patch.dict('os.environ', {'DYNAMODB_ACCESS_KEY_ID': ''})
    @patch.dict('os.environ', {'DYNAMODB_SECRET_ACCESS_KEY': ''})
    def test_no_db(self):
        with self.assertRaises(ValueError):
            self.client.get('/api/v1/compliant-repository/test')

    @patch('report_app.main.report_database.ReportDatabase')
    def test_no_repository(self, mock_from_context):
        mock_from_context.return_value.get_repository_report.return_value = None
        response = self.client.get('/api/v1/compliant-repository/test')
        self.assertEqual(response.status_code, 404)

    def test_private_repository(self):
        response = self.client.get('/api/v1/compliant-repository/test-private-repository')
        self.assertEqual(response.status_code, 403)

    def test_compliant_repository(self):
        response = self.client.get('/api/v1/compliant-repository/test-public-repository')
        self.assertEqual(response.status_code, 200)

    def test_non_compliant_repository(self):
        response = self.client.get('/api/v1/compliant-repository/test-public-repository')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data, b'{"color":"d4351c","isError":"true","label":"MoJ Compliant","message":"FAIL",'
                                        b''b'"schemaVersion":1,"style":"for-the-badge"}\n')


if __name__ == "__main__":
    unittest.main()
