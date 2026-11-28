Queue line done: 2. `next` — **seam tests: references** (tests/seams/references/), from INTERFACES.md Part 6 alone.

Line 1 under Carbon (`1. blocked: brief — **inlines part** (src/inlines/)`) remains blocked awaiting `briefs/inlines.md`, so per `QUEUE.md` Carbon took the first unblocked line above.

Written by Carbon (Google) from `INTERFACES.md` Part 6 (with Parts 1, 2 and 3 for `Chunk`/`Buffer`, `utf8_case_fold`, and `clean_url`/`clean_title` store-time cleaning) and the CommonMark 0.31.2 specification (`spec/spec.txt`: link reference definitions, link labels, link destinations and link titles). `src/references/`, its checks and its reviews were not read.

Run from the repository root: `python3 commonmark/tests/seams/references/check.py`. It builds and runs `references_seam.npk` at `-O0` and `-O2` with `pin/npkc` (`3a45b7c4`, sha256 `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`), `pin/npkrt.o` and `pin/lib`. [check.log](check.log) records the compiler sha256 and every command. Result: 12 groups, all pass at `-O0` and `-O2`. No findings against `cm_refs`.

Groups (exit code 11–22 names the failing one):

- 11 `refmap_new`, misses on an empty map, basic `refmap_add` / `refmap_lookup`, empty URL vs empty title, independent `RefMap` instances, ephemeral input bases, and `RefHit` clone ownership (moving/destructuring returned `url` and `title` leaves stored entries intact).
- 12 label normalisation: ASCII case-insensitivity, full Unicode case folding (`ẞ`/`ß`/`SS`, `Straße`, Greek `ΑΓΩ` and `Σ`/`σ`/`ς`, `ﬁ`/`ﬃ` ligatures, `İ`, Kelvin `K`), trimming and collapsing runs of space/tab/LF/CR/CRLF, non-collapsing `U+00A0` NBSP per CommonMark 0.31.2, and raw string matching without inline backslash/emphasis stripping (`foo\!` vs `foo!`).
- 13 first-definition-wins precedence (including when the first definition has an empty title and a duplicate supplies one), rejection of empty and whitespace-only labels, and the contract's 1,000-byte label limit across `refmap_add`, `refmap_lookup` and `parse_ref_definition` (999 and 1,000 bytes accepted; 1,001 ASCII bytes, 1,003 whitespace-padded bytes over an existing key, and 501 two-byte UTF-8 characters = 1,002 bytes rejected).
- 14 store-time `clean_url` and `clean_title` via `refmap_add`: URL trim before entity and backslash unescaping (entity-decoded edge spaces preserved), `&#0;`/`&#x0;` to `U+FFFD`, title no-trim rule, stripping a single matching outer delimiter pair (`"..."`, `'...'`, `(...)`) while keeping mismatched or 1-byte delimiters, and raw `0xFF` and interior `0x00` bytes built with `buffer_putc`.
- 15 `Chunk` offset/length bounds in `refmap_add` and `refmap_lookup`: three separate bases with surrounding noise, three slices into one shared base, interior lookup chunks, and zero-length chunks at non-zero offsets.
- 16 `parse_ref_definition` basics: 0–3 leading spaces accepted, 4 spaces and leading tab rejected, newline/whitespace before destination and title, missing destination and blank line after `:`, EOF without newline, and LF / CRLF / lone CR line endings.
- 17 `parse_ref_definition` destinations: `<...>` (empty `<>`, spaces, parens, escaped `\<`/`\>`; rejecting escaped closing `\>`, unescaped `<`, and line breaks) and bare destinations (5-level balanced parens, escaped unbalanced parens, `"title"` as bare destination, `U+00A0` non-separator, entities/backslashes/UTF-8; rejecting unbalanced parens, spaces, and ASCII control bytes `0x01`/`0x7F`).
- 18 `parse_ref_definition` titles and backtracking: `"..."`, `'...'`, `(...)`, empty titles, preserved interior whitespace, escaped delimiters and entities, multi-line titles without blank lines, rejection of same-line invalid/trailing-text or blank-line titles, and backtracking to a valid title-less definition when a next-line candidate title fails or has trailing text (spec example 209).
- 19 `parse_ref_definition` labels: escaped `\[`, `\]` and `\\` inside labels, rejection of unescaped `[`/`]`, escaped opening `\[`, space before `:`, empty/blank labels, and multi-line labels with trailing paragraph lines left unconsumed.
- 20 `parse_ref_definition` consecutive definitions: consuming multiple back-to-back definitions and stopping at trailing paragraph text, duplicate definitions within one parse (all consumed, first wins), and a valid definition followed by an invalid same-line definition.
- 21 `parse_ref_definition` strict sub-chunk isolation: non-zero `c.off` reporting chunk-relative `consumed`, truncated `c.len` hiding trailing characters or cutting off destinations/delimiters/next-line titles, and empty sub-chunks.
- 22 growth and scale: 200 definitions via `refmap_add` plus 200 consecutive definitions parsed from one strict sub-chunk, duplicate-overwrite resistance on early entries, lookup of all 400 keys under varied casing/whitespace, and 50 absent-key checks.

Checked that the suite can fail: a mutant expecting trimmed title whitespace on `"  keep spaces  "` in group 18 exits 18.

## Contract readings noted

- **Label limit (1,000 bytes).** Group 13 tests Part 6's stated 1,000-byte raw-label bound (`QUEUE.md` notes the manager's pending decision on 1,000 bytes vs the spec's 999 characters; if the contract changes to 999 characters, the 1,000-byte ASCII and 501-character UTF-8 cases in group 13 are the ones to update).
- **Label chunks vs definition chunks.** `refmap_add` and `refmap_lookup` take the label text inside `[...]` without outer brackets, while `parse_ref_definition` parses one or more consecutive `[label]: ...` definitions from the start of `c` and returns total bytes consumed relative to `c.off`.
- **Label whitespace set.** Following CommonMark 0.31.2, only ASCII space, tab, LF and CR are stripped/collapsed in labels (`U+00A0` NBSP is preserved); `cm_refs` matches this.

## Compiler notes

No possible compiler faults observed; `-O0` and `-O2` agree on every group. One normal language rule encountered while writing: moving a single field out of `RefHit` invalidates the whole binding under D-065 (`NITPICK-MOVE-001`), so group 11 consumes `RefHit` via `pick (move(...))` destructuring.

Queue: next unblocked line for Carbon is `3. ready — **part review: scan**`; not started (one line at a time).
