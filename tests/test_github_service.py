import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, call, patch

from freezegun import freeze_time
from github import (Github, GithubException, RateLimitExceededException,
                    UnknownObjectException)
from github.NamedUser import NamedUser
from github.Organization import Organization
from github.Variable import Variable
from gql.transport.exceptions import TransportServerError

from cronjobs.services.github_service import (
    GithubService, retries_github_rate_limit_exception_at_next_reset_once)

# pylint: disable=E1101

ORGANISATION_NAME = "moj-analytical-services"
ENTERPRISE_NAME = "ministry-of-justice-uk"
USER_ACCESS_REMOVED_ISSUE_TITLE = "User access removed, access is now via a team"
TEST_REPOSITORY = "moj-analytical-services/test_repository"


class TestRetriesGithubRateLimitExceptionAtNextResetOnce(unittest.TestCase):

    def test_function_is_only_called_once_with_arguments(self):
        mock_function = Mock()
        mock_github_client = Mock(Github)
        mock_github_service = Mock(
            GithubService, github_client_core_api=mock_github_client)
        retries_github_rate_limit_exception_at_next_reset_once(
            mock_function)(mock_github_service, "test_arg")
        mock_function.assert_has_calls(
            [call(mock_github_service, "test_arg")])

    @freeze_time("2023-02-01")
    def test_function_is_called_twice_when_rate_limit_exception_raised_once(self):
        mock_function = Mock(
            side_effect=[RateLimitExceededException(Mock(), Mock(), Mock()), Mock()])
        mock_github_client = Mock(Github)
        mock_github_client.get_rate_limit().core.reset = datetime.now()
        mock_github_service = Mock(
            GithubService, github_client_core_api=mock_github_client)
        retries_github_rate_limit_exception_at_next_reset_once(
            mock_function)(mock_github_service, "test_arg")
        mock_function.assert_has_calls([call(mock_github_service, 'test_arg')])

    @freeze_time("2023-02-01")
    def test_rate_limit_exception_raised_when_rate_limit_exception_raised_twice(self):
        mock_function = Mock(side_effect=[
            RateLimitExceededException(Mock(), Mock(), Mock()),
            RateLimitExceededException(Mock(), Mock(), Mock())]
        )
        mock_github_client = Mock(Github)
        mock_github_client.get_rate_limit().core.reset = datetime.now()
        mock_github_service = Mock(
            GithubService, github_client_core_api=mock_github_client)
        self.assertRaises(RateLimitExceededException,
                          retries_github_rate_limit_exception_at_next_reset_once(
                              mock_function), mock_github_service,
                          "test_arg")

    @freeze_time("2023-02-01")
    def test_function_is_called_twice_when_transport_server_error_raised_once(self):
        mock_function = Mock(
            side_effect=[TransportServerError(Mock(), Mock()), Mock()])
        mock_github_client = Mock(Github)
        mock_github_client.get_rate_limit().graphql.reset = datetime.now()
        mock_github_service = Mock(
            GithubService, github_client_core_api=mock_github_client)
        retries_github_rate_limit_exception_at_next_reset_once(
            mock_function)(mock_github_service, "test_arg")
        mock_function.assert_has_calls([call(mock_github_service, 'test_arg')])

    @freeze_time("2023-02-01")
    def test_rate_limit_exception_raised_when_transport_query_error_raised_twice(self):
        mock_function = Mock(side_effect=[
            TransportServerError(Mock(), Mock()),
            TransportServerError(Mock(), Mock())]
        )
        mock_github_client = Mock(Github)
        mock_github_client.get_rate_limit().graphql.reset = datetime.now()
        mock_github_service = Mock(
            GithubService, github_client_core_api=mock_github_client)
        self.assertRaises(TransportServerError,
                          retries_github_rate_limit_exception_at_next_reset_once(
                              mock_function), mock_github_service,
                          "test_arg")


@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__")
@patch("github.Github.__new__")
@patch("requests.sessions.Session.__new__")
class TestGithubServiceInit(unittest.TestCase):

    def test_sets_up_class(self,  mock_github_client_rest_api, mock_github_client_core_api, mock_github_client_gql_api):
        mock_github_client_core_api.return_value = "test_mock_github_client_core_api"
        mock_github_client_gql_api.return_value = "test_mock_github_client_gql_api"
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertEqual("test_mock_github_client_core_api",
                         github_service.github_client_core_api)
        self.assertEqual("test_mock_github_client_gql_api",
                         github_service.github_client_gql_api)
        mock_github_client_rest_api.assert_has_calls([call().headers.update(
            {'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer '})])
        self.assertEqual(ORGANISATION_NAME,
                         github_service.organisation_name)
        self.assertEqual(ENTERPRISE_NAME,
                         github_service.enterprise_name)


@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__")
@patch("github.Github.__new__", new=MagicMock)
class TestGithubServiceGetPaginatedListOfRepositoriesPerType(unittest.TestCase):
    def test_calls_downstream_services(self, _mock_gql_client):
        github_service = GithubService("", ORGANISATION_NAME)
        github_service.get_paginated_list_of_repositories_per_type(
            "public", "after_cursor")
        github_service.github_client_gql_api.execute.assert_called_once()

    def test_throws_value_error_when_page_size_greater_than_limit(self, _mock_gql_client):
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertRaises(
            ValueError, github_service.get_paginated_list_of_repositories_per_type, "public", "test_after_cursor", 101)
        

@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__", new=MagicMock)
@patch("github.Github.__new__", new=MagicMock)
class TestGithubServiceFetchAllRepositories(unittest.TestCase):
    def setUp(self):
        self.return_data = {
            "search": {
                "repos": [
                    {
                        "repo": {
                            "name": "test_repository",
                            "url": "test.com",
                            "isLocked": False,
                            "isDisabled": False,
                        },
                    },
                ],
                "pageInfo": {
                    "hasNextPage": False,
                    "endCursor": "test_end_cursor",
                },
            }
        }

    def test_returning_correct_data(self):
        github_service = GithubService("", ORGANISATION_NAME)
        github_service.get_paginated_list_of_repositories_per_type = MagicMock(
            return_value=self.return_data
        )
        repos = github_service.fetch_all_repositories_in_org()
        self.assertEqual(len(repos), 3)
        self.assertEqual(repos[0]["name"], "test_repository")
        self.assertFalse("unexpected_data" in repos[0])

    def test_nothing_to_return(self):
        github_service = GithubService("", ORGANISATION_NAME)
        self.return_data["search"]["repos"] = None
        github_service.get_paginated_list_of_repositories_per_type = MagicMock(
            return_value=self.return_data
        )
        repos = github_service.fetch_all_repositories_in_org()
        self.assertEqual(len(repos), 0)

    def test_ignore_locked_repo(self):
        github_service = GithubService("", ORGANISATION_NAME)
        self.return_data["search"]["repos"][0]["repo"]["isLocked"] = True
        github_service.get_paginated_list_of_repositories_per_type = MagicMock(
            return_value=self.return_data
        )
        repos = github_service.fetch_all_repositories_in_org()
        self.assertEqual(len(repos), 0)

    def test_ignore_disabled_repo(self):
        github_service = GithubService("", ORGANISATION_NAME)
        self.return_data["search"]["repos"][0]["repo"]["isDisabled"] = True
        github_service.get_paginated_list_of_repositories_per_type = MagicMock(
            return_value=self.return_data
        )
        repos = github_service.fetch_all_repositories_in_org()
        self.assertEqual(len(repos), 0)


if __name__ == "__main__":
    unittest.main()
