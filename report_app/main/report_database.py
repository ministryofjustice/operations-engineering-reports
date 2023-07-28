import datetime
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ReportDatabase:
    """The report database is a client layer that allows you to perform CRUD operations on the DynamoDB table."""

    def __init__(self, table_name: str, access_key: str, secret_key: str, region: str):
        self._table_name = table_name
        self._table = None
        self._client = None

        if not table_name:
            raise ValueError("The table name cannot be empty")

        self._client = self.__create_client(access_key, secret_key, region)
        self._table = self._check_table_and_assign(table_name)
        logger.info("ReportDatabase initialised with table %s", table_name)
        logger.debug("ReportDatabase initialised with client %s", self._client)

    def _check_table_and_assign(self, table_name) -> any:
        try:
            table = self._client.Table(table_name)
            table.load()
        except ClientError as err:
            if err.response['Error']['Code'] == 'ResourceNotFoundException':
                raise ClientError("The table %s does not exist", self._table_name)
            else:
                logger.error(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    table_name,
                    err.response['Error']['Code'], err.response['Error']['Message'])
                raise
        else:
            return table

    @staticmethod
    def __create_client(access_key, secret_key, region) -> boto3.resource:
        if not access_key or not secret_key:
            raise ValueError("Access key or secret key is empty")

        if not region:
            raise ValueError("Region is empty")

        # TODO: Find a way to do this implicitly
        if os.getenv("DOCKER_COMPOSE_DEV"):
            return boto3.resource(
                "dynamodb",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                endpoint_url="http://dynamodb-local:8000",
            )

        return boto3.resource(
            "dynamodb",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def get_all_repository_reports(self) -> list[dict]:
        try:
            response = self._table.scan()
        except ClientError as err:
            logger.error(
                "Couldn't get all items from table %s. Here's why: %s: %s",
                self._table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise ClientError("An error occurred while getting all items from the table: %s", err)
        else:
            return response["Items"]

    def add_repository_report(self, key: str, value: dict) -> None:
        time = datetime.datetime.now()
        try:
            self._table.put_item(
                Item={
                    "name": key,
                    "data": value,
                    "stored_at": f"{time:%d-%m-%Y %H:%M:%S}",
                }
            )
            logger.info("Item %s successfully added", key)
        except ClientError as err:
            logger.error(
                "Couldn't add item to table. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise ClientError("An error occurred while adding the item to the table: %s", err)
        logger.info("Item %s successfully added", key)
        logger.debug("Item value: %s", value)

    def get_repository_report(self, key: str) -> dict:
        logger.info("Getting report %s from table %s", key, self._table_name)
        try:
            response = self._table.get_item(Key={'name': key})
        except ClientError as err:
            logger.error(
                "Couldn't get report %s from table %s. Here's why: %s: %s",
                key, self._table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise ClientError("An error occurred while getting the report from the table: %s", err)
        else:
            logger.debug("Report %s successfully retrieved with %s", key, response['Item'])
            return response['Item']

    def get_all_compliant_repository_reports(self) -> list[dict]:
        """Get all compliant repository reports from the database."""
        reports = self.get_all_compliant_repository_reports()
        logger.debug("All compliant reports requested: %s", reports)
        return reports

    def get_all_non_compliant_repository_reports(self) -> list[dict]:
        """Get all non-compliant repository reports from the database."""
        reports = self.get_all_non_compliant_repository_reports()
        logger.debug("All noncompliant reports requested: %s", reports)
        return reports

    def get_all_public_repositories(self) -> list[dict]:
        """Get all public reports from the database."""
        reports = self.get_all_public_repositories()
        logger.debug("All public reports requested: %s", reports)
        return reports

    def get_all_private_repositories(self) -> list[dict]:
        """Get all private reports from the database."""
        reports = self.get_all_private_repositories()
        logger.debug("All private reports requested: %s", reports)
        return reports
