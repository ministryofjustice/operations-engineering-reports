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
    def test_update_all_github_reports_called(self, mock_db_context, mock_report, mock_is_request_correct):
        mock_db_context.return_value.add_item = Mock()  # Mock the add_item method

        mock_report.return_value.update_all_github_reports.return_value = None
        response = self.client.post('/api/v1/update-github-reports', json=['{"name": "value"}'])
        self.assertEqual(response.data, b'ok')
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
