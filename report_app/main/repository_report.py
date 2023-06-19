""" The interface between the App and the AWS DynamoDB table """
import logging
import json
from report_app.main.dynamodb import DynamoDB


logger = logging.getLogger(__name__)


class RepositoryReport:
    """RepositoryReport represents an abstraction of the DynamoDB table
    that stores the repository reports as a list. All public methods are
    called by the App.

    Attributes:
        report_data (list[any): A list of repository reports
    """
    def __init__(self, report_data: list[any]) -> None:
        logger.debug("Repositories.init()")
        self._report_data = report_data
        self.database_client = None

        try:
            self._create_db_client()
        except Exception as exception:
            logger.error("Failed to create database client: %s", exception)

    @property
    def _create_db_client(self):
        dynamo_db = DynamoDB.from_context()
        if dynamo_db is None:
            raise Exception("Could not connect to database")
        self.database_client = dynamo_db

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
            self.database_client.add_item(report_name, new_report)
        except Exception as exception:
            raise exception

    # def get_all_github_reports(self) -> list[dict]:
    #     """Retrieve all reports from the database"""
    #     logger.debug("Repositories.get_all_reports()")
    #     try:
    #         return self.database_client.get_all_items()
    #     except ClientError:
    #         raise ClientError("Could not retrieve all items from database")
    #

