Queue line done: 1. `next` — **utf8 fixes** per `reviews/utf8.md`: harness on the real `cm_buffer` (`buffer_create`) with a refreshed `check.log` from the real tree; regenerate both tables from `spec/case_fold.inc` and cmark's `utf8.c` via the new `--case-fold-inc` mode. (src/utf8/)

# Notes — Part 2: `utf8` (module `cm_utf8`)

Writer: Neon (Google)
Compiler pin: `3a45b7c4` (`pin/npkc` sha256 `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`)

## Fixes applied per `reviews/utf8.md`

1. **`checks/check_utf8.npk` & `checks/check.log`**: updated `buffer_new` → `buffer_create` throughout (import and all call sites; PR #3 landed the contract rename) and added regression checks for the Unicode 16 case-fold entries (`U+1C89`, `U+A7CB`, `U+A7DC`, `U+10D50`) and the 5 Unicode 15.1 P/S boundary code points absent from cmark 0.31.2 (`U+2FFC..U+2FFF`, `U+31EF`, alongside `U+2FFB`). Built and ran directly against the real `commonmark/src/buffer/cm_buffer.npk` at `-O0` and `-O2` (no stub), and refreshed `checks/check.log`.
2. **`gen_tables.py` & `cm_utf8_tables.npk`**:
   - Updated `parse_cmark_case_fold_inc` in `gen_tables.py` to parse cmark 0.31.2's compact `cf_table` + `cf_repl` format directly from `commonmark/spec/case_fold.inc` (via `--case-fold-inc ../../spec/case_fold.inc`, now also the default when `spec/case_fold.inc` is present). Regenerated `cm_utf8_tables.npk` with all **1,559** non-ASCII case-folding entries (104 multi-codepoint; 1,585 total with ASCII `A–Z`), adding the 55 Unicode 16 entries that `libutf8proc` 15.1.0 was missing.
   - Updated punctuation/symbol range generation to match cmark 0.31.2's `src/utf8.c` P/S set (Unicode 15.0.0: **334** non-ASCII ranges, **8,580** non-ASCII code points, **8,612** total with ASCII), removing the 5 Unicode 15.1 additions (`U+2FFC..U+2FFF`, `U+31EF`). Note: `src/utf8.c` is not checked into `commonmark/spec/`; `gen_tables.py` derives the exact Unicode 15.0.0 P/S set (via Python `unicodedata` 15.0.0, cross-checked against `libutf8proc` 15.1.0 minus `{U+2FFC..U+2FFF, U+31EF}` per the manager's entry-by-entry comparison in `reviews/utf8.md`).
3. **Removed stale contract note**: PR #3 resolved the `buffer_new` → `buffer_create` builtin collision in `INTERFACES.md` Part 1; the pre-rename section has been removed.

## Table generation provenance (`cm_utf8_tables.npk`)

- `commonmark/src/utf8/gen_tables.py` generates `commonmark/src/utf8/cm_utf8_tables.npk` (never hand-edited).
- Command used: `python3 commonmark/src/utf8/gen_tables.py --case-fold-inc commonmark/spec/case_fold.inc`.
- Case-folding table: parsed verbatim from `commonmark/spec/case_fold.inc` (cmark 0.31.2, commit `eec0eeba6d31189fd828314576494566d539b1e3`, Unicode 16): 1,559 non-ASCII entries (104 multi-codepoint), 1,585 total with ASCII `A–Z`.
- Punctuation/symbol ranges: cmark 0.31.2 `src/utf8.c` P/S set (Unicode 15.0.0: 334 non-ASCII ranges, 8,580 non-ASCII code points, 8,612 total with ASCII; excludes `U+2FFC..U+2FFF` and `U+31EF`).
- ASCII fast paths (`A–Z` for case folding; `0x21..0x2F`, `0x3A..0x40`, `0x5B..0x60`, `0x7B..0x7E` for `utf8_is_punct`) are inlined in `cm_utf8.npk`.

## Behavioural notes (cmark 0.31.2 fidelity)

- `utf8_iterate`: decodes valid RFC 3629 sequences (1–4 bytes, rejecting overlong encodings, UTF-16 surrogates `U+D800..U+DFFF`, and values `> U+10FFFF`; accepting `U+FFFE` and `U+FFFF` per cmark #548). Returns `{ 0xFFFD, 1 }` on any invalid/truncated byte sequence and `{ 0, 0 }` when `pos < 0` or `pos >= c.len`.
- `utf8_encode`: encodes valid scalars (including `U+0000`, `U+FFFE`, `U+FFFF`) as 1–4 UTF-8 bytes; invalid scalars (`< 0`, surrogates, `> U+10FFFF`) encode as `U+FFFD`.
- `utf8_check`: follows cmark's `cmark_utf8proc_check` / `valid_utf8`: replaces `U+0000` (NUL, per CommonMark spec §2.3) and each maximal subpart of an ill-formed UTF-8 sequence with one `U+FFFD` (`\xEF\xBF\xBD`), batching valid runs through `buffer_put`.
- `utf8_is_space`: exact 21 code points matching CommonMark / `cmark_utf8proc_is_space` (`Zs` + `0x09`, `0x0A`, `0x0C`, `0x0D`; excluding `0x0B` `\v`, `0x85`, `0x180E`, `0x200B`, `0xFEFF`).
- `utf8_is_punct`: Unicode `P*` and `S*` categories matching cmark 0.31.2's `cmark_utf8proc_is_punctuation_or_symbol`.
- `utf8_case_fold`: full Unicode case folding (status C + F) matching cmark 0.31.2's `src/case_fold.inc` with 1-, 2-, and 3-codepoint expansions; invalid UTF-8 bytes become `U+FFFD` and advance by 1 byte, matching `cmark_utf8proc_case_fold`.

## Compiler notes

No compiler crashes, -O0/-O2 divergences, or nondeterminism were observed while building and running `cm_utf8` and its checks at `-O0` and `-O2` on compiler commit `3a45b7c4`.

### Lexer / string-literal `\xNN` note (for awareness across the port)

Recorded in `commonmark/NOTES.md`: `LEXICAL_REFERENCE.md` §6.3 does not state whether `\xNN` (`0x80..0xFF`) in a `string` literal is a raw byte or a Unicode scalar value.

Smallest program (`3a45b7c4`, both `-O0` and `-O2`):
```nitpick
mod:hex_str;
func:main = int32(cstring[]:_~argv) {
    string:s = "\xFF";
    exit (s.len =>! int32);
};
func:failsafe = int32(Error:e) {
    pick (e) {
        (Unreachable, HeapOom, HeapBadRequest, WildLeak, StackExhausted, MachineFault) { exit 90i32; },
        (*) { exit 99i32; }
    }
};
```

- **Observed:** emits `@.str = private unnamed_addr constant [2 x i8] c"\C3\BF"` and exits `2` at both `-O0` and `-O2` (`\xFF` is UTF-8 encoded as `U+00FF`).
- **Impact / workaround:** In `TYPE_REFERENCE.md` §2.2 a `char8` literal `'\xFF'` is one byte, whereas in a `string` literal `"\xFF"` becomes two UTF-8 bytes. Tests that need raw non-UTF-8 byte sequences (e.g. `0x80..0xFF`) construct them with `buffer_putc` rather than `\xNN` string escapes.
