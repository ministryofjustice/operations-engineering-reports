from unittest.mock import patch, Mock
import unittest
import report_app


class TestViews(unittest.TestCase):
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


class TestGitHubReports(unittest.TestCase):
    def setUp(self):
        app = report_app.app
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()
        self.index = "/index"

    @patch('report_app.main.views.__is_request_correct', return_value=False)
    def test_bad_request(self, mock_is_request_correct):
        response = self.client.post('/api/v1/update-github-reports')
        self.assertEqual(response.status_code, 400)

    @patch('report_app.main.views.__is_request_correct', return_value=True)
    def test_no_json(self, mock_is_request_correct):
        response = self.client.post('/api/v1/update-github-reports', json=None)
        self.assertEqual(response.status_code, 500)

    @patch('report_app.main.views.__is_request_correct', return_value=True)
    @patch('report_app.main.repository_report.RepositoryReport')
    @patch('report_app.main.dynamodb.DynamoDB.from_context')
    def test_update_all_github_reports(self, mock_db_context, mock_report, mock_is_request_correct):
        mock_db_context.return_value.add_item = Mock()  # Mock the add_item method

        mock_report.return_value.update_all_github_reports.return_value = None
        response = self.client.post('/api/v1/update-github-reports', json=['{"name": "value"}'])
        self.assertEqual(response.data, b'ok')
        self.assertEqual(response.status_code, 200)


class TestDisplayBadgeIfCompliant(unittest.TestCase):
    def setUp(self):
        app = report_app.app
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()
        self.index = "/index"

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

    @patch('report_app.main.dynamodb.DynamoDB.from_context', return_value=None)
    def test_no_db(self, mock_from_context):
        with self.assertRaises(Exception):
            self.client.get('/api/v1/compliant-repository/test')

    @patch('report_app.main.dynamodb.DynamoDB.from_context')
    def test_no_repository(self, mock_from_context):
        mock_from_context.return_value.get_item.return_value = None
        response = self.client.get('/api/v1/compliant-repository/test')
        self.assertEqual(response.status_code, 404)

    @patch('report_app.main.dynamodb.DynamoDB.from_context')
    def test_private_repository(self, mock_from_context):
        mock_from_context.return_value.get_item.return_value = self.test_private_repository
        response = self.client.get('/api/v1/compliant-repository/test-private-repository')
        self.assertEqual(response.status_code, 403)

    @patch('report_app.main.dynamodb.DynamoDB.from_context')
    def test_compliant_repository(self, mock_from_context):
        mock_from_context.return_value.get_item.return_value = self.test_public_repository
        response = self.client.get('/api/v1/compliant-repository/test-public-repository')
        self.assertEqual(response.status_code, 200)

    @patch('report_app.main.dynamodb.DynamoDB.from_context')
    def test_non_compliant_repository(self, mock_from_context):
        mock_from_context.return_value.get_item.return_value = self.test_public_repository
        response = self.client.get('/api/v1/compliant-repository/test')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data, b'{"color":"d4351c","isError":"true","label":"MoJ Compliant","message":"FAIL",'
                                        b''b'"schemaVersion":1,"style":"for-the-badge"}\n')


if __name__ == "__main__":
    unittest.main()
