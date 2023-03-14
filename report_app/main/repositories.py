""" The interface between the App and the AWS DynamoDB table """
import os
import logging
import json
from cryptography.fernet import Fernet
from report_app.main.dynamodb import DynamoDB

logger = logging.getLogger(__name__)


class Repositories:
    """Encapsulates the repository data exchanged with the AWS DynamoDB database"""

    def __init__(self, repository_permission_type):
        """
        :param repository_permission_type: public or private
        """
        logger.debug("Repositories.init()")
        self.file_name = "data/" + repository_permission_type + "_github_repositories"
        self.repo_data = None
        self.stored_at = None
        self.database_exists = False
        self.table_exists = False
        self.is_data_missing = True
        self.table_name = os.environ.get("DYNAMODB_TABLE_NAME")
        dynamodb = DynamoDB.from_context()
        if dynamodb:
            self.database_exists = True
            if self.table_name:
                if dynamodb.exists(self.table_name):
                    self.table_exists = True
                    db_data = dynamodb.get_item(self.file_name)
                    if db_data:
                        self.repo_data = db_data.get("content")
                        self.stored_at = db_data.get("stored_at")
                        if self.repo_data and self.stored_at:
                            self.is_data_missing = False
                        else:
                            logger.warning("Repositories.init(): Item data is missing")
                    else:
                        logger.warning("Repositories.init(): Item in table is missing")
                else:
                    logger.warning("Repositories.init(): Table is missing in database")
            else:
                logger.error("Repositories.init(): Table name missing")
        else:
            logger.warning("Repositories.init(): Database does not exist")

    def is_database_ready(self):
        """Does the database, table and data exist

        Returns:
            bool: True if all three exist
        """
        logger.debug("Repositories.is_database_ready()")
        return self.database_exists and self.table_exists and not self.is_data_missing

    def is_item_missing(self):
        """Does the database and table exist but no data exists

        Returns:
            bool: True if the database and table exist but no data exists
        """
        logger.debug("Repositories.is_item_missing()")
        return self.database_exists and self.table_exists and self.is_data_missing

    def get_stored_at_date(self):
        """Return the last date the data was updated

        Returns:
            string: the date
        """
        logger.debug("Repositories.get_stored_at_date()")
        return self.stored_at

    def get_total_repositories(self):
        """Return the total number of repositories in the data

        Returns:
            int: the number of repos in the data
        """
        logger.debug("Repositories.get_total_repositories()")
        if self.repo_data:
            return len(self.repo_data)
        return 0

    def get_compliant_repositories(self):
        """Return the compliant repositories from the the data

        Returns:
            list: a list of dicts containing the name, url and
                  last update date of the repos from the data
        """
        logger.debug("Repositories.get_compliant_repositories()")
        compliant_repos = []
        for repository in self.repo_data:
            if repository.get("status") == "PASS":
                compliant_repos.append(
                    {
                        "name": repository.get("name"),
                        "url": repository.get("url"),
                        "last_push": repository.get("last_push"),
                    }
                )

        unique_compliant_repos = [
            i
            for n, i in enumerate(compliant_repos)
            if i not in compliant_repos[n + 1:]
        ]

        if len(compliant_repos) != len(unique_compliant_repos):
            logger.warning(
                "Repositories.get_compliant_repositories(): Duplicate repo's found in json data"
            )

        return unique_compliant_repos

    def get_fail_reasons(self, repo_checks):
        """Return a list of the failure reasons

        Args:
            repo_checks list: the checks performed on the repository
            default_branch (string): the default branch name

        Returns:
            list: list of strings that describe the failure reasons
        """
        reasons = []
        if not repo_checks.get("default_branch_main"):
            reasons.append("The default branch is not `main`")

        if not repo_checks.get("has_default_branch_protection"):
            msg = "Branch protection is not enabled on the `main` branch"
            reasons.append(msg)

        if not repo_checks.get("requires_approving_reviews"):
            reasons.append("Pull request require reviews is not enabled")

        if not repo_checks.get("administrators_require_review"):
            reasons.append(
                "Administrator pull requests require a review is not enabled"
            )

        if not repo_checks.get("issues_section_enabled"):
            reasons.append("The issues section is not enabled")

        if not repo_checks.get("has_require_approvals_enabled"):
            reasons.append(
                "The number of pull request approvers is not enabled ie `Require approvals`"
            )

        if not repo_checks.get("has_license"):
            reasons.append("License is not MIT")

        if not repo_checks.get("has_description"):
            reasons.append("Description section is empty")
        return reasons

    def get_non_compliant_repositories(self):
        """Return the non compliant repositories from the data

        Returns:
            list: a list of dicts containing the name, url, the
                  last update date and the failure reasons
        """
        logger.debug("Repositories.get_non_compliant_repositories()")
        non_compliant_repos = []
        for repository in self.repo_data:
            if repository.get("status") == "FAIL":
                non_compliant_repos.append(
                    {
                        "name": repository.get("name"),
                        "fail_reasons": self.get_fail_reasons(repository.get("report")),
                        "url": repository.get("url"),
                        "last_push": repository.get("last_push"),
                    }
                )

        unique_non_compliant_repos = [
            i
            for n, i in enumerate(non_compliant_repos)
            if i not in non_compliant_repos[n + 1:]
        ]

        if len(non_compliant_repos) != len(unique_non_compliant_repos):
            logger.warning(
                "Repositories.get_non_compliant_repositories(): Duplicate repo's found in json data"
            )

        return unique_non_compliant_repos

    def decrypt_data(self, payload):
        """Decrypt received data into plain text data (json)

        Args:
            payload (string): encrypted data

        Returns:
            json: plain text data
        """
        logger.debug("Repositories.decrypt_data()")
        key_hex = os.getenv("ENCRYPTION_KEY")
        if key_hex and payload:
            key = bytes.fromhex(key_hex)
            fernet = Fernet(key)
            encrypted_data_as_bytes = payload.encode()
            decrypted_data_as_bytes = fernet.decrypt(encrypted_data_as_bytes)
            data_as_string = decrypted_data_as_bytes.decode()
            data = json.loads(data_as_string)
            return data
        return 0

    def update_item_in_table(self, received_json):
        """Update an item within the table of the database with new data

        Args:
            received_json (json): the data to add to the item
        """
        logger.debug("Repositories.update_item_in_table()")
        received_json = self.decrypt_data(received_json)
        dynamodb = DynamoDB.from_context()
        if dynamodb:
            if dynamodb.exists(self.table_name):
                dynamodb.update_item(self.file_name, received_json.get("data"))
            else:
                logger.warning(
                    "Repositories.update_item_in_table(): Table does not exist"
                )
        else:
            logger.warning(
                "Repositories.update_item_in_table(): Could not connect to database"
            )

    def add_item_to_table(self, received_json):
        """Add a new item to the table within the database

        Args:
            received_json (json): the data to add to the item
        """
        logger.debug("Repositories.add_item_to_table()")
        received_json = self.decrypt_data(received_json)
        dynamodb = DynamoDB.from_context()
        if dynamodb:
            if dynamodb.exists(self.table_name):
                dynamodb.add_item(self.file_name, received_json.get("data"))
            else:
                logger.warning("Repositories.add_item_to_table(): Table does not exist")
        else:
            logger.warning(
                "Repositories.add_item_to_table(): Could not connect to database"
            )

    def update_data(self, json_data):
        """Either add or update the data item within the table

        Args:
            json_data (json): the data to add to the item
        """
        if self.is_database_ready():
            self.update_item_in_table(json_data)
        elif self.is_item_missing():
            self.add_item_to_table(json_data)
        else:
            logger.warning("Repositories.update_data(): Did not update")
