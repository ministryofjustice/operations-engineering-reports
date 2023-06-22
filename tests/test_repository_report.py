import unittest
from unittest.mock import patch, Mock
from report_app.main.repository_report import RepositoryReport
from moto import mock_dynamodb
import boto3


class TestRepositoryReport(unittest.TestCase):
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'TEST_TABLE'})
    @patch.dict('os.environ', {'DYNAMODB_REGION': 'eu-west-2'})
    @patch.dict('os.environ', {'DYNAMODB_ACCESS_KEY_ID': 'FAKE'})
    @patch.dict('os.environ', {'DYNAMODB_SECRET_ACCESS_KEY': 'FAKE'})
    def setUp(self):
        inpt_a = '{"name": "A"}'
        inpt_b = '{"name": "B"}'
        self.report_data = [
            inpt_a,
            inpt_b
        ]

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

        self.repository_report = RepositoryReport(self.report_data)

    def test_init(self):
        self.assertEqual(self.repository_report.report_data, self.report_data)
        self.assertIsNotNone(self.repository_report.database_client)

    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': ''})
    @patch.dict('os.environ', {'DYNAMODB_REGION': ''})
    @patch.dict('os.environ', {'DYNAMODB_ACCESS_KEY_ID': ''})
    @patch.dict('os.environ', {'DYNAMODB_SECRET_ACCESS_KEY': ''})
    def test_init_no_db(self):
        self.assertRaises(ValueError, RepositoryReport, self.report_data)

    def test_update_all_github_reports(self):
        self.repository_report.update_all_github_reports()
        test_data = self.repository_report.database_client.get_all_repository_reports()
        self.assertDictContainsSubset({"name": "A"}, test_data[0])

    def test_database_client_error(self):
        self.repository_report.database_client = None
        self.assertIsNone(self.repository_report.update_all_github_reports())

    @patch.object(RepositoryReport, '_add_report_to_db')
    def test_update_all_github_reports_empty(self, mock_add_report):
        self.repository_report._report_data = []
        self.repository_report.update_all_github_reports()
        mock_add_report.assert_not_called()

    @patch.object(RepositoryReport, '_add_report_to_db')
    def test_update_all_github_reports_valid_data(self, mock_add_report):
        self.repository_report._report_data = ['{"name": "valid_report"}']
        self.repository_report.update_all_github_reports()
        mock_add_report.assert_called_once_with({"name": "valid_report"})

    @patch('report_app.main.repository_report.json.loads')
    @patch('report_app.main.repository_report.logger')
    def test_update_all_github_reports_with_exception(self, mock_logger, mock_json_loads):
        mock_json_loads.side_effect = Exception("Test exception")

        self.repository_report._report_data = ['report1']
        self.repository_report.update_all_github_reports()

        self.repository_report._add_report_to_db = Mock()
        self.repository_report._add_report_to_db.side_effect = Exception("Test exception")
        self.repository_report._add_report_to_db.assert_not_called()

        mock_json_loads.assert_any_call(self.repository_report._report_data[0])

        self.assertEqual(mock_json_loads.call_count, 1)

        mock_logger.error.assert_called_once()

    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': ''})
    def test_fail_to_create_db_client_no_table(self):
        self.assertRaises(ValueError, RepositoryReport, self.report_data)

    @patch('report_app.main.report_database.ReportDatabase', return_value=None)
    def test_create_db_client_failure(self, mock_from_context):
        self.assertRaises(AttributeError, RepositoryReport, self.report_data)


if __name__ == '__main__':
    unittest.main()
