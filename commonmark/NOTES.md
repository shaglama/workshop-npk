# Notes: compiler notes and open questions

Manager: Muse Wonder (Meta). Compiler notes from the parts are gathered here from the writers' per-folder notes before each pull request, and repeated in the pull request under "Compiler notes", as the project guide requires.

## Compiler notes

(none so far — `buffer` and `utf8` reported none, and the manager's re-runs agreed)

## Spec-wording observations

- **String-literal `\xNN` escapes (from Neon, writing `utf8`; manager-verified 2026-11-27).** In a `string` literal, `"\xFF"` is the character U+00FF — two UTF-8 bytes (`s.len` is 2; smallest program in `src/utf8/notes.md`, re-run at the pin, -O0, exit 2 as reported) — while a `char8` literal `'\xFF'` is one byte (TYPE_REFERENCE §2.2). LEXICAL_REFERENCE §6.3 does not state the string-literal behaviour. The behaviour is self-consistent (a `string` is text, a `char8` is a byte); the gap is in the wording. Practical consequence for the port: tests needing raw bytes 0x80–0xFF build them with `buffer_putc`, not `\xNN` escapes.

## Contract changes in flight

From management's merge review of PR #1 (2026-11-27), two one-line slips in `INTERFACES.md`, approved as non-blocking at the merge. Both are included in contract-change PR #3 (opened 2026-11-27):

- The import graph omits `cm_scan` from `cm_html`'s imports, though Part 9's text has `render_html` using `scan_dangerous_url`. Add `cm_scan` (a leaf — no cycle).
- The driver pipeline sketch writes `parser_finish(move parser)`; the notation section's spelling is `move(...)`. Make it `move(parser)`.

Also in PR #3: `buffer_new` renamed to `buffer_create`. `buffer_new` is a compiler builtin at the pin (`int64 → buffer`, the prelude byte cell's constructor — BUILTIN_REFERENCE), so the port's constructor cannot use the name. Sol (writing `buffer`) hit this and stopped, correctly, for a manager-approved rename. The rest of the contract's names were checked against the pin's prelude, library and specs: no other collisions.

## Contract amendment: `clean_url` / `clean_title` order (2026-11-27)

The frozen contract's one-line summaries stated the cleaning steps in the wrong order — the manager's paraphrase error, caught by Neon while writing `escape` and verified by the manager against cmark 0.31.2's `src/inlines.c`: `cmark_clean_url` trims **first** (`cmark_chunk_trim`), then entity-unescapes, then backslash-unescapes; `cmark_clean_title` does not trim at all — it strips a matching pair of outer delimiters (when the chunk is at least 2 bytes), then entity-unescapes, then backslash-unescapes. Neon's implementation follows cmark, which is correct (spec example 193 turns on title whitespace surviving); the contract text is amended to match by a contract-change PR, and the escape brief's paraphrase of the order is corrected with it. Nothing else had been written against the wrong summary, so no part needs rework.
