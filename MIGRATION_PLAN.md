# Migration Plan: github3.py → PyGithub

**Status:** Draft
**Created:** 2025-11-08
**Target Completion:** TBD
**Author:** Claude AI
**Reviewer:** TBD

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Migration Rationale](#migration-rationale)
3. [Impact Analysis](#impact-analysis)
4. [Migration Strategy](#migration-strategy)
5. [Implementation Phases](#implementation-phases)
6. [Testing Strategy](#testing-strategy)
7. [Rollback Plan](#rollback-plan)
8. [Timeline & Resources](#timeline--resources)
9. [Risk Assessment](#risk-assessment)
10. [Appendix](#appendix)

---

## Executive Summary

This document outlines the plan to migrate the rebasebot project from **github3.py** (inactive, last release April 2023) to **PyGithub** (actively maintained, latest release September 2025).

**Key Benefits:**
- ✅ Active maintenance and security updates
- ✅ Native cross-repository PR support (eliminates hack at bot.py:482)
- ✅ Better community support (7,600+ stars vs 2,000+)
- ✅ Modern Python 3.8+ support with type hints
- ✅ Regular releases and bug fixes

**Estimated Effort:** 16-24 hours over 2-3 days
**Risk Level:** Low-Medium
**Migration Approach:** Incremental with comprehensive testing

---

## Migration Rationale

### Current Pain Points with github3.py

1. **Inactive Maintenance**
   - Last release: v4.0.1 (April 2023)
   - No releases in 2024 or 2025
   - Classified as "Inactive project" by Snyk
   - Maintainer acknowledged design issues (January 2024 blog post)

2. **Missing Features Requiring Hacks**
   - Cross-repository PR creation requires internal `_post()` method
   - Location: `rebasebot/bot.py:482-497`
   - Related issue: https://github.com/sigmavirus24/github3.py/issues/1190 (unresolved since 2022)

3. **Future Risk**
   - Security vulnerabilities may remain unpatched
   - Potential incompatibility with future Python versions
   - GitHub API deprecations won't be addressed

### Why PyGithub?

| Criteria | github3.py | PyGithub |
|----------|-----------|----------|
| Last Release | April 2023 | September 2025 |
| Stars | ~2,000 | ~7,600 |
| Contributors | ~70 | 394 |
| Python Version | 3.7+ | 3.8+ |
| Cross-repo PRs | Hack required | Native support |
| Type Hints | Partial | Full |
| Maintenance | Inactive | Active |

---

## Impact Analysis

### Files Affected

| File Path | Impact Level | Changes Required |
|-----------|--------------|------------------|
| `requirements.txt` | High | Replace dependency |
| `rebasebot/github.py` | High | Auth & provider rewrite |
| `rebasebot/bot.py` | High | API calls & PR creation |
| `rebasebot/lifecycle_hooks.py` | Medium | Import & type hints |
| `rebasebot/cli.py` | Low | Logging changes |
| `tests/*.py` | High | Mock objects & fixtures |

### API Mapping

#### Authentication

**github3.py:**
```python
import github3

gh = github3.GitHub()
gh.login_as_app(key, app_id, expire_in=300)
install = gh.app_installation_for_repository(owner, repo)
gh.login_as_app_installation(key, app_id, install.id)
```

**PyGithub:**
```python
from github import Auth, Github, GithubIntegration

auth = Auth.AppAuth(app_id, private_key)
gi = GithubIntegration(auth=auth)
installation = gi.get_repo_installation(owner, repo)
auth = gi.get_access_token(installation.id)
gh = Github(auth=auth)
```

#### Repository Operations

**github3.py:**
```python
repo = gh.repository(owner, name)
pr = repo.pull_request(number)
commits = pr.commits()
```

**PyGithub:**
```python
repo = gh.get_repo(f"{owner}/{name}")
pr = repo.get_pull(number)
commits = pr.get_commits()
```

#### Pull Request Creation

**github3.py (with hack):**
```python
gh_pr = gh_app._post(
    f"https://api.github.com/repos/{dest.ns}/{dest.name}/pulls",
    data={
        "title": title,
        "head": head_branch,
        "head_repo": f"{head_ns}/{head_name}",
        "base": base_branch,
    },
    json=True,
)
```

**PyGithub (native):**
```python
repo = gh.get_repo(f"{dest.ns}/{dest.name}")
pr = repo.create_pull(
    title=title,
    body="",
    head=f"{head_ns}:{head_branch}",
    base=base_branch,
    maintainer_can_modify=False,
)
```

---

## Migration Strategy

### Approach: Incremental Migration with Feature Flags

We will use a phased approach to minimize risk:

1. **Phase 0:** Preparation & Setup
2. **Phase 1:** Dependency & Infrastructure
3. **Phase 2:** Authentication Layer
4. **Phase 3:** Core Operations
5. **Phase 4:** Pull Request Operations
6. **Phase 5:** Testing & Validation
7. **Phase 6:** Cleanup & Documentation

### Branch Strategy

```
main (protected)
  └── claude/migrate-to-pygithub-XXXXX (development)
      ├── checkpoint-1-dependencies
      ├── checkpoint-2-authentication
      ├── checkpoint-3-core-operations
      └── checkpoint-4-pr-operations
```

Each checkpoint will be a working, tested state that can be committed.

---

## Implementation Phases

### Phase 0: Preparation & Setup

**Duration:** 1-2 hours

#### Checkpoint 0.1: Environment Setup
- [ ] Create migration branch: `claude/migrate-to-pygithub-<session-id>`
- [ ] Document current behavior with integration tests
- [ ] Set up local testing environment
- [ ] Review all github3.py usage in codebase

#### Checkpoint 0.2: Baseline Tests
- [ ] Run existing test suite and document results
- [ ] Create snapshot of current functionality
- [ ] Document all GitHub API interactions

**Deliverables:**
- ✓ Migration branch created
- ✓ Baseline test results documented
- ✓ Current API usage catalog

---

### Phase 1: Dependency & Infrastructure

**Duration:** 1-2 hours

#### Checkpoint 1.1: Update Dependencies

**File:** `requirements.txt`

**Changes:**
```diff
 cryptography>=3.4.7
-github3.py>=3.0.0
+PyGithub>=2.8.0
 GitPython>=3.1.18
 requests>=2.26.0
 validators>=0.18.2
```

**Verification:**
```bash
pip install -r requirements.txt
python -c "import github; print(github.__version__)"
```

- [ ] Update `requirements.txt`
- [ ] Update `requirements-hacking.txt` if needed
- [ ] Install new dependencies locally
- [ ] Verify no conflicts with existing packages
- [ ] Test import: `import github`

#### Checkpoint 1.2: Update Type Stubs

**File:** `requirements-hacking.txt`

**Changes:**
```diff
 types-requests
+types-PyGithub
 mypy
```

- [ ] Add PyGithub type stubs
- [ ] Run `mypy` to check for type errors
- [ ] Document any type-related issues

**Deliverables:**
- ✓ Dependencies updated
- ✓ All packages install successfully
- ✓ No import conflicts

---

### Phase 2: Authentication Layer

**Duration:** 3-4 hours

#### Checkpoint 2.1: Update GitHub Provider Class

**File:** `rebasebot/github.py`

**Current Implementation:** Lines 85-217
**Target:** Complete rewrite of `GithubAppProvider` class

**Changes Required:**

1. **Update Imports**
```python
# OLD
import github3

# NEW
from github import Auth, Github, GithubIntegration, GithubException
```

2. **Rewrite `_github_login_app()` method** (lines 186-210)

**Old Code:**
```python
@staticmethod
def _github_login_app(credentials: GitHubAppCredentials) -> github3.GitHub:
    logging.info("Logging to GitHub as an Application for repository %s",
                 credentials.github_branch.url)
    gh_app = github3.GitHub()
    gh_app.login_as_app(credentials.app_key, credentials.app_id, expire_in=300)
    gh_branch = credentials.github_branch

    try:
        install = gh_app.app_installation_for_repository(
            owner=gh_branch.ns, repository=gh_branch.name
        )
    except github3.exceptions.NotFoundError as err:
        msg = (f"App has not been authorized by {gh_branch.ns}, or repo "
               f"{gh_branch.ns}/{gh_branch.name} does not exist")
        logging.error(msg)
        raise builtins.Exception(msg) from err

    gh_app.login_as_app_installation(credentials.app_key, credentials.app_id, install.id)
    return gh_app
```

**New Code:**
```python
@staticmethod
def _github_login_app(credentials: GitHubAppCredentials) -> Github:
    logging.info("Logging to GitHub as an Application for repository %s",
                 credentials.github_branch.url)
    gh_branch = credentials.github_branch

    # Create app authentication
    auth = Auth.AppAuth(credentials.app_id, credentials.app_key)
    gi = GithubIntegration(auth=auth)

    try:
        # Get installation for the repository
        installation = gi.get_repo_installation(gh_branch.ns, gh_branch.name)
    except GithubException as err:
        msg = (f"App has not been authorized by {gh_branch.ns}, or repo "
               f"{gh_branch.ns}/{gh_branch.name} does not exist")
        logging.error(msg)
        raise builtins.Exception(msg) from err

    # Get installation access token
    access_token = gi.get_access_token(installation.id)

    # Create authenticated Github instance
    auth = Auth.Token(access_token.token)
    gh_app = Github(auth=auth)

    return gh_app
```

3. **Rewrite `_get_github_user_logged_in_app()` method** (lines 212-216)

**Old Code:**
```python
def _get_github_user_logged_in_app(self) -> github3.GitHub:
    logging.info("Logging to GitHub as a User")
    gh_app = github3.GitHub()
    gh_app.login(token=self.user_token)
    return gh_app
```

**New Code:**
```python
def _get_github_user_logged_in_app(self) -> Github:
    logging.info("Logging to GitHub as a User")
    auth = Auth.Token(self.user_token)
    gh_app = Github(auth=auth)
    return gh_app
```

4. **Update Type Hints**
```python
# OLD
from typing import Optional
import github3

@cached_property
def github_app(self) -> github3.GitHub:
    ...

# NEW
from typing import Optional
from github import Github

@cached_property
def github_app(self) -> Github:
    ...
```

5. **Update Token Retrieval Methods** (lines 140-154)

**Old Code:**
```python
def get_app_token(self) -> str:
    return self.github_app.session.auth.token

def get_cloner_token(self) -> str:
    return self.github_cloner_app.session.auth.token
```

**New Code:**
```python
def get_app_token(self) -> str:
    # PyGithub stores auth differently
    auth = self.github_app._Github__requester.auth
    if isinstance(auth, Auth.Token):
        return auth.token
    # For app installations, we need to store the token separately
    # This will be handled in _github_login_app
    return self._app_token

def get_cloner_token(self) -> str:
    auth = self.github_cloner_app._Github__requester.auth
    if isinstance(auth, Auth.Token):
        return auth.token
    return self._cloner_token
```

**Note:** We'll need to store tokens as instance variables during login.

**Updated `_github_login_app()`:**
```python
@staticmethod
def _github_login_app(credentials: GitHubAppCredentials) -> tuple[Github, str]:
    """Returns tuple of (Github instance, access_token)"""
    # ... (auth code as above)
    access_token = gi.get_access_token(installation.id)
    auth = Auth.Token(access_token.token)
    gh_app = Github(auth=auth)

    return gh_app, access_token.token
```

Then update the callers to store the token.

#### Checkpoint 2.2: Update Exception Handling

**Search and Replace:**
```python
# OLD
import github3
except github3.exceptions.NotFoundError
except github3.exceptions.GithubException

# NEW
from github import GithubException, UnknownObjectException
except UnknownObjectException
except GithubException
```

**Files to check:**
- `rebasebot/github.py`
- `rebasebot/bot.py`

#### Checkpoint 2.3: Testing Authentication

**Test Cases:**
- [ ] GitHub App authentication works
- [ ] Installation token retrieval works
- [ ] User token authentication works
- [ ] Token retrieval methods return valid tokens
- [ ] Error handling for unauthorized repos

**Manual Test:**
```python
from rebasebot.github import GithubAppProvider, GitHubBranch

# Test with your credentials
provider = GithubAppProvider(
    app_id=YOUR_APP_ID,
    app_key=YOUR_APP_KEY,
    dest_branch=GitHubBranch(...),
    cloner_id=YOUR_CLONER_ID,
    cloner_key=YOUR_CLONER_KEY,
    rebase_branch=GitHubBranch(...),
)

gh = provider.github_app
print(f"Authenticated: {gh.get_user().login}")
token = provider.get_app_token()
print(f"Token length: {len(token)}")
```

**Deliverables:**
- ✓ Authentication layer completely migrated
- ✓ All auth tests passing
- ✓ Token retrieval working

---

### Phase 3: Core Operations

**Duration:** 4-6 hours

#### Checkpoint 3.1: Update Repository Operations

**File:** `rebasebot/bot.py`

**Locations:**
- Lines 709-714: Repository retrieval
- Line 84-105: PR merge checking
- Line 597-603: Manual rebase PR checking

**Changes:**

1. **Repository Retrieval** (lines 709-714)

**Old Code:**
```python
dest_repo = gh_app.repository(dest.ns, dest.name)
rebase_repo = gh_cloner_app.repository(rebase.ns, rebase.name)
source_repo = gh_app.repository(source.ns, source.name)
```

**New Code:**
```python
dest_repo = gh_app.get_repo(f"{dest.ns}/{dest.name}")
rebase_repo = gh_cloner_app.get_repo(f"{rebase.ns}/{rebase.name}")
source_repo = gh_app.get_repo(f"{source.ns}/{source.name}")
```

2. **Update Type Hints** (lines 30-32)

**Old Code:**
```python
from github3.pulls import ShortPullRequest
from github3.repos.commit import ShortCommit
from github3.repos.repo import Repository
```

**New Code:**
```python
from github.PullRequest import PullRequest
from github.Commit import Commit
from github.Repository import Repository
```

**Global Search/Replace:**
- `ShortPullRequest` → `PullRequest`
- `ShortCommit` → `Commit`

3. **PR Retrieval** (line 86)

**Old Code:**
```python
gh_pr = source_repo.pull_request(pr_number)
```

**New Code:**
```python
gh_pr = source_repo.get_pull(pr_number)
```

4. **Check PR Merged Status** (lines 88-94)

**Old Code:**
```python
if not gh_pr.is_merged():
    return False

merge_commit_sha = gh_pr.merge_commit_sha
```

**New Code:**
```python
if not gh_pr.merged:
    return False

merge_commit_sha = gh_pr.merge_commit_sha
```

5. **Pull Requests Iteration** (lines 398, 450, 598)

**Old Code:**
```python
for pull_request in dest_repo.pull_requests(state="open", base=f"{dest.branch}"):
    assert isinstance(pull_request, ShortPullRequest)  # type hint
```

**New Code:**
```python
for pull_request in dest_repo.get_pulls(state="open", base=dest.branch):
    # No need for assert, PyGithub has proper types
```

6. **PR Attributes** (line 400)

**Old Code:**
```python
pull_request.user.login
```

**New Code:**
```python
pull_request.user.login  # Same in PyGithub
```

7. **PR Commits** (line 411)

**Old Code:**
```python
for commit in pull_request.commits():
    assert isinstance(commit, ShortCommit)
```

**New Code:**
```python
for commit in pull_request.get_commits():
    # No assert needed
```

8. **PR Update** (line 634)

**Old Code:**
```python
if not pull_req.update(title=computed_title):
    raise builtins.Exception(f"Error updating title")
```

**New Code:**
```python
pull_req.edit(title=computed_title)
# PyGithub raises exception on failure, no return value check needed
```

#### Checkpoint 3.2: Update PR as_dict() Usage

**Location:** Line 454

**Old Code:**
```python
pr_repo = pr.as_dict()["head"]["repo"]["full_name"]
```

**New Code:**
```python
# PyGithub objects have direct attributes
pr_repo = pr.head.repo.full_name
```

#### Checkpoint 3.3: Update Labels Checking

**Location:** Line 601

**Old Code:**
```python
for label in pull_req.labels:
    if label['name'] == 'rebase/manual':
```

**New Code:**
```python
for label in pull_req.labels:
    if label.name == 'rebase/manual':
```

#### Checkpoint 3.4: Testing Core Operations

**Test Cases:**
- [ ] Repository retrieval works
- [ ] PR retrieval works
- [ ] PR merged status checking works
- [ ] PR iteration works
- [ ] PR commits retrieval works
- [ ] PR update/edit works
- [ ] Label checking works

**Deliverables:**
- ✓ All repository operations migrated
- ✓ All PR read operations working
- ✓ Type hints updated

---

### Phase 4: Pull Request Creation

**Duration:** 2-3 hours

#### Checkpoint 4.1: Replace PR Creation Hack

**File:** `rebasebot/bot.py`
**Location:** Lines 463-497

This is the **CRITICAL CHANGE** that eliminates the hack!

**Old Code:**
```python
def _create_pr(
        gh_app: github3.GitHub,
        dest: GitHubBranch,
        source: GitHubBranch,
        rebase: GitHubBranch,
        gitwd: git.Repo
) -> str:
    source_head_commit = gitwd.git.rev_parse(f"source/{source.branch}", short=7)

    logging.info("Creating a pull request")

    # FIXME(rmanak): This hack is because github3 doesn't support setting
    # head_repo param when creating a PR.
    #
    # This param is required when creating cross-repository pull requests if both repositories
    # are owned by the same organization.
    #
    # https://github.com/sigmavirus24/github3.py/issues/1190

    gh_pr: requests.Response = gh_app._post(  # pylint: disable=W0212
        f"https://api.github.com/repos/{dest.ns}/{dest.name}/pulls",
        data={
            "title": f"Merge {source.url}:{source.branch} ({source_head_commit}) into {dest.branch}",
            "head": rebase.branch,
            "head_repo": f"{rebase.ns}/{rebase.name}",
            "base": dest.branch,
            "maintainer_can_modify": False,
        },
        json=True,
    )

    logging.debug(gh_pr.json())
    gh_pr.raise_for_status()

    return gh_pr.json()["html_url"]
```

**New Code:**
```python
def _create_pr(
        gh_app: Github,
        dest: GitHubBranch,
        source: GitHubBranch,
        rebase: GitHubBranch,
        gitwd: git.Repo
) -> str:
    source_head_commit = gitwd.git.rev_parse(f"source/{source.branch}", short=7)

    logging.info("Creating a pull request")

    # PyGithub natively supports cross-repository PRs!
    # No hack needed - just specify the head as "namespace:branch"
    dest_repo = gh_app.get_repo(f"{dest.ns}/{dest.name}")

    pr = dest_repo.create_pull(
        title=f"Merge {source.url}:{source.branch} ({source_head_commit}) into {dest.branch}",
        body="",  # Empty body as in original
        head=f"{rebase.ns}:{rebase.branch}",  # Cross-repo format
        base=dest.branch,
        maintainer_can_modify=False,
    )

    logging.info(f"Created pull request: {pr.html_url}")

    return pr.html_url
```

**Key Changes:**
- ✅ Removed `requests.Response` import dependency
- ✅ Removed `_post()` hack
- ✅ Removed `# pylint: disable=W0212` comment
- ✅ Native cross-repo PR support via `namespace:branch` format
- ✅ Simplified error handling (PyGithub raises exceptions)
- ✅ Removed manual JSON parsing

#### Checkpoint 4.2: Update Error Handling

**Location:** Lines 890-897

**Old Code:**
```python
except requests.exceptions.HTTPError as ex:
    logging.error(f"Failed to create a pull request: {ex}\n Response: %s", ex.response.text)
    _message_slack(
        slack_webhook,
        f"Failed to create a pull request: {ex}\n Response: {ex.response.text}"
    )
    return False
```

**New Code:**
```python
except GithubException as ex:
    logging.error(f"Failed to create a pull request: {ex}")
    if ex.data:
        logging.error(f"Response data: {ex.data}")
    _message_slack(
        slack_webhook,
        f"Failed to create a pull request: {ex}"
    )
    return False
```

#### Checkpoint 4.3: Clean Up Imports

**File:** `rebasebot/bot.py`

**Remove:**
```python
import requests  # Line 28 - if only used for PR creation
```

**Check if `requests` is used elsewhere in the file. If not, remove it.**

**Add:**
```python
from github import GithubException
```

#### Checkpoint 4.4: Testing PR Creation

**Test Cases:**
- [ ] Cross-repository PR creation works
- [ ] PR title format is correct
- [ ] PR base/head branches are correct
- [ ] `maintainer_can_modify` flag is set correctly
- [ ] Error handling works for invalid repos
- [ ] Error handling works for permission issues

**Integration Test:**
```python
# Test cross-repo PR creation
# This would require actual GitHub repos and credentials
def test_cross_repo_pr_creation():
    # Use test repositories
    source = GitHubBranch("https://github.com/test-org/source", "test-org", "source", "main")
    dest = GitHubBranch("https://github.com/test-org/dest", "test-org", "dest", "main")
    rebase = GitHubBranch("https://github.com/test-org/rebase", "test-org", "rebase", "test-branch")

    # Create provider with test credentials
    provider = GithubAppProvider(...)

    # Mock gitwd
    gitwd = MagicMock()
    gitwd.git.rev_parse.return_value = "abc1234"

    # Call _create_pr
    pr_url = _create_pr(provider.github_app, dest, source, rebase, gitwd)

    assert "https://github.com" in pr_url
    assert "pull" in pr_url
```

**Deliverables:**
- ✓ PR creation hack completely removed
- ✓ Native cross-repo PR support implemented
- ✓ All PR creation tests passing
- ✓ Cleaner, more maintainable code

---

### Phase 5: Lifecycle Hooks & Minor Updates

**Duration:** 1-2 hours

#### Checkpoint 5.1: Update lifecycle_hooks.py

**File:** `rebasebot/lifecycle_hooks.py`

**Location:** Line 27

**Old Code:**
```python
from github3.repos.contents import Contents
```

**New Code:**
```python
from github.ContentFile import ContentFile
```

**Search for usages of `Contents` type:**

**Old:**
```python
def some_method(...) -> Contents:
    ...
```

**New:**
```python
def some_method(...) -> ContentFile:
    ...
```

#### Checkpoint 5.2: Update CLI Logging Suppression

**File:** `rebasebot/cli.py`

**Location:** Line 342

**Old Code:**
```python
# Silence info logs from github3
```

**New Code:**
```python
# Silence info logs from PyGithub
```

**Check if there's actual logging configuration:**

**Old:**
```python
logging.getLogger("github3").setLevel(logging.WARNING)
```

**New:**
```python
logging.getLogger("github").setLevel(logging.WARNING)
```

#### Checkpoint 5.3: Review Import Statements

**Run global search for all `github3` imports:**

```bash
grep -r "import github3" rebasebot/
grep -r "from github3" rebasebot/
```

**Replace all remaining imports:**
- `import github3` → `from github import Github`
- `from github3.xyz import ABC` → appropriate PyGithub import

**Deliverables:**
- ✓ All imports updated
- ✓ All type hints updated
- ✓ No references to github3 remain

---

### Phase 6: Testing & Validation

**Duration:** 4-6 hours

#### Checkpoint 6.1: Unit Tests Update

**File:** `tests/test_bot.py`, `tests/test_cli.py`, etc.

**Mock Objects to Update:**

**Old Mocks:**
```python
from unittest.mock import MagicMock
import github3

mock_gh = MagicMock(spec=github3.GitHub)
mock_repo = MagicMock(spec=github3.repos.repo.Repository)
```

**New Mocks:**
```python
from unittest.mock import MagicMock
from github import Github, Repository, PullRequest

mock_gh = MagicMock(spec=Github)
mock_repo = MagicMock(spec=Repository)
```

**Update Mock Behaviors:**

**Old:**
```python
mock_gh.repository.return_value = mock_repo
mock_repo.pull_request.return_value = mock_pr
```

**New:**
```python
mock_gh.get_repo.return_value = mock_repo
mock_repo.get_pull.return_value = mock_pr
```

#### Checkpoint 6.2: Integration Tests

**Test Scenarios:**

1. **Authentication Flow**
   - [ ] GitHub App installation auth works
   - [ ] User token auth works
   - [ ] Token retrieval works
   - [ ] Invalid credentials fail gracefully

2. **Repository Operations**
   - [ ] Get repository works
   - [ ] Get PR works
   - [ ] List PRs works
   - [ ] Check PR merged status works

3. **PR Operations**
   - [ ] Create same-repo PR works
   - [ ] Create cross-repo PR works (CRITICAL)
   - [ ] Update PR title works
   - [ ] Get PR commits works

4. **Edge Cases**
   - [ ] Non-existent repository
   - [ ] Non-existent PR
   - [ ] Unauthorized access
   - [ ] Rate limiting handling

#### Checkpoint 6.3: End-to-End Testing

**Create Test Script:**

```python
#!/usr/bin/env python3
"""
End-to-end test for PyGithub migration.

Tests the complete rebasebot flow with real GitHub repos (test environment).
"""

import os
import tempfile
from rebasebot.github import GithubAppProvider, GitHubBranch
from rebasebot.bot import run

def test_e2e_rebase():
    """Test complete rebase flow."""

    # Use test repositories
    source = GitHubBranch(
        url="https://github.com/test-org/source-repo",
        ns="test-org",
        name="source-repo",
        branch="main"
    )

    dest = GitHubBranch(
        url="https://github.com/test-org/dest-repo",
        ns="test-org",
        name="dest-repo",
        branch="main"
    )

    rebase = GitHubBranch(
        url="https://github.com/test-org/rebase-repo",
        ns="test-org",
        name="rebase-repo",
        branch="rebase-branch"
    )

    # Load test credentials
    app_id = int(os.environ["TEST_APP_ID"])
    app_key = os.environ["TEST_APP_KEY"].encode()

    provider = GithubAppProvider(
        app_id=app_id,
        app_key=app_key,
        dest_branch=dest,
        cloner_id=app_id,
        cloner_key=app_key,
        rebase_branch=rebase,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        result = run(
            source=source,
            dest=dest,
            rebase=rebase,
            working_dir=tmpdir,
            git_username="RebaseBot Test",
            git_email="test@example.com",
            github_app_provider=provider,
            slack_webhook=None,
            tag_policy="none",
            bot_emails=[],
            exclude_commits=[],
            dry_run=True,  # Don't actually create PRs
        )

    assert result is True, "Rebase operation failed"
    print("✓ End-to-end test passed!")

if __name__ == "__main__":
    test_e2e_rebase()
```

**Run Test:**
```bash
python tests/test_e2e_pygithub.py
```

#### Checkpoint 6.4: Regression Testing

**Test Checklist:**

- [ ] All existing unit tests pass
- [ ] All existing integration tests pass
- [ ] Code coverage maintained or improved
- [ ] No new linting errors
- [ ] Type checking passes (`mypy`)

**Commands:**
```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=rebasebot --cov-report=html

# Lint
flake8 rebasebot/
pylint rebasebot/

# Type check
mypy rebasebot/
```

**Deliverables:**
- ✓ All tests updated and passing
- ✓ Code coverage ≥ baseline
- ✓ No regressions identified
- ✓ E2E test confirms cross-repo PR works

---

### Phase 7: Documentation & Cleanup

**Duration:** 2-3 hours

#### Checkpoint 7.1: Update Documentation

**Files to Update:**

1. **README.md**
   - Update dependencies section
   - Mention PyGithub instead of github3.py
   - Update any code examples

2. **requirements.txt**
   - Already done in Phase 1

3. **Code Comments**
   - Remove FIXME comment at bot.py:474
   - Add comment explaining PyGithub native cross-repo support

4. **CHANGELOG.md** (create if doesn't exist)
```markdown
## [Unreleased]

### Changed
- Migrated from github3.py to PyGithub for better maintenance and support
- Replaced cross-repository PR creation hack with native PyGithub support

### Improved
- More robust error handling with PyGithub exceptions
- Better type hints support
- Updated to modern Python 3.8+ practices

### Removed
- Workaround for cross-repository PR creation
- Dependency on unmaintained github3.py library
```

#### Checkpoint 7.2: Code Cleanup

**Tasks:**
- [ ] Remove all commented-out github3 code
- [ ] Remove unused imports
- [ ] Update docstrings to reference PyGithub
- [ ] Format code with Black
- [ ] Sort imports with isort

**Commands:**
```bash
# Format
black rebasebot/

# Sort imports
isort rebasebot/

# Remove unused imports
autoflake --remove-all-unused-imports --recursive --in-place rebasebot/
```

#### Checkpoint 7.3: Update Type Hints

**Review and update all type hints:**

```python
# OLD
from typing import Optional
import github3

def foo() -> github3.GitHub:
    ...

# NEW
from typing import Optional
from github import Github

def foo() -> Github:
    ...
```

#### Checkpoint 7.4: Performance Validation

**Compare performance:**

1. **Measure API call counts**
   - Ensure we're not making more API calls than before
   - Check rate limit usage

2. **Measure execution time**
   - Run benchmark on typical rebase operation
   - Compare with baseline (if available)

3. **Memory usage**
   - Monitor memory during large operations

**Deliverables:**
- ✓ All documentation updated
- ✓ Code cleaned and formatted
- ✓ Type hints complete and accurate
- ✓ Performance validated

---

### Phase 8: Final Review & Deployment

**Duration:** 2-3 hours

#### Checkpoint 8.1: Code Review

**Self-Review Checklist:**

- [ ] All github3 references removed
- [ ] All imports updated
- [ ] All type hints updated
- [ ] All tests passing
- [ ] Documentation complete
- [ ] No TODOs or FIXMEs related to migration
- [ ] Error handling comprehensive
- [ ] Logging appropriate

**Automated Checks:**
```bash
# Final test run
pytest tests/ -v --cov=rebasebot

# Final lint
flake8 rebasebot/
pylint rebasebot/ --fail-under=8.0

# Final type check
mypy rebasebot/ --strict

# Security check
bandit -r rebasebot/
```

#### Checkpoint 8.2: Create Pull Request

**PR Checklist:**

- [ ] Branch pushed to remote
- [ ] All commits have clear messages
- [ ] PR title: "Migrate from github3.py to PyGithub"
- [ ] PR description includes:
  - Migration rationale
  - Key changes summary
  - Testing performed
  - Breaking changes (none expected)
  - Link to this migration plan

**PR Description Template:**

```markdown
## Migration: github3.py → PyGithub

### Summary
This PR migrates the rebasebot project from the unmaintained github3.py library to the actively maintained PyGithub library.

### Rationale
- github3.py has not been released since April 2023
- PyGithub is actively maintained (latest: Sept 2025)
- Native support for cross-repository PRs eliminates our hack at bot.py:482
- Better community support and modern Python practices

### Key Changes
1. **Authentication**: Rewritten using PyGithub's Auth module
2. **Repository Operations**: Updated all API calls to PyGithub equivalents
3. **PR Creation**: Removed hack, using native cross-repo PR support
4. **Error Handling**: Updated to use PyGithub exceptions
5. **Type Hints**: Full type hint support with PyGithub

### Testing
- ✅ All existing unit tests passing
- ✅ Integration tests updated and passing
- ✅ End-to-end test confirms functionality
- ✅ Cross-repository PR creation tested
- ✅ Code coverage maintained

### Breaking Changes
None. This is a drop-in replacement at the functionality level.

### Migration Plan
See [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) for detailed implementation plan.

### Closes
- Eliminates workaround for https://github.com/sigmavirus24/github3.py/issues/1190
```

#### Checkpoint 8.3: Deployment Preparation

**Pre-deployment Checklist:**

1. **Containerfile Update**
   - [ ] Verify dependencies install correctly in container
   - [ ] Test container build
   - [ ] Update base image if needed

2. **CI/CD Pipeline**
   - [ ] Ensure CI tests pass with new dependencies
   - [ ] Update any deployment scripts
   - [ ] Verify GitHub Actions workflows

3. **Rollback Plan Ready**
   - [ ] Document rollback procedure
   - [ ] Tag current production version
   - [ ] Ensure quick rollback is possible

**Test Container Build:**
```bash
# Build container
docker build -t rebasebot:pygithub-migration .

# Run tests in container
docker run --rm rebasebot:pygithub-migration pytest tests/

# Verify dependencies
docker run --rm rebasebot:pygithub-migration pip list | grep -i github
```

#### Checkpoint 8.4: Staged Rollout

**Deployment Strategy:**

1. **Stage 1: Canary (Optional)**
   - Deploy to test environment
   - Run for 24-48 hours
   - Monitor for issues

2. **Stage 2: Production**
   - Deploy to production
   - Monitor logs closely
   - Watch for rate limiting issues
   - Verify PR creation works

3. **Stage 3: Verification**
   - Confirm first production PR created successfully
   - Verify no errors in logs
   - Check GitHub API rate limit status

**Monitoring:**
```bash
# Watch logs for errors
tail -f /var/log/rebasebot.log | grep -i error

# Check GitHub API rate limit
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/rate_limit
```

**Deliverables:**
- ✓ Code reviewed and approved
- ✓ PR created and merged
- ✓ Container builds successfully
- ✓ Deployed to production
- ✓ Verified working in production

---

## Testing Strategy

### Testing Pyramid

```
        ╱╲
       ╱E2E╲          1-2 tests (complete workflow)
      ╱▔▔▔▔▔▔╲
     ╱Integration╲     5-10 tests (API interactions)
    ╱▔▔▔▔▔▔▔▔▔▔▔▔╲
   ╱   Unit Tests   ╲  20-30 tests (individual functions)
  ╱▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔╲
```

### Test Categories

#### 1. Unit Tests

**Authentication:**
- `test_github_app_login()` - Test GitHub App authentication
- `test_user_token_login()` - Test user token authentication
- `test_get_app_token()` - Test token retrieval
- `test_auth_failure()` - Test authentication failure handling

**Repository Operations:**
- `test_get_repository()` - Test repository retrieval
- `test_repository_not_found()` - Test 404 handling
- `test_unauthorized_repository()` - Test 403 handling

**PR Operations:**
- `test_get_pull_request()` - Test PR retrieval
- `test_check_pr_merged()` - Test merged status check
- `test_list_pull_requests()` - Test PR listing
- `test_pr_update()` - Test PR title update

#### 2. Integration Tests

**Cross-Repository PR:**
- `test_create_cross_repo_pr()` - **CRITICAL** - Test cross-repo PR creation
- `test_same_org_cross_repo_pr()` - Test same-org cross-repo PR

**Complete Auth Flow:**
- `test_app_installation_flow()` - Test complete app installation auth

**Error Scenarios:**
- `test_rate_limit_handling()` - Test rate limit responses
- `test_network_error_handling()` - Test network failures

#### 3. End-to-End Tests

**Complete Rebase Workflow:**
- `test_full_rebase_flow()` - Test complete rebase operation
- `test_dry_run_mode()` - Test dry-run mode

### Test Data

**Mock Repositories:**
```python
# Test fixtures
TEST_SOURCE_REPO = {
    "ns": "test-org",
    "name": "source-repo",
    "branch": "main"
}

TEST_DEST_REPO = {
    "ns": "test-org",
    "name": "dest-repo",
    "branch": "main"
}

TEST_REBASE_REPO = {
    "ns": "test-org",
    "name": "rebase-repo",
    "branch": "rebase-branch"
}
```

### Coverage Goals

- **Line Coverage:** ≥ 80%
- **Branch Coverage:** ≥ 70%
- **Critical Paths:** 100% (auth, PR creation)

---

## Rollback Plan

### Triggers for Rollback

Rollback immediately if:
1. Production PR creation fails
2. Authentication failures occur
3. Rate limiting issues emerge
4. Critical bugs discovered in production
5. Data integrity issues

### Rollback Procedure

#### Quick Rollback (< 5 minutes)

**Step 1: Revert Dependencies**
```bash
cd /path/to/rebasebot

# Checkout previous version
git checkout <previous-production-tag>

# Reinstall dependencies
pip install -r requirements.txt

# Restart service
systemctl restart rebasebot
```

**Step 2: Verify**
```bash
# Check service status
systemctl status rebasebot

# Verify github3.py is active
python -c "import github3; print(github3.__version__)"

# Monitor logs
tail -f /var/log/rebasebot.log
```

#### Full Rollback with PR Revert

**Step 1: Revert Merge Commit**
```bash
# Find merge commit
git log --oneline | grep "Migrate from github3.py"

# Revert the merge
git revert -m 1 <merge-commit-sha>

# Push revert
git push origin main
```

**Step 2: Redeploy**
```bash
# Trigger deployment pipeline
# Or manual deployment
./deploy.sh
```

### Post-Rollback Actions

1. **Investigate root cause**
2. **Document the issue**
3. **Create fix in migration branch**
4. **Re-test thoroughly**
5. **Attempt migration again**

---

## Timeline & Resources

### Estimated Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 0: Preparation | 1-2 hours | 2 hours |
| Phase 1: Dependencies | 1-2 hours | 4 hours |
| Phase 2: Authentication | 3-4 hours | 8 hours |
| Phase 3: Core Operations | 4-6 hours | 14 hours |
| Phase 4: PR Creation | 2-3 hours | 17 hours |
| Phase 5: Lifecycle Hooks | 1-2 hours | 19 hours |
| Phase 6: Testing | 4-6 hours | 25 hours |
| Phase 7: Documentation | 2-3 hours | 28 hours |
| Phase 8: Deployment | 2-3 hours | 31 hours |

**Total Estimated Time:** 25-31 hours (3-4 working days)

### Resource Requirements

**Human Resources:**
- 1 Developer (primary implementer)
- 1 Reviewer (code review)
- 1 QA Engineer (optional, for testing)

**Infrastructure:**
- Development environment with GitHub access
- Test GitHub repositories for E2E testing
- CI/CD pipeline for automated testing
- Staging environment (optional but recommended)

**Access Requirements:**
- GitHub App credentials for testing
- Access to production repositories (read-only for testing)
- CI/CD pipeline access

---

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Severity | Mitigation |
|------|------------|--------|----------|------------|
| Authentication breaks in production | Low | High | **HIGH** | Comprehensive auth testing, staged rollout |
| Cross-repo PR fails | Low | High | **HIGH** | Dedicated integration test, verify in staging |
| API rate limiting issues | Medium | Medium | **MEDIUM** | Monitor rate limits, implement backoff |
| Incomplete migration | Low | Medium | **MEDIUM** | Thorough code review, automated checks |
| Breaking changes in PyGithub | Low | Low | **LOW** | Pin version in requirements.txt |
| Performance degradation | Low | Low | **LOW** | Benchmark before/after |

### Mitigation Strategies

#### High-Severity Risks

**1. Authentication Breakage**
- **Prevention:**
  - Unit tests for all auth methods
  - Integration tests with real GitHub
  - Staging environment testing
  - Manual verification before production

- **Detection:**
  - Monitor authentication errors in logs
  - Alert on repeated auth failures

- **Response:**
  - Immediate rollback if auth fails
  - Fallback to github3.py

**2. Cross-Repo PR Failure**
- **Prevention:**
  - Dedicated integration test
  - Test with actual repositories
  - Verify same-org scenario specifically

- **Detection:**
  - Monitor PR creation failures
  - Alert on 422/403 errors from GitHub API

- **Response:**
  - Rollback to github3 hack
  - Debug with GitHub API logs

#### Medium-Severity Risks

**3. Rate Limiting**
- **Prevention:**
  - Review API call patterns
  - Implement exponential backoff
  - Use conditional requests where possible

- **Detection:**
  - Monitor X-RateLimit-Remaining headers
  - Alert at 20% remaining

- **Response:**
  - Increase delay between operations
  - Use GitHub App installation tokens (higher limits)

**4. Incomplete Migration**
- **Prevention:**
  - Comprehensive checklist
  - Automated grep for github3 imports
  - Code review

- **Detection:**
  - Import errors
  - Test failures

- **Response:**
  - Fix missing migrations
  - Re-test

### Contingency Plans

**Plan A: Normal Migration**
- Follow all phases sequentially
- Comprehensive testing at each checkpoint
- Deploy to production after all tests pass

**Plan B: Issues Found During Testing**
- Fix issues in migration branch
- Re-test affected areas
- Continue migration when stable

**Plan C: Critical Issues in Production**
- Immediate rollback to github3.py
- Root cause analysis
- Fix in development
- Re-attempt migration with fixes

**Plan D: PyGithub Has Breaking Changes**
- Pin to specific working version
- Investigate workarounds
- Consider alternative library if necessary

---

## Success Criteria

### Must-Have (Blocking)

- ✅ All existing tests pass
- ✅ Cross-repository PR creation works
- ✅ Authentication works for all methods
- ✅ No github3 imports remain
- ✅ Code coverage maintained or improved
- ✅ Production deployment successful
- ✅ First production PR created successfully

### Should-Have (Important)

- ✅ Type hints complete and accurate
- ✅ Documentation updated
- ✅ Performance maintained or improved
- ✅ Error handling comprehensive
- ✅ Logging appropriate and helpful

### Nice-to-Have (Optional)

- ⭐ Improved code organization
- ⭐ Additional test coverage
- ⭐ Performance improvements
- ⭐ Better error messages

### Metrics

**Pre-Migration Baseline:**
- github3.py version: 3.0.0+
- Test coverage: TBD%
- Average rebase time: TBD
- API calls per rebase: TBD

**Post-Migration Target:**
- PyGithub version: 2.8.0+
- Test coverage: ≥ baseline
- Average rebase time: ≤ baseline + 10%
- API calls per rebase: ≤ baseline

---

## Appendix

### A. API Comparison Cheat Sheet

| Operation | github3.py | PyGithub |
|-----------|-----------|----------|
| **Import** | `import github3` | `from github import Github` |
| **Create instance** | `gh = github3.GitHub()` | `gh = Github()` |
| **User auth** | `gh.login(token=token)` | `gh = Github(auth=Auth.Token(token))` |
| **App auth** | `gh.login_as_app(key, id)` | `auth = Auth.AppAuth(id, key); gh = Github(auth=auth)` |
| **Get repo** | `repo = gh.repository(owner, name)` | `repo = gh.get_repo(f"{owner}/{name}")` |
| **Get PR** | `pr = repo.pull_request(num)` | `pr = repo.get_pull(num)` |
| **List PRs** | `prs = repo.pull_requests(state="open")` | `prs = repo.get_pulls(state="open")` |
| **Create PR** | `repo.create_pull(...)` | `repo.create_pull(...)` |
| **PR merged?** | `pr.is_merged()` | `pr.merged` |
| **PR commits** | `pr.commits()` | `pr.get_commits()` |
| **Update PR** | `pr.update(title="...")` | `pr.edit(title="...")` |
| **Exceptions** | `github3.exceptions.NotFoundError` | `github.UnknownObjectException` |
| **Exception base** | `github3.exceptions.GitHubException` | `github.GithubException` |

### B. Common Gotchas

1. **Method vs Property**
   - github3: `pr.is_merged()` (method)
   - PyGithub: `pr.merged` (property)

2. **Get vs Direct Access**
   - github3: `repo.pull_request(123)`
   - PyGithub: `repo.get_pull(123)` (note the `get_` prefix)

3. **Repository Specification**
   - github3: `gh.repository("owner", "name")`
   - PyGithub: `gh.get_repo("owner/name")` (combined string)

4. **Dictionary vs Object**
   - github3: Often returns dicts, e.g., `pr.as_dict()["head"]["repo"]`
   - PyGithub: Proper objects, e.g., `pr.head.repo`

5. **Exception Names**
   - github3: `NotFoundError`, `ForbiddenError`
   - PyGithub: `UnknownObjectException`, `GithubException`

6. **Token Access**
   - github3: `gh.session.auth.token`
   - PyGithub: Token stored in Auth object, need to track separately

### C. Useful Resources

**PyGithub Documentation:**
- Official Docs: https://pygithub.readthedocs.io/
- GitHub Repo: https://github.com/PyGithub/PyGithub
- Examples: https://pygithub.readthedocs.io/en/latest/examples.html

**Migration Guides:**
- PyGithub Quickstart: https://pygithub.readthedocs.io/en/latest/introduction.html
- GitHub API Reference: https://docs.github.com/en/rest

**Testing Resources:**
- pytest Documentation: https://docs.pytest.org/
- Mock Documentation: https://docs.python.org/3/library/unittest.mock.html

**GitHub App Auth:**
- GitHub Apps Docs: https://docs.github.com/en/apps
- PyGithub Auth Module: https://pygithub.readthedocs.io/en/latest/github.html#github.Auth

### D. Contact & Support

**For Questions:**
- Rebasebot maintainers (see OWNERS file)
- PyGithub community: https://github.com/PyGithub/PyGithub/discussions

**For Issues:**
- Internal issue tracker
- PyGithub issues: https://github.com/PyGithub/PyGithub/issues

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-08 | Claude AI | Initial migration plan created |

---

## Approval

**Plan Approved By:**
- [ ] Project Maintainer: _________________ Date: _________
- [ ] Technical Lead: _________________ Date: _________
- [ ] QA Lead: _________________ Date: _________

**Deployment Approved By:**
- [ ] Project Maintainer: _________________ Date: _________
- [ ] Operations: _________________ Date: _________

---

*End of Migration Plan*
