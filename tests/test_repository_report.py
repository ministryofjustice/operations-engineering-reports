import unittest
from unittest.mock import patch
from report_app.main.repository_report import RepositoryReport
from moto import mock_dynamodb
import json
import boto3


class TestRepositoryReport(unittest.TestCase):
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'TEST_TABLE'})
    @patch.dict('os.environ', {'DYNAMODB_REGION': 'eu-west-2'})
    @patch.dict('os.environ', {'DYNAMODB_ACCESS_KEY_ID': 'FAKE'})
    @patch.dict('os.environ', {'DYNAMODB_SECRET_ACCESS_KEY': 'FAKE'})
    def setUp(self):
        inpt_a = '{"name": "A"}'
        inpt_b = '{"name": "A"}'
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
        print("test", self.repository_report.database_client)

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
        print(test_data)
        self.assertDictContainsSubset({"name": "A"}, test_data[0])

    def test_database_client_error(self):
        self.repository_report.database_client = None
        self.assertRaises(Exception, self.repository_report.update_all_github_reports)

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

    def test_update_all_github_reports_invalid_data(self):
        self.repository_report._report_data = ['invalid_json']
        with self.assertRaises(json.JSONDecodeError):
            self.repository_report.update_all_github_reports()

    @patch.object(RepositoryReport, '_add_report_to_db', side_effect=Exception('Failed to add repository data'))
    def test_update_all_github_reports_client_error(self, mock_add_report):
        self.repository_report._report_data = ['{"name": "valid_report"}']
        with self.assertRaises(Exception):
            self.repository_report.update_all_github_reports()

    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'NO_TABLE'})
    def test_fail_to_create_db_client_no_table(self):
        self.assertRaises(ValueError, RepositoryReport, self.report_data)

    @patch('report_app.main.report_database.ReportDatabase', return_value=None)
    def test_create_db_client_failure(self, mock_from_context):
        self.assertRaises(ValueError, RepositoryReport, self.report_data)

    def tearDown(self):
        self.dyanmodb.stop()


if __name__ == '__main__':
    unittest.main()
