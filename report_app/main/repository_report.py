""" The interface between the App and the AWS DynamoDB table """
import logging
import json
from report_app.main.report_database import ReportDatabase
from botocore.exceptions import ClientError
import os


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

        if not self.database_client:
            raise ValueError("Could not create database client")

    @property
    def _create_db_client(self) -> ReportDatabase:
        # TODO: Find a nicer way to pass these values to the ReportDatabase class
        access_key = os.environ.get("DYNAMODB_ACCESS_KEY_ID")
        secret_key = os.environ.get("DYNAMODB_SECRET_ACCESS_KEY")
        region = os.environ.get("DYNAMODB_REGION")
        table = os.environ.get("DYNAMODB_TABLE_NAME")
        try:
            dynamo_db = ReportDatabase(
                table_name=table,
                access_key=access_key,
                secret_key=secret_key,
                region=region,
            )
        except ClientError as exception:
            logger.error("Failed to create database client: %s", exception)
            raise exception

        return dynamo_db

    @property
    def report_data(self) -> list[str]:
        """A list of repository reports"""
        return self._report_data

    def update_all_github_reports(self) -> None:
        for report in self.report_data:
            try:
                json_report = json.loads(report)
            except json.JSONDecodeError as exception:
                logger.error("Could not decode JSON: %s", exception)
                raise exception
            try:
                self._add_report_to_db(json_report)
            except Exception as exception:
                raise Exception("Could not add report to database: %s", exception)

    def _add_report_to_db(self, new_report: dict) -> None:
        report_name = new_report["name"]
        try:
            self.database_client.add_repository_report(report_name, new_report)
        except Exception as exception:
            raise exception
