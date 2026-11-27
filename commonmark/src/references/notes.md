# Notes — Part 6: `references` (module `cm_refs`)

Writer: Neon (Google)
Compiler pin: `3a45b7c4` (`pin/npkc` sha256 `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`, `pin/npkrt.o` sha256 `c8e5033ad17c70f838d567157738a6cc046af0ca3140ad92259fa71f0e747b4e`)

## Design and contract fidelity

- **Imports (`INTERFACES.md` import graph):** `cm_refs` imports only `cm_buffer`, `cm_utf8`, `cm_scan`, and `cm_escape`. No `main`, no `failsafe`, no error constants; all fallible calls are relayed unchanged.
- **Public surface (`INTERFACES.md` Part 6):**
  - `RefMap` — owning, move-only struct with hidden managed `List<RefEntry>` and `List<int64>` bucket index (no `wild` pointers; Nitpick's generated drop frees every entry's strings and both lists automatically on scope exit, and `move(m)` transfers ownership cleanly for `doc_set_refs`).
  - `RefHit = { bool:found; string:url; string:title; }` — owning, move-only lookup result; `url` and `title` are independent owned clones via `.clone()` when `found` is `true`, and `""` when `false`.
  - `RefParse = { int64:consumed; }` — plain result of `parse_ref_definition`.
  - `refmap_new`, `refmap_add`, `refmap_lookup`, `parse_ref_definition` with exact contract signatures.
- **Indexing:** Open-addressed linear-probing hash table using overflow-free 32-bit FNV-1a computed in `uint64` (truncated via `=>! uint32`), growing by powers of two from 16 whenever `(entries.count + 1) * 2 > buckets.count`. Keeping the index maintained on insert avoids mutating the lent `RefMap` parameter during `refmap_lookup`.

## Behavioural notes (cmark 0.31.2 / CommonMark 0.31.2 fidelity)

- **Label normalisation (`normalize_label`, matching cmark `references.c`):**
  - Rejects empty labels and labels longer than `1000` bytes (`MAX_LINK_LABEL_LENGTH = 1000`) in `refmap_add`, `refmap_lookup`, and `parse_ref_definition`.
  - Applies full Unicode case folding via `cm_utf8.utf8_case_fold` (handling multi-codepoint folds such as `ẞ` ↔ `SS`, `ﬁ` ↔ `FI`, and Greek `ΑΓΩ` ↔ `αγω`).
  - Strips leading/trailing ASCII whitespace (`' '`, `'\t'`, `'\n'`, `'\v'`, `'\f'`, `'\r'`, matching `cmark_isspace`) and collapses internal runs of ASCII whitespace to a single `' '` (`0x20`); non-ASCII whitespace such as U+00A0 (NBSP) is preserved unchanged, and backslashes in labels are not unescaped.
  - Whitespace-only labels normalise to empty and are neither stored nor matched.
- **Cleaning and precedence (`refmap_add`, matching cmark `cmark_reference_create`):**
  - Cleans `url` through `cm_escape.clean_url` and `title` through `cm_escape.clean_title` at store time.
  - The first definition of a normalised label wins; a later duplicate is still cleaned (so errors relay identically) and dropped.
- **Definition parsing (`parse_ref_definition`, matching cmark `cmark_parse_reference_inline` + multi-definition loop):**
  - Consumes **one or more** consecutive link reference definitions starting at `c.off` within `[c.off, c.off + c.len)`, adding each to `m` and returning total bytes consumed (`0` if none).
  - Accepts `0..3` leading ASCII spaces before `[` (rejecting 4+ spaces and leading tabs), handles backslash-escaped ASCII punctuation inside labels (`\]`, `\[`, `\\`), rejects unescaped `[` and embedded NUL and blank lines in labels, and requires at least one non-whitespace byte in the label.
  - Supports both angle-bracketed (`<...>`, including empty `<>`, escaped punctuation, rejecting `<`, line endings, NUL) and bare link destinations (nonempty, rejecting ASCII controls/spaces, allowing balanced unescaped parentheses up to 32 levels deep matching cmark).
  - Delegates link title scanning to `cm_scan.scan_link_title`, requiring whitespace (`spnl`) between destination and title. When `c` is a strict sub-chunk (`c.off + c.len < base.len`), slices the remaining sub-chunk via `cm_buffer.chunk_to_string` before invoking `scan_link_title` so scanning never reads past `c`'s end.
  - Rejects titles containing a blank line, and implements cmark's rewind-before-title rule (spec §4.7): if non-space characters follow a parsed title on its closing line, rewinds to the end of the destination and succeeds without a title if a line ending (or end of chunk) follows the destination.
  - Supports `\n`, `\r\n`, and lone `\r` line endings.

## Extra verification performed (outside `check.log`)

- **Error-relay seam & `move(RefMap)` verification (`-O0` and `-O2`):** compiled `cm_refs.npk` against controllable failing stubs for `cm_buffer` (`EFakeBuf`, `EFakeSlice`), `cm_utf8` (`EFakeUtf8`), and `cm_escape` (`EFakeUrl`, `EFakeTitle`) in a scratch harness (12 cases covering `refmap_add` including duplicate-label cleaning, `refmap_lookup`, `parse_ref_definition` including strict sub-chunk title slicing, and `move(m)` ownership transfer); all 12 cases passed identically at both `-O0` and `-O2`.

## Compiler notes

None. No compiler crashes, `-O0`/`-O2` divergences, or run-to-run differences were observed on compiler commit `3a45b7c4`.
