""" Interface to an Amazon DynamoDB table """
import os
import logging
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DynamoDB:
    """Encapsulates an Amazon DynamoDB table"""

    def __init__(self, table, dyn_resource):
        """
        :param table: the DynamoDB table
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        logger.debug("DynamoDB.init()")
        self.table = table
        self.dyn_resource = dyn_resource

    @classmethod
    def from_context(cls):
        """
        Creates a storage object based on context.
        :return: Created DynamoDB object or None
        """
        logger.debug("DynamoDB.from_context()")
        storage = None
        try:
            dyn_resource = None
            if os.getenv("DOCKER_COMPOSE_DEV"):
                dyn_resource = boto3.resource(
                    "dynamodb",
                    endpoint_url="http://dynamodb-local:8000",
                )
            elif os.getenv("FLASK_CONFIGURATION", "production") == "development":
                dyn_resource = boto3.resource(
                    "dynamodb",
                    endpoint_url="http://localhost:8000",
                )
            else:
                # In order it looks in these places.
                # 1. Passing credentials as parameters in the boto.client() method
                # 2. Passing credentials as parameters when creating a Session object
                # 3. Environment variables
                # 4. Shared credential file (~/.aws/credentials)
                # 5. AWS config file (~/.aws/config)

                # Overwrite the AWS env vars with user provided credentials
                os.environ["AWS_DEFAULT_REGION"] = os.getenv("DYNAMODB_REGION")
                os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("DYNAMODB_ACCESS_KEY_ID")
                os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv(
                    "DYNAMODB_SECRET_ACCESS_KEY"
                )

                # Create resource with above credentials
                dyn_resource = boto3.resource(
                    service_name="dynamodb",
                )

            table_name = os.environ.get("DYNAMODB_TABLE_NAME")
            if table_name:
                table = dyn_resource.Table(table_name)
                table.scan()
                logger.info("Table %s ready.", table.name)
                storage = cls(table, dyn_resource)
        except ClientError as err:
            logger.error(
                "DynamoDB.from_context(): Connection error to database. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
        except Exception as err:  # pylint: disable=broad-except
            logger.error(
                "DynamoDB.from_context(): Connection error to database. Here's why: %s",
                err,
            )
        return storage

    def exists(self, table_name):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.
        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
        logger.debug("DynamoDB.exists()")
        try:
            table = self.dyn_resource.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.error("DynamoDB.exists(): Database does not exist")
                exists = False
            else:
                logger.error(
                    "Couldn't check for table existence. Here's why: %s: %s",
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
        else:
            self.table = table
        return exists

    def add_item(self, filename, content):
        """
        Adds a item to the table.
        :param filename: The name of the file in db
        :param content: The data
        """
        logger.debug("DynamoDB.add_item()")
        try:
            self.table.put_item(
                Item={
                    "filename": filename,
                    "content": content,
                    "stored_at": f"{datetime.now():%d-%m-%Y %H:%M:%S}",
                }
            )
            logger.info("Add item succesful")
        except ClientError as err:
            logger.error(
                "Couldn't add item to table. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )

    def get_item(self, filename):
        """
        Gets item data from the table.
        :param filename: The name of the file.
        :return: The requested data.
        """
        logger.debug("DynamoDB.get_item()")
        try:
            response = self.table.get_item(Key={"filename": filename})
        except ClientError as err:
            logger.error(
                "Couldn't get item from table. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            return None
        else:
            return response.get("Item")

    def update_item(self, filename, content):
        """
        Updates the item in the table.
        :param filename: The name of the file to update.
        :param content: The data to update.
        :return: The fields that were updated, with their new values.
        """
        logger.debug("DynamoDB.update_item()")
        stored_at = f"{datetime.now():%d-%m-%Y %H:%M:%S}"
        try:
            response = self.table.update_item(
                Key={"filename": filename},
                UpdateExpression="set content=:content, stored_at=:stored_at",
                ExpressionAttributeValues={
                    ":content": content,
                    ":stored_at": stored_at,
                },
                ReturnValues="UPDATED_NEW",
            )
            logger.info("Update item succesful")
        except ClientError as err:
            logger.error(
                "Couldn't update item in table. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            return None
        else:
            return response.get("Attributes")
