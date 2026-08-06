# Design: Builtin go modules hook without vendoring

## Problem

Downstream repos that do not keep a `vendor/` tree (e.g. Konflux/Cachi2 builds) still need rebasebot to reset and tidy Go modules after an upstream rebase. The existing `_BUILTIN_/update_go_modules.sh` always runs `go mod vendor` / `go work vendor`, which is wrong for those consumers.

## Goals

- Provide a builtin lifecycle hook that matches `update_go_modules.sh` except it does not vendor.
- Invoke via existing `--post-rebase-hook` only (no new CLI flag).
- Document the hook in the README.
- Leave `--update-go-modules` and `update_go_modules.sh` behavior unchanged.

## Non-goals

- New CLI flag (e.g. `--update-go-modules-no-vendor`).
- Sharing/refactoring logic between the vendoring and no-vendor scripts.
- Changing bot.py go-mod carry/squash special-casing tied to `--update-go-modules`.
- Auto-attaching this hook from any existing flag.

## Behavior

New script: `rebasebot/builtin-hooks/update_go_modules_no_vendor.sh`, available as `_BUILTIN_/update_go_modules_no_vendor.sh`.

It is a copy of `update_go_modules.sh` with these differences only:

| Step | Vendoring script (unchanged) | No-vendor script |
|------|------------------------------|------------------|
| Require `REBASEBOT_SOURCE` | yes | yes |
| Reset `go.mod` / `go.sum` from `source/$REBASEBOT_SOURCE` | yes | yes |
| `go.work` path: reset `go.work` / `go.work.sum`, `go work sync` | yes | yes |
| `go.work` path: `go work vendor` | yes | **no** |
| Per-module path: `go mod tidy` | yes | yes |
| Per-module path: `go mod vendor` | yes | **no** |
| Stage and commit when dirty | yes | yes |
| Commit message | `UPSTREAM: <drop>: Updating and vendoring go modules after an upstream rebase` | `UPSTREAM: <drop>: Updating go modules after an upstream rebase` |

Invocation:

```sh
rebasebot ... --post-rebase-hook _BUILTIN_/update_go_modules_no_vendor.sh
```

Error handling matches the existing script: non-zero from tidy/sync (or missing `REBASEBOT_SOURCE`, unsupported downstream-only `go.work`) fails the hook and thus the rebase lifecycle.

## Implementation approach

Duplicate the existing builtin script (approach chosen over a shared parameterized script) so the vendoring path stays untouched and review stays small.

Files to add/change:

1. `rebasebot/builtin-hooks/update_go_modules_no_vendor.sh` — new script as above.
2. `README.md` — document under Golang vendor update (sibling subsection for no-vendor) and list under Builtin lifecycle hook scripts.
3. `tests/test_bot.py` — tests mirroring `TestGoMod` for the new script: commits with the new message; does not introduce a `vendor/` tree when the vendoring script would.

No changes to `lifecycle_hooks.py` or `cli.py` beyond what README describes for callers.

## Testing

- Unit/integration style tests like existing `TestGoMod`, invoking `LifecycleHookScript("_BUILTIN_/update_go_modules_no_vendor.sh")`.
- Assert commit message is the no-vendor string.
- Assert no `vendor/` directory is created when dependencies are present (contrast with vendoring script behavior where applicable).
- Existing `update_go_modules.sh` tests remain green.

## Docs

- README: explain when to use the no-vendor builtin vs `--update-go-modules` / `update_go_modules.sh`.
- Show the `_BUILTIN_/update_go_modules_no_vendor.sh` post-rebase-hook example.
