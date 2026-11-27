# Notes — Part 2: `utf8` (module `cm_utf8`)

Writer: Neon (Google)
Compiler pin: `3a45b7c4` (`pin/npkc` sha256 `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`)

## Contract note for management (Part 1 `cm_buffer`, NOT Part 2 `cm_utf8`)

`commonmark/INTERFACES.md` Part 1 specifies `buffer_new() -> Result<Buffer>` in `cm_buffer`.
Under Nitpick D-294 (`BUILTIN_REFERENCE.md` §2b), `buffer_new` is a reserved bare-name builtin (`int64 -> buffer`), so declaring `pub func:buffer_new = Buffer()` in `cm_buffer.npk` is refused by `npkc`:

```
NITPICK-RESOLVE-001 ../../buffer/cm_buffer.npk:14:1: `buffer_new` is a builtin (BUILTIN_REFERENCE), so a program cannot declare it as a function: the declaration would silently take the name over wherever this module's scope reaches, and one call would mean two things (D-294) -- rename it
```

- **`cm_utf8.npk` itself is unaffected**: it only imports `{Buffer, Chunk, buffer_put, buffer_putc}` from `../buffer/cm_buffer.npk` and implements every Part 2 type and signature in `INTERFACES.md` verbatim.
- **`src/utf8/checks/check_utf8.npk`** calls `buffer_new()` per the current frozen contract. Once management issues the contract-fix PR renaming `buffer_new` in Part 1, `check_utf8.npk` will need that one-identifier update. During Milestone 2 parallel testing in `/tmp/cm_utf8_test/`, `buffer_new` was temporarily substituted with `cm_buf_new` in the `/tmp` test copy only.

## Table generation provenance (`cm_utf8_tables.npk`)

- `commonmark/src/utf8/gen_tables.py` generates `commonmark/src/utf8/cm_utf8_tables.npk` (never hand-edited).
- It supports direct parsing of cmark 0.31.2's `src/case_fold.inc` / `src/case_fold_switch.inc` via `--case-fold-inc <path>`.
- Because this workspace has no network access or local cmark checkout, `cm_utf8_tables.npk` was generated offline from the system's `libutf8proc` (Unicode 15.1.0), which matches cmark 0.31.2's Unicode 15.1.0 full case-folding (C + F: 1,504 non-ASCII entries, 1,530 total with ASCII `A–Z`) and P/S general-category ranges (335 non-ASCII ranges, 8,617 P/S code points total including ASCII).
- ASCII fast paths (`A–Z` for case folding; `0x21..0x2F`, `0x3A..0x40`, `0x5B..0x60`, `0x7B..0x7E` for `utf8_is_punct`) are inlined in `cm_utf8.npk`.

## Behavioural notes (cmark 0.31.2 fidelity)

- `utf8_iterate`: decodes valid RFC 3629 sequences (1–4 bytes, rejecting overlong encodings, UTF-16 surrogates `U+D800..U+DFFF`, and values `> U+10FFFF`; accepting `U+FFFE` and `U+FFFF` per cmark #548). Returns `{ 0xFFFD, 1 }` on any invalid/truncated byte sequence and `{ 0, 0 }` when `pos < 0` or `pos >= c.len`.
- `utf8_encode`: encodes valid scalars (including `U+0000`, `U+FFFE`, `U+FFFF`) as 1–4 UTF-8 bytes; invalid scalars (`< 0`, surrogates, `> U+10FFFF`) encode as `U+FFFD`.
- `utf8_check`: follows cmark's `cmark_utf8proc_check` / `valid_utf8`: replaces `U+0000` (NUL, per CommonMark spec §2.3) and each maximal subpart of an ill-formed UTF-8 sequence with one `U+FFFD` (`\xEF\xBF\xBD`), batching valid runs through `buffer_put`.
- `utf8_is_space`: exact 21 code points matching CommonMark / `cmark_utf8proc_is_space` (`Zs` + `0x09`, `0x0A`, `0x0C`, `0x0D`; excluding `0x0B` `\v`, `0x85`, `0x180E`, `0x200B`, `0xFEFF`).
- `utf8_is_punct`: Unicode `P*` and `S*` categories (`cmark_utf8proc_is_punctuation_or_symbol`).
- `utf8_case_fold`: full Unicode case folding (status C + F) with 1-, 2-, and 3-codepoint expansions; invalid UTF-8 bytes become `U+FFFD` and advance by 1 byte, matching `cmark_utf8proc_case_fold`.

## Compiler notes

No compiler crashes, -O0/-O2 divergences, or nondeterminism were observed while building and running `cm_utf8` and its checks at `-O0` and `-O2` on compiler commit `3a45b7c4`.

### Lexer / string-literal `\xNN` note (for awareness across the port)

Not necessarily a defect, but worth noting because `LEXICAL_REFERENCE.md` §6.3 does not state whether `\xNN` (`0x80..0xFF`) in a `string` literal is a raw byte or a Unicode scalar value:

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
