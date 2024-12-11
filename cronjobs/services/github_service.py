# pylint: disable=E1136, E1135, W0718, C0411

import json
from calendar import timegm
from datetime import date, datetime, timedelta, timezone
from time import gmtime, sleep
from typing import Any, Callable

from dateutil.relativedelta import relativedelta
from github import (Github, NamedUser, RateLimitExceededException,
                    UnknownObjectException, GithubException)
from github.Organization import Organization
from github.Repository import Repository
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportServerError
from requests import Session

from config.logging_config import logging

logging.getLogger("gql").setLevel(logging.WARNING)


def retries_github_rate_limit_exception_at_next_reset_once(func: Callable) -> Callable:
    def decorator(*args, **kwargs):
        """
        A decorator to retry the method when rate limiting for GitHub resets if the method fails due to Rate Limit related exception.

        WARNING: Since this decorator retries methods, ensure that the method being decorated is idempotent
         or contains only one non-idempotent method at the end of a call chain to GitHub.

         Example of idempotent methods are:
            - Retrieving data
         Example of (potentially) non-idempotent methods are:
            - Deleting data
            - Updating data
        """
        try:
            return func(*args, **kwargs)
        except (RateLimitExceededException, TransportServerError) as exception:
            logging.warning(
                f"Caught {type(exception).__name__}, retrying calls when rate limit resets.")
            rate_limits = args[0].github_client_core_api.get_rate_limit()
            rate_limit_to_use = rate_limits.core if isinstance(
                exception, RateLimitExceededException) else rate_limits.graphql

            reset_timestamp = timegm(rate_limit_to_use.reset.timetuple())
            now_timestamp = timegm(gmtime())
            time_until_core_api_rate_limit_resets = (
                reset_timestamp - now_timestamp) if reset_timestamp > now_timestamp else 0

            wait_time_buffer = 5
            sleep(time_until_core_api_rate_limit_resets +
                  wait_time_buffer if time_until_core_api_rate_limit_resets else 0)
            return func(*args, **kwargs)

    return decorator


class GithubService:
    USER_ACCESS_REMOVED_ISSUE_TITLE: str = "User access removed, access is now via a team"
    GITHUB_GQL_MAX_PAGE_SIZE = 100
    GITHUB_GQL_DEFAULT_PAGE_SIZE = 80
    ENTERPRISE_NAME = "ministry-of-justice-uk"

    # Added to stop TypeError on instantiation. See https://github.com/python/cpython/blob/d2340ef25721b6a72d45d4508c672c4be38c67d3/Objects/typeobject.c#L4444
    def __new__(cls, *_, **__):
        return super(GithubService, cls).__new__(cls)

    def __init__(self, org_token: str, organisation_name: str,
                 enterprise_name: str = ENTERPRISE_NAME) -> None:
        self.organisation_name: str = organisation_name
        self.enterprise_name: str = enterprise_name
        self.organisations_in_enterprise: list = ["ministryofjustice", "moj-analytical-services"]

        self.github_client_core_api: Github = Github(org_token)
        self.github_client_gql_api: Client = Client(transport=AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {org_token}"},
        ), execute_timeout=120)
        self.github_client_rest_api = Session()
        self.github_client_rest_api.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {org_token}",
            }
        )

    @retries_github_rate_limit_exception_at_next_reset_once
    def get_paginated_list_of_repositories_per_type(self, repo_type: str, after_cursor: str | None,
                                                    page_size: int = GITHUB_GQL_DEFAULT_PAGE_SIZE) -> dict[str, Any]:
        logging.info(
            f"Getting paginated list of repositories per type {repo_type}. Page size {page_size}, after cursor {bool(after_cursor)}")
        if page_size > self.GITHUB_GQL_MAX_PAGE_SIZE:
            raise ValueError(
                f"Page size of {page_size} is too large. Max page size {self.GITHUB_GQL_MAX_PAGE_SIZE}")
        the_query = f"org:{self.organisation_name}, archived:false, is:{repo_type}"
        return self.github_client_gql_api.execute(gql("""
            query($page_size: Int!, $after_cursor: String, $the_query: String!) {
                search(
                    type: REPOSITORY
                    query: $the_query
                    first: $page_size
                    after: $after_cursor
                ) {
                repos: edges {
                    repo: node {
                        ... on Repository {
                                isDisabled
                                isPrivate
                                isLocked
                                name
                                pushedAt
                                url
                                description
                                hasIssuesEnabled
                                repositoryTopics(first: 10) {
                                    edges {
                                        node {
                                            topic {
                                                name
                                            }
                                        }
                                    }
                                }
                                defaultBranchRef {
                                    name
                                }
                                collaborators(affiliation: DIRECT) {
                                    totalCount
                                }
                                licenseInfo {
                                    name
                                }
                                collaborators(affiliation: DIRECT) {
                                    totalCount
                                }
                                branchProtectionRules(first: 10) {
                                    edges {
                                        node {
                                            isAdminEnforced
                                            pattern
                                            requiredApprovingReviewCount
                                            requiresApprovingReviews
                                        }
                                    }
                                }
                            }
                        }
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        """), variable_values={"the_query": the_query, "page_size": page_size, "after_cursor": after_cursor})
    
    @retries_github_rate_limit_exception_at_next_reset_once
    def fetch_all_repositories_in_org(self) -> list[dict[str, Any]]:
        """A wrapper function to run a GraphQL query to get the list of repositories in the organisation

        Returns:
            list: A list of the organisation repos names
        """
        repos = []

        # Specifically switch off logging for this query as it is very large and doesn't need to be logged
        logging.disabled = True

        for repo_type in ["public", "private", "internal"]:
            after_cursor = None
            has_next_page = True
            while has_next_page:
                data = self.get_paginated_list_of_repositories_per_type(
                    repo_type, after_cursor)

                if data["search"]["repos"] is not None:
                    for repo in data["search"]["repos"]:
                        if repo["repo"]["isDisabled"] or repo["repo"]["isLocked"]:
                            continue
                        repos.append(repo["repo"])

                has_next_page = data["search"]["pageInfo"]["hasNextPage"]
                after_cursor = data["search"]["pageInfo"]["endCursor"]

        # Re-enable logging
        logging.disabled = False
        return repos