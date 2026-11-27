# Notes: compiler notes and open questions

Manager: Muse Wonder (Meta). Compiler notes from the parts are gathered here from the writers' per-folder notes before each pull request, and repeated in the pull request under "Compiler notes", as the project guide requires.

## Compiler notes

(none yet — no part has been written)

## Pending contract fixes (from management's merge review of PR #1, 2026-11-27)

Two one-line slips in `INTERFACES.md`, approved as non-blocking at the merge; they go into the first contract-change pull request:

- The import graph omits `cm_scan` from `cm_html`'s imports, though Part 9's text has `render_html` using `scan_dangerous_url`. Add `cm_scan` (a leaf — no cycle).
- The driver pipeline sketch writes `parser_finish(move parser)`; the notation section's spelling is `move(...)`. Make it `move(parser)`.
