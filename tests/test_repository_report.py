import unittest
from unittest.mock import Mock, patch

from report_app.main.repository_report import RepositoryReport


class TestRepositoryReport(unittest.TestCase):

    @patch('report_app.main.repository_report.ReportDatabase')
    def setUp(self, MockReportDatabase):
        self.mock_data = ["{\"name\": \"repo1\", \"data\": {\"status\": true}}", "{\"name\": \"repo2\", \"data\": {\"status\": false}}"]
        self.report = RepositoryReport(report_data=self.mock_data)
        self.mock_db_instance = MockReportDatabase.return_value

    @patch('report_app.main.repository_report.ReportDatabase')
    def test_initialization(self, MockReportDatabase):
        mock_data = [{"name": "repo1", "data": {"status": True}}, {"name": "repo2", "data": {"status": False}}]
        mock_db_instance = MockReportDatabase.return_value

        report = RepositoryReport(report_data=mock_data)

        self.assertEqual(report._report_data, mock_data)

        self.assertEqual(report.database_client, mock_db_instance)

    def test_update_all_github_reports_success(self):
        self.report._add_report_to_db = Mock()

        self.report.update_all_github_reports()

        self.assertEqual(self.report._add_report_to_db.call_count, len(self.mock_data))

    @patch('report_app.main.repository_report.logger')
    def test_update_all_github_reports_failure(self, mock_logger):
        self.report._report_data = ["not a valid json"]

        self.report.update_all_github_reports()

        mock_logger.error.assert_called_once()


    @patch('report_app.main.repository_report.ReportDatabase')
    def test_add_report_to_db_success(self, MockReportDatabase):
        mock_report = {"name": "repo1", "data": {"status": True}}
        report = RepositoryReport(report_data=[])

        report._add_report_to_db(mock_report)

        MockReportDatabase.return_value.add_repository_report.assert_called_once_with("repo1", mock_report)

    @patch('report_app.main.repository_report.ReportDatabase')
    def test_add_report_to_db_failure(self, MockReportDatabase):
        mock_report = {"name": "repo1", "data": {"status": True}}
        MockReportDatabase.return_value.add_repository_report.side_effect = Exception("Database error")
        report = RepositoryReport(report_data=[])

        with self.assertRaises(Exception) as context:
            report._add_report_to_db(mock_report)
        self.assertEqual(str(context.exception), "Database error")


if __name__ == '__main__':
    unittest.main()
