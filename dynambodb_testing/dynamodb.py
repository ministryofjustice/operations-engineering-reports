""" Example of working with a locally created AWS DynamoDB instance """
import logging
import time
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

#  pylint: disable=duplicate-code


class DynamoDB:
    """Encapsulates an Amazon DynamoDB table"""

    def __init__(self, dyn_resource):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        self.table = None

    def exists(self, table_name):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.
        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
        try:
            table = self.dyn_resource.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
            else:
                logger.error(
                    "Couldn't check for table existence. Here's why: %s: %s",
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        else:
            self.table = table
        return exists

    def list_tables(self):
        """
        Lists the Amazon DynamoDB tables for the current account.
        :return: The list of tables.
        """
        try:
            tables = []
            for table in self.dyn_resource.tables.all():
                tables.append(table)
        except ClientError as err:
            logger.error(
                "Couldn't list tables. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            return None
        else:
            return tables

    def add_item(self, filename, content):
        """
        Adds a item to the table.
        :param filename: The name of the file in db
        :param content: The data
        """
        try:
            self.table.put_item(
                Item={
                    "filename": filename,
                    "content": content,
                    "stored_at": f"{datetime.now():%d-%m-%Y %H:%M:%S}",
                }
            )
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
            return response["Item"]

    def update_item(self, filename, content):
        """
        Updates the item in the table.
        :param filename: The name of the file to update.
        :param content: The data to update.
        :return: The fields that were updated, with their new values.
        """
        new_stored_at = f"{datetime.now():%d-%m-%Y %H:%M:%S}"
        try:
            response = self.table.update_item(
                Key={"filename": filename},
                UpdateExpression="set content=:content, stored_at=:new_stored_at",
                ExpressionAttributeValues={
                    ":content": content,
                    ":new_stored_at": new_stored_at,
                },
                ReturnValues="UPDATED_NEW",
            )
        except ClientError as err:
            logger.error(
                "Couldn't update item in table. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            return None
        else:
            return response["Attributes"]

    def scan_db(self):
        """
        Scans for database items
        :return: The list of items
        """
        items = []
        try:
            done = False
            start_key = None
            while not done:
                response = self.table.scan()
                items.extend(response.get("Items", []))
                start_key = response.get("LastEvaluatedKey", None)
                done = start_key is None
        except ClientError as err:
            logger.error(
                "Couldn't scan for items. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )

        return items

    def delete_table(self):
        """
        Deletes the table.
        """
        try:
            self.table.delete()
            self.table = None
        except ClientError as err:
            logger.error(
                "Couldn't delete table. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )

    def create_table(self):
        """
        Creates the table.
        """
        try:
            self.dyn_resource.create_table(
                TableName="cp-637250fa84046ef0",
                KeySchema=[{"AttributeName": "filename", "KeyType": "HASH"}],
                AttributeDefinitions=[
                    {"AttributeName": "filename", "AttributeType": "S"}
                ],
                ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
            )
        except ClientError as err:
            logger.error(
                "Couldn't create table. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )


CONTENT = {
    "data": [
        {
            "name": "cloud-platform",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/cloud-platform",
            "status": "PASS",
            "last_push": "2022-02-01",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
    ]
}


def main():
    """
    Main function
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("-" * 88)
    print("Start")

    time.sleep(4)

    dyn_resource = boto3.resource(
        "dynamodb", region_name="eu-west-2", endpoint_url="http://localhost:8000"
    )
    dynamodb = DynamoDB(dyn_resource)
    dynamodb.create_table()

    filename = "data/public_github_repositories"

    if dynamodb.exists("cp-637250fa84046ef0"):
        dynamodb.add_item(filename, CONTENT)
        result = dynamodb.scan_db()
        print(result)
        dynamodb.list_tables()
        CONTENT["last_push"] = "2028-02-01"
        result = dynamodb.update_item(filename, CONTENT)
        repo_data = dynamodb.get_item(filename)
        print(repo_data["filename"])
        print(repo_data["stored_at"])
        print(repo_data["content"])
        dynamodb.delete_table()
    print("Finished")
    print("-" * 88)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # pylint: disable=broad-except
        print(f"Dynamodynamodb.py: Something went wrong. Here's what: {e}")
