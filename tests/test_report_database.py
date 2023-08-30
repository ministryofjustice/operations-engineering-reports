import unittest
from unittest.mock import ANY, MagicMock, patch

from botocore.exceptions import ClientError

from report_app.main.report_database import ReportDatabase


@patch.dict('os.environ', {'AWS_ROLE_ARN': 'arn:aws:iam::000000000000:role/test-role'})
class TestReportDatabase(unittest.TestCase):

    @patch('boto3.client')
    @patch('boto3.resource')
    def test_client_creation(self, mock_resource, mock_client):
        mock_client.return_value.assume_role.return_value = {
            'Credentials': {
                'AccessKeyId': 'test_key',
                'SecretAccessKey': 'test_secret',
                'SessionToken': 'test_token'
            }
        }

        mock_dynamodb_client = MagicMock()
        mock_resource.return_value = mock_dynamodb_client

        db = ReportDatabase('test_table')

        mock_resource.assert_called_once_with(
            "dynamodb",
            region_name='eu-west-2'
        )

        self.assertEqual(db._client, mock_dynamodb_client)

    @patch('boto3.client')
    @patch('boto3.resource')
    @patch.object(ReportDatabase, '_check_table_and_assign')
    def test_successful_table_check(self, mock_check_table, mock_client, mock_resource):
        mock_table = MagicMock()
        mock_check_table.return_value = mock_table

        mock_client.return_value.assume_role.return_value = {
            'Credentials': {
                'AccessKeyId': 'test_key',
                'SecretAccessKey': 'test_secret',
                'SessionToken': 'test_token'
            }
        }

        mock_dynamodb_client = MagicMock()
        mock_resource.return_value = mock_dynamodb_client

        report_database = ReportDatabase('test_table')

        self.assertEqual(report_database._table, mock_table)
        self.assertEqual(report_database._table_name, 'test_table')

    @patch('boto3.client')
    @patch('boto3.resource')
    @patch.object(ReportDatabase, '_check_table_and_assign')
    def test_failed_table_check(self, mock_check_table, mock_client, mock_resource):
        mock_check_table.side_effect = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
            operation_name='DescribeTable'
        )

        with self.assertRaises(ClientError):
            ReportDatabase('test_table')

    @patch('boto3.client')
    @patch('boto3.resource')
    @patch.object(ReportDatabase, '_check_table_and_assign')
    def test_successful_scan(self, mock_check_table, mock_client, mock_resource):
        mock_table = MagicMock()
        mock_check_table.return_value = mock_table

        mock_client.return_value.assume_role.return_value = {
            'Credentials': {
                'AccessKeyId': 'test_key',
                'SecretAccessKey': 'test_secret',
                'SessionToken': 'test_token'
            }
        }

        mock_dynamodb_client = MagicMock()
        mock_resource.return_value = mock_dynamodb_client

        mock_table.scan.return_value = {"Items": [{"name": "test_item"}]}

        report_database = ReportDatabase('test_table')
        result = report_database.get_all_repository_reports()

        self.assertEqual(result, [{"name": "test_item"}])

    @patch('boto3.client')
    @patch('boto3.resource')
    @patch.object(ReportDatabase, '_check_table_and_assign')
    def test_failed_scan(self, mock_check_table, mock_client, mock_resource):
        mock_table = MagicMock()
        mock_check_table.return_value = mock_table

        mock_client.return_value.assume_role.return_value = {
            'Credentials': {
                'AccessKeyId': 'test_key',
                'SecretAccessKey': 'test_secret',
                'SessionToken': 'test_token'
            }
        }

        mock_dynamodb_client = MagicMock()
        mock_resource.return_value = mock_dynamodb_client

        mock_table.scan.side_effect = ClientError(
            error_response={'Error': {'Code': 'SomeError', 'Message': 'Some error occurred'}},
            operation_name='Scan'
        )

        self.assertRaises(ClientError, ReportDatabase('test').get_all_repository_reports)

    @patch.object(ReportDatabase, '_check_table_and_assign')
    @patch.object(ReportDatabase, '_ReportDatabase__create_client')
    def test_add_repository_report_success(self, mock_create_client, mock_check_table_and_assign):
        mock_table = MagicMock()
        mock_table.put_item.return_value = None
        mock_check_table_and_assign.return_value = mock_table

        db = ReportDatabase('test_table')

        db.add_repository_report('test_key', {'test': 'value'})

        mock_table.put_item.assert_called_once_with(Item={'name': 'test_key', 'data': {'test': 'value'}, 'stored_at': ANY})

    @patch.object(ReportDatabase, '_check_table_and_assign')
    @patch.object(ReportDatabase, '_ReportDatabase__create_client')
    def test_add_repository_report_failure(self, mock_create_client, mock_check_table_and_assign):
        mock_table = MagicMock()
        error_response = {'Error': {'Code': 'SomeErrorCode', 'Message': 'Some error occurred'}}
        mock_table.put_item.side_effect = ClientError(error_response, 'PutItem')
        mock_check_table_and_assign.return_value = mock_table

        db = ReportDatabase('test_table')

        with self.assertRaises(ClientError):
            db.add_repository_report('test_key', {'test': 'value'})

    @patch.object(ReportDatabase, '_check_table_and_assign')
    @patch.object(ReportDatabase, '_ReportDatabase__create_client')
    def test_get_repository_report_success(self, mock_create_client, mock_check_table_and_assign):
        mock_table = MagicMock()

        mock_table.get_item.return_value = {
            'Item': {
                'name': 'test_repo',
                'data': {'some_key': 'some_value'},
                'stored_at': '01-01-2023 12:00:00'
            }
        }
        mock_check_table_and_assign.return_value = mock_table

        db = ReportDatabase('test_table')
        result = db.get_repository_report('test_repo')
        self.assertEqual(result['name'], 'test_repo')
        self.assertEqual(result['data']['some_key'], 'some_value')

    @patch.object(ReportDatabase, '_check_table_and_assign')
    @patch.object(ReportDatabase, '_ReportDatabase__create_client')
    def test_get_repository_report_failure(self, mock_create_client, mock_check_table_and_assign):
        mock_table = MagicMock()
        error_response = {'Error': {'Code': 'SomeErrorCode', 'Message': 'Some error occurred'}}
        mock_check_table_and_assign.return_value = mock_table

        mock_table.get_item.side_effect = ClientError(error_response, 'GetItem')

        with self.assertRaises(ClientError):
            db = ReportDatabase('test_table')
            db.get_repository_report('test_repo')

    @patch.object(ReportDatabase, '_ReportDatabase__create_client', return_value=MagicMock())
    @patch.object(ReportDatabase, '_check_table_and_assign', return_value=MagicMock())
    @patch.object(ReportDatabase, 'get_all_repository_reports')
    def test_get_all_compliant_repository_reports(self, mock_get_all_reports, mock_check_table, mock_create_client):
        mock_get_all_reports.return_value = [
            {'name': 'repo1', 'data': {'status': True}},
            {'name': 'repo2', 'data': {'status': False}},
            {'name': 'repo3', 'data': {'status': True}},
        ]

        db = ReportDatabase('test_table')
        compliant_reports = db.get_all_compliant_repository_reports()
        self.assertEqual(len(compliant_reports), 2)
        self.assertTrue(all(report['data']['status'] for report in compliant_reports))

    @patch.object(ReportDatabase, '_ReportDatabase__create_client', return_value=MagicMock())
    @patch.object(ReportDatabase, '_check_table_and_assign', return_value=MagicMock())
    @patch.object(ReportDatabase, 'get_all_repository_reports')
    def test_get_all_non_compliant_repository_reports(self, mock_get_all_reports, mock_check_table, mock_create_client):
        mock_get_all_reports.return_value = [
            {'name': 'repo1', 'data': {'status': True}},
            {'name': 'repo2', 'data': {'status': False}},
            {'name': 'repo3', 'data': {'status': True}},
        ]

        db = ReportDatabase('test_table')

        non_compliant_reports = db.get_all_non_compliant_repository_reports()
        self.assertEqual(len(non_compliant_reports), 1)
        self.assertTrue(all(not report['data']['status'] for report in non_compliant_reports))

    @patch.object(ReportDatabase, '_ReportDatabase__create_client', return_value=MagicMock())
    @patch.object(ReportDatabase, '_check_table_and_assign', return_value=MagicMock())
    @patch.object(ReportDatabase, 'get_all_repository_reports')
    def test_get_all_public_repositories(self, mock_get_all_reports, mock_check_table, mock_create_client):
        mock_get_all_reports.return_value = [
            {'name': 'repo1', 'data': {'is_private': True}},
            {'name': 'repo2', 'data': {'is_private': False}},
            {'name': 'repo3', 'data': {'is_private': True}},
        ]

        db = ReportDatabase('test_table')

        public_repositories = db.get_all_public_repositories()
        self.assertEqual(len(public_repositories), 1)
        self.assertFalse(all(report['data']['is_private'] for report in public_repositories))

    @patch.object(ReportDatabase, '_ReportDatabase__create_client', return_value=MagicMock())
    @patch.object(ReportDatabase, '_check_table_and_assign', return_value=MagicMock())
    @patch.object(ReportDatabase, 'get_all_repository_reports')
    def test_get_all_private_repositories(self, mock_get_all_reports, mock_check_table, mock_create_client):
        mock_get_all_reports.return_value = [
            {'name': 'repo1', 'data': {'is_private': True}},
            {'name': 'repo2', 'data': {'is_private': False}},
            {'name': 'repo3', 'data': {'is_private': True}},
        ]

        db = ReportDatabase('test_table')

        public_repositories = db.get_all_private_repositories()
        self.assertEqual(len(public_repositories), 2)
        self.assertTrue(all(report['data']['is_private'] for report in public_repositories))


if __name__ == '__main__':
    unittest.main()
