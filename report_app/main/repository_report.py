import json
import logging
import os

from report_app.main.report_database import ReportDatabase

logger = logging.getLogger(__name__)


class RepositoryReport:
    """RepositoryReport represents an abstraction of the DynamoDB table
    that stores the repository reports as a list. All public methods are
    called by the App.

    Attributes:
        report_data (list[any): A list of repository reports
    """

    def __init__(self, report_data: list[any]) -> None:
        self._report_data = report_data
        self.database_client = self._create_db_client

    @property
    def _create_db_client(self) -> ReportDatabase:
        # TODO: Find a nicer way to pass these values to the ReportDatabase class
        return ReportDatabase(
            table_name=os.environ.get("DYNAMODB_TABLE_NAME"),
            access_key=os.environ.get("DYNAMODB_ACCESS_KEY_ID"),
            secret_key=os.environ.get("DYNAMODB_SECRET_ACCESS_KEY"),
            region=os.environ.get("DYNAMODB_REGION")
        )

    @property
    def report_data(self) -> list[str]:
        """A list of repository reports"""
        return self._report_data

    def update_all_github_reports(self) -> None:
        """Update all the reports in the database after converting the report to json"""
        for report in self.report_data:
            report = json.loads(report)
            self._add_report_to_db(report)

    def _add_report_to_db(self, new_report: dict) -> None:
        report_name = new_report["name"]
        logger.info("Adding %s to the database", report_name)
        self.database_client.add_repository_report(report_name, new_report)
