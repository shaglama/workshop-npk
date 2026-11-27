# Notes: compiler notes and open questions

Manager: Muse Wonder (Meta). Compiler notes from the parts are gathered here from the writers' per-folder notes before each pull request, and repeated in the pull request under "Compiler notes", as the project guide requires.

## Compiler notes

(none yet — no part has been written)

## Contract changes in flight

From management's merge review of PR #1 (2026-11-27), two one-line slips in `INTERFACES.md`, approved as non-blocking at the merge. Both are included in contract-change PR #2 (opened 2026-11-27):

- The import graph omits `cm_scan` from `cm_html`'s imports, though Part 9's text has `render_html` using `scan_dangerous_url`. Add `cm_scan` (a leaf — no cycle).
- The driver pipeline sketch writes `parser_finish(move parser)`; the notation section's spelling is `move(...)`. Make it `move(parser)`.

Also in PR #2: `buffer_new` renamed to `buffer_create`. `buffer_new` is a compiler builtin at the pin (`int64 → buffer`, the prelude byte cell's constructor — BUILTIN_REFERENCE), so the port's constructor cannot use the name. Sol (writing `buffer`) hit this and stopped, correctly, for a manager-approved rename. The rest of the contract's names were checked against the pin's prelude, library and specs: no other collisions.
