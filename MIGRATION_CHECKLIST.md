# PyGithub Migration - Implementation Checklist

**Quick reference checklist for implementing the migration.**
**See MIGRATION_PLAN.md for detailed instructions.**

---

## Phase 0: Preparation ⏱️ 1-2 hours

- [ ] Create migration branch
- [ ] Run baseline tests and document results
- [ ] Set up local testing environment

---

## Phase 1: Dependencies ⏱️ 1-2 hours

- [ ] Update `requirements.txt`: `github3.py>=3.0.0` → `PyGithub>=2.8.0`
- [ ] Add `types-PyGithub` to `requirements-hacking.txt`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify import: `python -c "import github; print(github.__version__)"`

---

## Phase 2: Authentication Layer ⏱️ 3-4 hours

### rebasebot/github.py

- [ ] Update imports:
  ```python
  # OLD: import github3
  # NEW: from github import Auth, Github, GithubIntegration, GithubException
  ```

- [ ] Rewrite `_github_login_app()` method (lines 186-210)
  - [ ] Use `Auth.AppAuth()` and `GithubIntegration()`
  - [ ] Get installation with `gi.get_repo_installation()`
  - [ ] Get access token with `gi.get_access_token()`
  - [ ] Return authenticated `Github` instance

- [ ] Rewrite `_get_github_user_logged_in_app()` method (lines 212-216)
  - [ ] Use `Auth.Token(self.user_token)`
  - [ ] Return `Github(auth=auth)`

- [ ] Update `get_app_token()` and `get_cloner_token()` methods
  - [ ] Store tokens during login process
  - [ ] Return stored tokens

- [ ] Update type hints:
  - [ ] `github3.GitHub` → `Github`

- [ ] Update exception handling:
  - [ ] `github3.exceptions.NotFoundError` → `GithubException`

- [ ] **Test authentication thoroughly**

---

## Phase 3: Core Operations ⏱️ 4-6 hours

### rebasebot/bot.py

- [ ] Update imports (lines 25-32):
  ```python
  # OLD: import github3
  # OLD: from github3.pulls import ShortPullRequest
  # OLD: from github3.repos.commit import ShortCommit
  # OLD: from github3.repos.repo import Repository

  # NEW: from github import Github, GithubException
  # NEW: from github.PullRequest import PullRequest
  # NEW: from github.Commit import Commit
  # NEW: from github.Repository import Repository
  ```

- [ ] Update repository retrieval (lines 709-714):
  - [ ] `gh.repository(ns, name)` → `gh.get_repo(f"{ns}/{name}")`

- [ ] Update PR retrieval (line 86):
  - [ ] `repo.pull_request(num)` → `repo.get_pull(num)`

- [ ] Update PR merged check (line 88):
  - [ ] `pr.is_merged()` → `pr.merged`

- [ ] Update PR iteration (lines 398, 450, 598):
  - [ ] `repo.pull_requests()` → `repo.get_pulls()`
  - [ ] Remove `assert isinstance()` type hints

- [ ] Update PR commits (line 411):
  - [ ] `pr.commits()` → `pr.get_commits()`

- [ ] Update PR attributes (line 454):
  - [ ] `pr.as_dict()["head"]["repo"]["full_name"]` → `pr.head.repo.full_name`

- [ ] Update labels (line 601):
  - [ ] `label['name']` → `label.name`

- [ ] Update PR update (line 634):
  - [ ] `pr.update(title=...)` → `pr.edit(title=...)`
  - [ ] Remove return value check (PyGithub raises on error)

- [ ] **Test all core operations**

---

## Phase 4: PR Creation (CRITICAL) ⏱️ 2-3 hours

### rebasebot/bot.py - _create_pr() function

- [ ] **Remove the entire hack** (lines 463-497)

- [ ] Replace with native PyGithub implementation:
  ```python
  def _create_pr(
          gh_app: Github,  # Updated type hint
          dest: GitHubBranch,
          source: GitHubBranch,
          rebase: GitHubBranch,
          gitwd: git.Repo
  ) -> str:
      source_head_commit = gitwd.git.rev_parse(f"source/{source.branch}", short=7)
      logging.info("Creating a pull request")

      dest_repo = gh_app.get_repo(f"{dest.ns}/{dest.name}")
      pr = dest_repo.create_pull(
          title=f"Merge {source.url}:{source.branch} ({source_head_commit}) into {dest.branch}",
          body="",
          head=f"{rebase.ns}:{rebase.branch}",  # Cross-repo format!
          base=dest.branch,
          maintainer_can_modify=False,
      )

      logging.info(f"Created pull request: {pr.html_url}")
      return pr.html_url
  ```

