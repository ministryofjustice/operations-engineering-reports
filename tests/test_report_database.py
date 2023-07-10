import unittest
from unittest.mock import MagicMock, patch

import boto3
from moto import mock_dynamodb

from report_app.main.report_database import ReportDatabase


class TestReportDatabase(unittest.TestCase):
    def setUp(self):
        self.mock_db = mock_dynamodb()
        self.mock_db.start()

        boto3.resource('dynamodb', region_name='eu-west-2').create_table(
            TableName='MOCK_TABLE',
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
        self.report_database = ReportDatabase('MOCK_TABLE', 'test_access_key', 'test_secret_key', 'eu-west-2')

    def tearDown(self):
        self.mock_db.stop()

    def test_init_with_correct_table(self):
        self.assertEqual(self.report_database._table_name, 'MOCK_TABLE')
        self.assertIsNotNone(self.report_database._table)
        self.assertIsNotNone(self.report_database._client)

    def test_init_without_credentials(self):
        self.assertRaises(ValueError, ReportDatabase, 'MOCK_TABLE', '', '', 'eu-west-2')

    def test_init_with_incorrect_table(self):
        self.assertRaises(Exception, ReportDatabase, 'INCORRECT_TABLE', 'test_access_key', 'test_secret_key',
                          'eu-west-2')

    def test_init_without_region(self):
        self.assertRaises(ValueError, ReportDatabase, 'MOCK_TABLE', 'test_access_key', 'test_secret_key', '')

    @patch('report_app.main.report_database.boto3.resource')
    @patch('report_app.main.report_database.os.getenv')
    def test_create_client_with_docker_compose_dev(self, mock_getenv, mock_boto_resource):
        # Arrange
        mock_boto_resource.return_value = MagicMock()
        mock_getenv.return_value = '1'
        access_key = 'test_access_key'
        secret_key = 'test_secret_key'
        region = 'test_region'

        # Act
        client = ReportDatabase._ReportDatabase__create_client(access_key, secret_key, region)

        # Assert
        mock_boto_resource.assert_called_once_with(
            "dynamodb",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            endpoint_url="http://dynamodb-local:8000",
        )
        self.assertEqual(client, mock_boto_resource.return_value)

    def test_check_table_exists_with_correct_table(self):
        self.assertEqual(self.report_database._table_name, 'MOCK_TABLE')

    def test_check_table_exists_with_incorrect_table(self):
        self.assertRaises(Exception, self.report_database._check_table_and_assign, 'INCORRECT_TABLE')

    def test_add_item(self):
        self.report_database.add_repository_report('test_key', {'name': 'test_key', 'data': 'test_value'})
        self.assertIsNotNone(self.report_database.get_repository_report('test_key'))

    def test_add_item_with_incorrect_key(self):
        self.assertRaises(AttributeError, self.report_database.add_repository_report, "", "")

    def test_get_item_with_incorrect_key(self):
        self.assertRaises(AttributeError, self.report_database.get_repository_report, "")

    def test_get_all_items(self):
        self.report_database.add_repository_report('test_key', {'name': 'test_key', 'data': 'test_value'})
        self.report_database.add_repository_report('test_key2', {'name': 'test_key2', 'data': 'test_value2'})
        self.assertEqual(len(self.report_database.get_all_repository_reports()), 2)

    def test_get_all_items_with_no_items(self):
        self.assertEqual(len(self.report_database.get_all_repository_reports()), 0)

    def test_get_all_compliant_and_non_compliant_reports(self):
        self.report_database.add_repository_report('test_key', {'name': 'test_key', 'status': True})
        self.report_database.add_repository_report('test_key2', {'name': 'test_key2', 'status': False})
        self.assertEqual(len(self.report_database.get_all_compliant_repository_reports()), 1)
        self.assertEqual(len(self.report_database.get_all_non_compliant_repository_reports()), 1)

    def test_get_all_public_repositories(self):
        self.report_database.add_repository_report('test_key', {'name': 'test_key', 'is_private': True})
        self.report_database.add_repository_report('test_key2', {'name': 'test_key', 'is_private': False})
        self.assertEqual(len(self.report_database.get_all_public_repositories()), 1)

    def test_get_all_private_repositories(self):
        self.report_database.add_repository_report('test_key', {'name': 'test_key', 'is_private': True})
        self.report_database.add_repository_report('test_key2', {'name': 'test_key', 'is_private': False})
        self.assertEqual(len(self.report_database.get_all_private_repositories()), 1)


if __name__ == '__main__':
    unittest.main()
