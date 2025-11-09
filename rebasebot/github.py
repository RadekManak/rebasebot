#    Copyright 2023 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""Contains GitHub related helper classes."""

import logging
import builtins
from dataclasses import dataclass

from functools import cached_property
import re
from urllib.parse import urlparse
from typing import Optional

from github import Auth, Github, GithubIntegration, GithubException, UnknownObjectException

logger = logging.getLogger()


@dataclass
class GitHubBranch:
    """
    GitHubBranch specifies GitHub repository along with a branch there.

    :url:       full GitHub url
    :ns:        namespace (example: 'openshift' in 'https://github.com/openshift/api')
    :name:      repository name (example: 'api' in 'https://github.com/openshift/api')
    :branch:    branch name, 'main' for example
    """
    url: str
    ns: str  # pylint: disable=invalid-name
    name: str
    branch: str


def parse_github_branch(repository_string) -> GitHubBranch:
    """
    parse_github_branch constructs GitHubBranch object from the provided location.
    The repository_string format is <user or organization>/<repo>:<branch>
    """
    url = urlparse(repository_string)
    if url.scheme and url.netloc != "github.com":
        raise ValueError("Only GitHub URLs are supported right now")

    # Remove prefix if it's a URL
    repository_string = repository_string.removeprefix("https://github.com/")

    github_regex = re.compile(
        r"^(?P<organization>[^/]+)/(?P<name>[^:]+):(?P<branch>.*)$")
    match = github_regex.match(repository_string)
    if match is None:
        raise ValueError(
            "GitHub branch value must be in the form <user or organization>/<repo>:<branch>")

    return GitHubBranch(
        f"https://github.com/{match.group('organization')}/{match.group('name')}",
        match.group("organization"),
        match.group("name"),
        match.group("branch")
    )


@dataclass
class GitHubAppCredentials:
    """
    GitHubAppCredentials holds credentials for GitHub app.

    :github_branch: uses for specifying repository where app is installed.
    """
    app_id: int
    app_key: bytes
    github_branch: GitHubBranch


class GithubAppProvider:
    """
    GithubAppProvider helper for constructing and holding authenticated GitHub app.

    Might operate with user API token, or with GithHub app credentials.

    In case user_auth is specified, app-related logic would not be engaged
    and user credentials will be used.

    For the 'app' mode this provider requires two application credentials sets:
    * app: application which is installed in target repository (where rebase PR will be created)
    * cloner: application which is installed into intermediate (rebase) repository
              (where resulting git tree will be pushed)
    """
    _app_credentials: Optional[GitHubAppCredentials]

    _cloner_app_credentials: Optional[GitHubAppCredentials]

    user_auth: bool
    user_token: Optional[str]
    _app_token: Optional[str]
    _cloner_token: Optional[str]

    def __init__(
            self,
            *,
            app_id: Optional[int] = None,
            app_key: Optional[bytes] = None,
            dest_branch: Optional[GitHubBranch] = None,

            cloner_id: Optional[int] = None,
            cloner_key: Optional[bytes] = None,
            rebase_branch: Optional[GitHubBranch] = None,

            user_auth: bool = False,
            user_token: Optional[str] = None,
    ):
        self.user_auth = user_auth
        self.user_token = user_token
        self._app_credentials = None
        self._cloner_app_credentials = None
        self._app_token = None
        self._cloner_token = None

        if not user_auth:
            if not all(
                (app_id, app_key, dest_branch, cloner_id, cloner_key, rebase_branch)
            ):
                raise ValueError(
                    "Credentials for both, cloning and pushing app should be provided")

            self._app_credentials = GitHubAppCredentials(
                app_id=app_id, app_key=app_key, github_branch=dest_branch
            )

            self._cloner_app_credentials = GitHubAppCredentials(
                app_id=cloner_id, app_key=cloner_key, github_branch=rebase_branch
            )

    def get_app_token(self) -> str:
        """
        Get app auth token

        :return: str
        """
        if self.user_auth:
            return self.user_token
        return self._app_token

    def get_cloner_token(self) -> str:
        """
        Get cloner app auth token

        :return: str
        """
        if self.user_auth:
            return self.user_token
        return self._cloner_token

    @cached_property
    def github_app(self) -> Github:
        """
        Authenticated GitHub app.

        In case `user_auth` = True, returns app authenticated with user token.
        In app mode `app_id`, `app_key` and `dest_branch` will be used for app authentication.

        :return: Github
        """
        if self.user_auth:
            return self._get_github_user_logged_in_app()

        gh_app, token = self._github_login_app(self._app_credentials)
        self._app_token = token
        return gh_app

    @cached_property
    def github_cloner_app(self) -> Github:
        """
        Authenticated GitHub app.

        In case `user_auth` = True, returns app authenticated with user token.
        In app mode `cloner_id`, `cloner_key` and `rebase_branch`will be used for app authentication.

        :return: Github
        """
        if self.user_auth:
            return self._get_github_user_logged_in_app()

        gh_app, token = self._github_login_app(self._cloner_app_credentials)
        self._cloner_token = token
        return gh_app

    @staticmethod
    def _github_login_app(credentials: GitHubAppCredentials) -> tuple[Github, str]:
        """
        Authenticate as a GitHub App and return both the Github instance and access token.

        :return: tuple of (Github instance, access_token)
        """
        logging.info(
            "Logging to GitHub as an Application for repository %s", credentials.github_branch.url
        )
        gh_branch = credentials.github_branch

        # Create app authentication
        auth = Auth.AppAuth(credentials.app_id, credentials.app_key)
        gi = GithubIntegration(auth=auth)

        try:
            # Get installation for the repository
            installation = gi.get_repo_installation(gh_branch.ns, gh_branch.name)
        except UnknownObjectException as err:
            msg = (
                f"App has not been authorized by {gh_branch.ns}, or repo "
                f"{gh_branch.ns}/{gh_branch.name} does not exist"
            )
            logging.error(msg)
            raise builtins.Exception(msg) from err

        # Get installation access token
        access_token = gi.get_access_token(installation.id)

        # Create authenticated Github instance
        auth = Auth.Token(access_token.token)
        gh_app = Github(auth=auth)

        return gh_app, access_token.token

    def _get_github_user_logged_in_app(self) -> Github:
        logging.info("Logging to GitHub as a User")
        auth = Auth.Token(self.user_token)
        gh_app = Github(auth=auth)
        return gh_app
