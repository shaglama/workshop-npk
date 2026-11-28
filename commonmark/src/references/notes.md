Queue line done: 2. `next` — **references optimisation** (from Sol's part review, `src/node/references-review/NOTES.md`): strict sub-chunk title scans copy the remaining suffix repeatedly — a strict sub-chunk of n small definitions copies O(n²) bytes. Bound the input once per parse, preserving chunk isolation. Correctness is unaffected; only after the fixes above. (src/references/)

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
  - Delegates link title scanning to `cm_scan.scan_link_title`, requiring whitespace (`spnl`) between destination and title. When `c` is a strict sub-chunk (`c.off + len < base.len`), `parse_ref_definition` bounds the clamped chunk once via `cm_buffer.chunk_to_string` (after rejecting chunks that do not start with `0..3` ASCII spaces + `'['` without allocating) so `scan_link_title` never reads past `c`'s end and never repeats suffix copies across consecutive definitions.
  - Rejects titles containing a blank line, and implements cmark's rewind-before-title rule (spec §4.7): if non-space characters follow a parsed title on its closing line, rewinds to the end of the destination and succeeds without a title if a line ending (or end of chunk) follows the destination.
  - Supports `\n`, `\r\n`, and lone `\r` line endings.

## Optimisation — single-bound strict sub-chunk parsing (2026-11-27)

- **Finding addressed:** Sol's part review (`src/node/references-review/NOTES.md`) noted that `parse_one_ref_def` sliced `base[pos .. stop)` via `chunk_to_string` on every title scan inside a strict sub-chunk (`stop < base.len`), causing `O(n²)` bytes copied for a strict sub-chunk of `n` consecutive definitions.
- **Change in `cm_refs.npk`:**
  - `parse_one_ref_def(m, base, start)` now relies on the module-internal invariant that `base.len` is the active chunk end (`stop = base.len`), calling `scan_link_title(base, pos)` directly with zero copies.
  - `parse_ref_loop(m, src, start)` loops `parse_one_ref_def` over `[start, src.len)`.
  - `parse_ref_definition(m, base, c)` clamps `c` and:
    1. When `stop == base.len` (full-string or trailing-suffix chunk), calls `parse_ref_loop(m, base, c.off)` directly (0 bytes copied).
    2. When `stop < base.len` (strict sub-chunk), first skips up to 3 ASCII spaces at `c.off` and returns `RefParse{ consumed: 0 }` without allocating if the next byte is not `'['`; otherwise copies `Chunk{ off: c.off, len: len }` **once** via `relay chunk_to_string(base, bounded_c)` and runs `parse_ref_loop(m, bounded, 0)`.
  - Strict chunk isolation is preserved across all definitions in the parse, error relay from `chunk_to_string` is unchanged, and strict sub-chunk copying drops from `O(n²)` to at most one `O(len)` copy per `parse_ref_definition` call.
- **Verification (pin `3a45b7c4`, LLVM/LLD `20.1.2`, `-O0` and `-O2`):**
  - Expanded `checks/check_refs.npk` group 6 (`parse_ref_definition edge cases & sub-chunks`) with strict sub-chunk fast-path probes (non-def, 4-space indent, 3-space indent, trailing-suffix chunk), multi-definition strict sub-chunk boundary isolation (3rd definition truncated before its closing `"` outside the chunk), and scale checks (2,500 untitled `[x]: /u\n` definitions and 500 distinct titled definitions inside strict sub-chunks wrapped in outside prefix/suffix bytes).
  - Re-ran `python3 commonmark/src/references/checks/check.py`: exit 0, all 6 groups PASS at `-O0` and `-O2`, refreshed `checks/check.log`.
  - Compiled and ran Carbon's 12-group seam suite (`commonmark/tests/seams/references/references_seam.npk`) in `/tmp` (leaving `tests/seams/references/` untouched): exit 0 at `-O0` and `-O2`.

## Extra verification performed (outside `check.log`)

- **Error-relay seam & `move(RefMap)` verification (`-O0` and `-O2`):** compiled `cm_refs.npk` against controllable failing stubs for `cm_buffer` (`EFakeBuf`, `EFakeSlice`), `cm_utf8` (`EFakeUtf8`), and `cm_escape` (`EFakeUrl`, `EFakeTitle`) in a scratch harness (12 cases covering `refmap_add` including duplicate-label cleaning, `refmap_lookup`, `parse_ref_definition` including strict sub-chunk title slicing, and `move(m)` ownership transfer); all 12 cases passed identically at both `-O0` and `-O2`.

## Compiler notes

None. No compiler crashes, `-O0`/`-O2` divergences, or run-to-run differences were observed on compiler commit `3a45b7c4`.
