import datetime
import logging
import os

import boto3
from botocore.exceptions import ClientError
from flask import Flask
from app.config import config

logger = logging.getLogger(__name__)


class DBClient:
    def __init__(self, app: Flask, table_name: str):
        self.app = app
        self.db = None

        self.app.config['AWS_REGION'] = 'eu-west-2'

        if table_name is None:
            raise ValueError("The table name cannot be empty")

        self.db = self._create_client()
        self._table = self._check_table_and_assign(table_name)

    def _check_table_and_assign(self, table_name) -> any:
        try:
            table = self.db.Table(table_name)
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

    def _create_client(self) -> boto3.resource:
        # Check for development environment
        return boto3.resource(
            "dynamodb",
            region_name=self.app.config['AWS_REGION'],
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