- [ ] Update error handling (lines 890-897):
  - [ ] `requests.exceptions.HTTPError` → `GithubException`
  - [ ] Update error message format

- [ ] Remove `requests` import if only used for PR creation

- [ ] **Test cross-repository PR creation** (MOST CRITICAL TEST)

---

## Phase 5: Lifecycle Hooks ⏱️ 1-2 hours

### rebasebot/lifecycle_hooks.py

- [ ] Update imports (line 27):
  - [ ] `from github3.repos.contents import Contents` → `from github.ContentFile import ContentFile`

- [ ] Update type hints:
  - [ ] `Contents` → `ContentFile`

### rebasebot/cli.py

- [ ] Update comment (line 342):
  - [ ] "Silence info logs from github3" → "Silence info logs from PyGithub"

- [ ] Update logger name if present:
  - [ ] `logging.getLogger("github3")` → `logging.getLogger("github")`

- [ ] **Search for any remaining github3 references:**
  ```bash
  grep -r "github3" rebasebot/
  ```

---

## Phase 6: Testing ⏱️ 4-6 hours

### Update Test Mocks

- [ ] Update mock imports in test files
- [ ] Update mock specs:
  - [ ] `MagicMock(spec=github3.GitHub)` → `MagicMock(spec=Github)`
- [ ] Update mock method calls:
  - [ ] `.repository()` → `.get_repo()`
  - [ ] `.pull_request()` → `.get_pull()`

### Run Tests

- [ ] Run unit tests: `pytest tests/test_bot.py -v`
- [ ] Run all tests: `pytest tests/ -v`
- [ ] Check coverage: `pytest tests/ --cov=rebasebot --cov-report=html`
- [ ] Run linting: `flake8 rebasebot/`
- [ ] Run type check: `mypy rebasebot/`

### Integration Testing

- [ ] Test authentication flow end-to-end
- [ ] Test repository operations
- [ ] **Test cross-repository PR creation** (CRITICAL)
- [ ] Test error scenarios

### E2E Testing

- [ ] Create E2E test script (see migration plan)
- [ ] Run with test repositories
- [ ] Verify complete workflow

---

## Phase 7: Documentation ⏱️ 2-3 hours

- [ ] Update README.md (if it mentions github3.py)
- [ ] Create/update CHANGELOG.md
- [ ] Remove FIXME comment at bot.py:~474
- [ ] Update docstrings
- [ ] Format code: `black rebasebot/`
- [ ] Sort imports: `isort rebasebot/`
- [ ] Remove unused imports

---

## Phase 8: Deployment ⏱️ 2-3 hours

### Pre-Deployment

- [ ] All tests passing ✅
- [ ] Code review complete ✅
- [ ] Documentation updated ✅
- [ ] Container builds successfully ✅

### Commit & Push

- [ ] Commit all changes with clear message
- [ ] Push to migration branch
- [ ] Create pull request

### Deployment

- [ ] Deploy to staging (if available)
- [ ] Test in staging environment
- [ ] Deploy to production
- [ ] Monitor logs for errors
- [ ] Verify first production PR created

---

## Rollback (If Needed)

If anything goes wrong:

```bash
# Quick rollback
git checkout <previous-tag>
pip install -r requirements.txt
systemctl restart rebasebot

# Or revert merge commit
git revert -m 1 <merge-commit-sha>
git push origin main
```

---

## Success Criteria

✅ All tests passing
✅ Cross-repository PR works natively
✅ No github3 references remain
✅ Production deployment successful
✅ First production PR created successfully

---

## Estimated Total Time

**25-31 hours** (3-4 working days)

---

## Critical Items 🔥

1. **Authentication** - Must work flawlessly
2. **Cross-repo PR creation** - Main reason for migration
3. **Comprehensive testing** - Before production deployment
4. **Rollback plan ready** - In case of issues

---

*For detailed instructions, see MIGRATION_PLAN.md*
