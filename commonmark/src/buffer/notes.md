# Buffer status — Sol (OpenAI)

Blocked before implementation. The frozen contract cannot be implemented with
the pinned public compiler at `3a45b7c4`: Part 1 requires a module-level function
named `buffer_new`, but Nitpick reserves that name for its built-in constructor
`buffer_new(int64) -> buffer never fails`.

The buffer brief explicitly requires stopping and raising a contract mismatch
instead of silently changing the API. No replacement API or partial buffer
implementation has been added. Manager action: approve a contract change giving
the port's constructor a non-reserved name (for example `cm_buffer_new`) and
update the affected callers and test contracts.

## Reproduction and checks

Smallest reproduction, kept in `checks/reserved_name.npk`:

```nitpick
mod:reserved_name;
pub func:buffer_new = NIL() { pass NIL; };
```

The return type is reduced to NIL because the rejection depends only on the
function's name. The contract's owning Buffer return type cannot change this
resolution rule.

From the repository root, run:

```sh
python3 commonmark/src/buffer/checks/check.py
```

`checks/blocker.log` records the compiler commit, compiler SHA-256, exact
commands, exit statuses, and diagnostics for both intended optimization
pipelines. Both stop at resolution, before IR emission, so neither -O0 nor -O2
can be linked or run. The negative reproduction check passes; buffer behavior
tests have not run, and this piece is not complete.

## Compiler notes

This is a documented language restriction, not a new compiler fault. Checked
`/home/outside/jobs/lab/context/known-issues.md` before classifying it; no listed
fault matches. The pin's `meta/specs/BUILTIN_REFERENCE.md` documents D-294 in its
preamble (module-level functions cannot take bare-name builtin names) and lists
`buffer_new` as a builtin. `meta/specs/TYPE_REFERENCE.md` section 23 confirms its
existing signature. Actual result: exit 1, `NITPICK-RESOLVE-001`, asking that the
function be renamed. Expected according to those language documents: the same
rejection. Required by the project contract: a declaration the compiler refuses.

## Handoff

All files written are under `commonmark/src/buffer/`, as permitted by
`commonmark/assign/sol.txt`. No commit was possible: this workspace's `.git` is
an empty read-only directory rather than a Git repository, and Git metadata is
outside the allowed write paths.
