import datetime
import logging
import os

import boto3
from botocore.exceptions import ClientError
from flask import current_app

logger = logging.getLogger(__name__)


class ReportDatabase:
    """The report database is a client layer that allows you to perform CRUD operations on the DynamoDB table."""

    def __init__(self, table_name: str):
        self._table_name = table_name
        self._table = None
        self._client = None

        self._aws_region = "eu-west-2"
        self._aws_role_arn = os.environ['AWS_ROLE_ARN']

        if not table_name:
            raise ValueError("The table name cannot be empty")

        self._client = self.__create_client()
        self._table = self._check_table_and_assign(table_name)

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

    def __create_client(self) -> boto3.resource:
        # Check for development environment
        if os.getenv("DOCKER_COMPOSE_DEV"):
            return boto3.resource(
                'dynamodb',
                aws_access_key_id="test_access_key",
                aws_secret_access_key="test_secret_key",
                region_name=self._aws_region,
                endpoint_url='http://dynamodb-local:8000'
            )

        # create an STS client object that represents a live connection to the
        # STS service
        sts_client = boto3.client('sts')

        # Call the assume_role method of the STSConnection object and pass the role
        # ARN and a role session name.
        assumed_role_object = sts_client.assume_role(
            RoleArn=self._aws_role_arn,
            RoleSessionName="AssumeRoleSession"
        )

        # From the response that contains the assumed role, get the temporary
        # credentials that can be used to make subsequent API calls
        credentials = assumed_role_object['Credentials']

        return boto3.resource(
            "dynamodb",
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=self._aws_region,
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
            error_msg = f"An error occurred while getting all items from the table: {err}"
            error_response = {'Error': {'Code': '500', 'Message': error_msg}}
            raise ClientError(error_response, 'Scan')
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
            error_msg = f"An error occurred while adding items to the table: {err}"
            error_response = {'Error': {'Code': '500', 'Message': error_msg}}
            raise ClientError(error_response, 'PutItem')
        logger.info("Item %s successfully added", key)
        logger.debug("Item value: %s", value)

    def get_repository_report(self, key: str) -> dict:
        try:
            response = self._table.get_item(Key={'name': key})
        except ClientError as err:
            logger.error(
                "Couldn't get report %s from table %s. Here's why: %s: %s",
                key, self._table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            error_msg = f"An error occurred while getting the report from the table: {err}"
            error_response = {'Error': {'Code': '500', 'Message': error_msg}}
            raise ClientError(error_response, 'GetItem')
        else:
            logger.debug("Report %s successfully retrieved with %s", key, response['Item'])
            return response['Item']

    def get_all_compliant_repository_reports(self) -> list[dict]:
        """Get all compliant repository reports from the database."""
        reports = self.get_all_repository_reports()
        return [report for report in reports if report["data"]["status"]]

    def get_all_non_compliant_repository_reports(self) -> list[dict]:
        """Get all non-compliant repository reports from the database."""
        reports = self.get_all_repository_reports()
        return [report for report in reports if not report["data"]["status"]]

    def get_all_public_repositories(self) -> list[dict]:
        """Get all public reports from the database."""
        reports = self.get_all_repository_reports()
        return [report for report in reports if not report["data"]["is_private"]]

    def get_all_private_repositories(self) -> list[dict]:
        """Get all private reports from the database."""
        reports = self.get_all_repository_reports()
        return [report for report in reports if report["data"]["is_private"]]
