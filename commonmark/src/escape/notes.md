Queue line done: 1. `next` — **escape apostrophe fix** per `reviews/escape.md` addendum (Astra's part review, manager-verified): in secure mode `'` escapes to `&#39;`; correct writer checks 13, 15, 17 and add the regression case. (src/escape/)

# Notes — Part 3: `escape` (module `cm_escape`)

Writer: Neon (Google)
Compiler pin: `3a45b7c4` (`pin/npkc` sha256 `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`, `pin/npkrt.o` sha256 `c8e5033ad17c70f838d567157738a6cc046af0ca3140ad92259fa71f0e747b4e`)

## Fixes applied per `reviews/escape.md` addendum (Astra's part review)

1. **`cm_escape.npk` (`escape_html_into`)**: in secure mode (`secure == true`), ASCII apostrophe `'` (`0x27`, byte `39`) now escapes to `&#39;`, matching cmark 0.31.2's `houdini_html_e.c` (`HTML_ESCAPE_TABLE[0x27] == 3`, `HTML_ESCAPES[3] == "&#39;"`, skipped only when `!secure`). Non-secure mode keeps `'` literal.
2. **`checks/check_escape.npk` & `checks/check.log`**:
   - Corrected the `secure = true` expectations in writer checks 13 (`'single'` → `&#39;single&#39;`), 15 (`a/b'c` → `a&#47;b&#39;c`), and 17 (`"&/<>'` → `&quot;&amp;&#47;&lt;&gt;&#39;`).
   - Added Astra's regression case `expect_html("'", raw chunk_all("'"), true, "&#39;")` (and paired non-secure check `expect_html("'", raw chunk_all("'"), false, "'")`).
   - Re-ran `commonmark/src/escape/checks/check.py` at `-O0` and `-O2` and verified an all-256-bytes sweep (`0x00..0xFF`) for `escape_html_into` in both `secure = false` and `secure = true` modes against cmark 0.31.2's `houdini_escape_html0` at `-O0` and `-O2`.

## Table generation provenance (`cm_escape_entities.npk`)

- `commonmark/src/escape/gen_entities.py` generates `commonmark/src/escape/cm_escape_entities.npk` (never hand-edited).
- Target reference: cmark `0.31.2` (commit `eec0eeba6d31189fd828314576494566d539b1e3`), `src/entities.inc`, which cmark's `tools/make_entities_inc.py` generates from the WHATWG HTML5 `entities.json` table (all 2,125 semicolon-terminated named character references, name lengths `2..31`, 1 or 2 Unicode scalar values each).
- Because this workspace has no network access or local cmark checkout, `cm_escape_entities.npk` was generated offline from Python 3.12.3 stdlib `html.entities.html5` (filtering to semicolon-terminated keys: 2,125 entries, 14,004 packed ASCII name bytes, 93 two-codepoint entries).
- `gen_entities.py --entities-json <path>` also regenerates the table directly from a WHATWG `entities.json` file; verified to produce byte-identical data arrays.

## Behavioural notes (cmark 0.31.2 fidelity)

- **`escape_html_into`** (`src/houdini_html_e.c`, `houdini_escape_html0`): escapes `"` (`&quot;`), `&` (`&amp;`), `<` (`&lt;`), `>` (`&gt;`). When `secure` is `true`, also escapes `'` (`&#39;`) and `/` (`&#47;`); when `secure` is `false`, `'` and `/` pass through unchanged, matching cmark 0.31.2's `HTML_ESCAPE_TABLE` and `!secure` check.
- **`escape_href_into`** (`src/houdini_href_e.c`, `houdini_escape_href`): copies the 81 bytes marked `1` in cmark's `HREF_SAFE` table (`!#$%()*+,-./0-9:;=?@A-Z_a-z~`) verbatim, escapes `&` as `&amp;` and `'` as `&#x27;`, and percent-encodes every other byte (`0x00..0x20`, `"`, `<`, `>`, `[`, `\`, `]`, `^`, `` ` ``, `{`, `|`, `}`, `0x7F..0xFF`) as uppercase `%XX`. Existing `%` sequences are preserved without double-escaping, matching cmark 0.31.2.
- **`unescape_entities_into`** (`src/houdini_html_u.c`, `houdini_unescape_html_f` / `houdini_unescape_ent`):
  - Named entities: binary search over the 2,125 sorted HTML5 names (`2..31` ASCII alphanumeric chars followed by `;`), case-sensitive, encoded via `cm_utf8.utf8_encode`.
  - Decimal numeric references: `&#` + `1..7` ASCII digits + `;`.
  - Hexadecimal numeric references: `&#x` or `&#X` + `1..6` ASCII hex digits + `;`.
  - For numeric references, `0`, UTF-16 surrogates (`0xD800..0xDFFF`), and values `> 0x10FFFF` are replaced with `U+FFFD` (`0xFFFD`), per CommonMark 0.31.2 §2.5 / cmark; valid noncharacters such as `U+FFFE` and `U+FFFF` are preserved.
  - Unrecognised or unterminated `&...` sequences are left intact.
- **`unescape_backslashes_into`** (`cmark_strbuf_unescape`): drops `\` immediately preceding any of the 32 ASCII punctuation characters (`0x21..0x2F`, `0x3A..0x40`, `0x5B..0x60`, `0x7B..0x7E`) inside the chunk; keeps `\` before all other bytes and at the chunk end.
- **Note on `clean_url` and `clean_title` wording in `INTERFACES.md` / `briefs/escape.md`**:
  - `INTERFACES.md` summarises `clean_url` as `cmark_clean_url: entity-unescape, backslash-unescape, trim — in cmark's order` and `clean_title` as `cmark_clean_title: the same cleaning, for titles`, and `briefs/escape.md` paraphrases this as "entity-unescape, then backslash-unescape, then trim".
  - In cmark 0.31.2 (`src/inlines.c`), `cmark_clean_url` actually **trims first** (`cmark_chunk_trim`, ASCII whitespace `' '`, `'\t'`, `'\n'`, `'\v'`, `'\f'`, `'\r'`), then calls `houdini_unescape_html_f` (entity-unescape), then `cmark_strbuf_unescape` (backslash-unescape) — so entity-decoded spaces such as `&#32;` in `<&#32;foo&#32;>` are preserved.
  - Likewise, cmark 0.31.2's `cmark_clean_title` does **not** trim whitespace (CommonMark spec Example 193 requires preserving leading/trailing newlines/spaces inside a quoted title), and instead strips matching outer delimiters (`"..."`, `'...'`, or `(...)` when `len >= 2`), then entity-unescapes, then backslash-unescapes.
  - `cm_escape.npk` follows cmark 0.31.2's exact `cmark_clean_url` and `cmark_clean_title` behaviour (as required by CommonMark spec examples and cmark's `cmark_reference_create` / `inlines.c` callers), flagged here for manager/reviewer/seam-test awareness.

## Extra verification performed (outside `check.log`)

- **Exhaustive sweep (`-O0` and `-O2`)**: verified all 2,125 HTML5 named entities concatenated (`6,216` UTF-8 output bytes, FNV-1a 64-bit `1441682606462249284`) and all 256 byte values `0x00..0xFF` across `escape_html_into(false)`, `escape_html_into(true)`, `escape_href_into`, and `unescape_backslashes_into` (`\` + every byte `0..255`) against independent Python oracles; both `-O0` and `-O2` matched bit-for-bit.
- **Error-relay seam check (`-O0` and `-O2`)**: compiled against a failing `cm_buffer` stub returning `EFakeBuf`; all 6 functions (`escape_html_into`, `escape_href_into`, `unescape_entities_into`, `unescape_backslashes_into`, `clean_url`, `clean_title`) relayed `cm_buffer.EFakeBuf` unchanged at both `-O0` and `-O2`.

## Compiler notes

None. No compiler crashes, `-O0`/`-O2` divergences, or run-to-run differences were observed on compiler commit `3a45b7c4`.
