import logging
import boto3
from botocore.exceptions import ClientError
import datetime

logger = logging.getLogger(__name__)


class ReportDatabase:
    """The report database is a client layer that allows you to perform CRUD operations on the DynamoDB table."""
    def __init__(self, table_name: str, access_key: str, secret_key: str, region: str):
        self._table_name = table_name
        self._table = None
        self._client = None

        try:
            self._client = self.__create_client(access_key, secret_key, region)
        except ValueError as err:
            logger.error("Failed to create database client: %s", err)
            raise ValueError("An error occurred while creating the database client: %s", err)

        try:
            self._check_table_exists(table_name)
        except ClientError as err:
            logger.error("The table %s does not exist: %s", self._table_name, err)
            raise ClientError("An error occurred while checking if the table exists: %s", err)

    def _check_table_exists(self, table_name) -> None:
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
            self._table = table

    @staticmethod
    def __create_client(access_key, secret_key, region) -> boto3.resource:
        if not access_key or not secret_key:
            raise ValueError("Access key or secret key is empty")

        if not region:
            raise ValueError("Region is empty")
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

    def get_repository_report(self, key: str) -> dict:
        try:
            response = self._table.get_item(Key={'name': key})
        except ClientError as err:
            logger.error(
                "Couldn't get report %s from table %s. Here's why: %s: %s",
                key, self._table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise ClientError("An error occurred while getting the report from the table: %s", err)
        else:
            return response['Item']
