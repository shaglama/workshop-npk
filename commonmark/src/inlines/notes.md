Queue line done: 2. `next` — **part review: scan**.

Queue line blocked: 1. `blocked: brief` — **inlines part** (src/inlines/). Brief: `briefs/inlines.md` (manager to post).

# Part 4 (`scan` / `cm_scan`) review — Carbon (Google), 2026-11-27

These review notes live in Carbon's assigned `src/inlines/` handback folder while `src/inlines/` awaits `briefs/inlines.md`.

**Verdict: passes review (no changes requested for `src/scan/`).**

`cm_scan.npk` satisfies `INTERFACES.md` Part 4 and matches `cmark` 0.31.2's `src/scanners.re` patterns across all 22 public scanners:

- **Contract & module discipline.** Module `cm_scan` has zero imports (matching the acyclic import graph), owns no state, stores no borrowed views, defines no `main`, `failsafe`, or error constants, and exports the exact 22 functions in `INTERFACES.md` Part 4 with signature `int64(string:base, int64:at) never fails`.
- **Bounds, sentinel & termination safety.** Out-of-range offsets (`at < 0` or `at >= base.len`, including `INT64_MIN` and `INT64_MAX`) return `0` without overflow or out-of-bounds indexing. `byte_at` supplies a virtual NUL at `base.len` instead of mutating the lent `base`, while embedded `0x00` bytes act as pattern terminators just as in `cmark`'s sentinel buffer. Every `while` loop carries a non-negative, strictly decreasing `decreases` measure (`word.len - i` or `base.len - i`), including multi-byte advances in `scan_html_comment`, `scan_html_pi`, `scan_html_cdata`, and attribute-whitespace rewinds in `scan_html_tag`.
- **Pattern fidelity & linear worst-case runtime.**
  - `scan_atx_heading_start`, `scan_setext_heading_line`, `scan_open_code_fence`, and `scan_close_code_fence` implement `scanners.re`'s whitespace/EOL rules (`[\r\n]` consumes a single CR on CRLF; fence scanners validate trailing line context while returning only the fence-run length `>= 3`).
  - `scan_html_block_start` checks all 62 CommonMark 0.31.2 condition-6 block tag names case-insensitively (including `search`), case-insensitive condition-1 raw tags (`script`, `pre`, `textarea`, `style`), case-sensitive `<![CDATA[`, `<!--`, `<?`, and `<!` + ASCII letter. `scan_html_block_start_7` delegates to `scan_html_tag` after `<` and handles `[\t\n\f ]*[\r\n]` LF backtracking in one pass.
  - `scan_html_block_end_1` .. `scan_html_block_end_5` match the longest `[^\n\x00]*` prefix through the last terminator before `\n` or `\x00`.
  - `scan_spacechars`, `scan_scheme`, `scan_autolink_uri`, `scan_autolink_email`, and `scan_html_tag` match their `scanners.re` character classes, length caps (2–32 scheme bytes; 1–63 domain-label bytes with alphanumeric endpoints), and quote/attribute rules in `O(n)` time.
  - `scan_link_title` models `scanners.re`'s `(escaped_char | [^"\x00])*` / `[^'\x00]*` / `[^()\x00]*` maximal-munch ambiguity in a single linear pass by bookmarking candidate closing delimiters when preceded by `\`.
  - `scan_dangerous_url` implements `cmark`'s case-insensitive prefix whitelist (`data:image/(png|gif|jpeg|webp)` -> `0`) ahead of `javascript:` (`11`), `vbscript:` (`9`), `file:` (`5`), and `data:` (`5`).

## Integration seams & `scanners.re` notes for callers (`blocks`, `inlines`, `references`, `html`)

None of the items below are defects in `cm_scan`; they are exact consequences of Part 4 and `cmark` 0.31.2's `src/scanners.re` that callers and seam tests should account for:

1. **Match lengths vs `cmark` classification codes (`blocks`, `tests/seams/scan/`).** Per Part 4, `scan_setext_heading_line`, `scan_html_block_start`, and `scan_html_block_start_7` return matched byte counts rather than `cmark`'s level (`1`/`2`) or HTML block type (`1`–`7`). `cm_blocks` must derive setext level from `base[at]` (`'='` vs `'-'`) and HTML block type `1`–`6` from the matched prefix, and must run `scan_html_block_start` before `scan_html_block_start_7` (note also that `scanners.re`'s `opentag` in condition 7 does not exclude `pre`/`script`/`style`/`textarea`, so self-closing `<script/>\n` misses condition 1 and matches `scan_html_block_start_7` with length `10`, as in `cmark`).
2. **No slice-stop parameter (`references`, `blocks`, `inlines`).** Every scanner reads `base` from `at` up to `base.len` (or embedded NUL). Callers holding a strict sub-chunk (`off + len < base.len`) must bound the slice before calling scanners whose match could cross `off + len` (as `cm_refs` does for `scan_link_title`).
3. **Inline raw HTML entry offsets, body-only returns, and short comments (`inlines`).**
   - `scan_autolink_uri`, `scan_autolink_email`, and `scan_html_tag` start at `at + 1` (after `<`) and include closing `>`.
   - `scan_html_comment` starts at `at + 2` (at `--` after `<!`), includes closing `-->`, and implements `scanners.re`'s `--(?:[^\x00-]|-[^\x00-]|--[^\x00>])*-->`. Because re2c maximal-munch would otherwise swallow `<!--> foo -->` (`--> foo -->` returns `11`) and `<!---> foo -->` (`---> foo -->` returns `12`) while `-->`, `--->`, `----->`, and `--a--->` return `0`, `cm_inlines` must handle CommonMark 0.31.2's `<!-->` / `<!--->` cases and linear-time comment closing rules in the inline parser (as `cmark` 0.31.2's `inlines.c` does).
   - `scan_html_pi` (after `<?`), `scan_html_declaration` (after `<!`), and `scan_html_cdata` (at `CDATA[` after `<![`) return **body prefix lengths** without requiring or consuming `?>`, `>`, or `]]>` (and `scanners.re`'s `html_pi` / `html_cdata` patterns consume past the closing delimiter on `??>` -> `3` and `CDATA[]]]>` -> `10`). `cm_inlines` must verify the closing delimiter at `pos + n` and use the scanned span to avoid quadratic re-scanning on unclosed sequences.
4. **Tagged `scanners.re` vs spec prose details.** `scan_autolink_uri` follows `scanners.re`'s `[^\x00-\x20<>]*>` and accepts `0x7F` (`DEL`), whereas CommonMark 0.31.2 §6.5 excludes all ASCII control characters (`0x00–0x1F` and `0x7F`); `scan_html_tag` uses `spacechar` (`[ \t\v\f\r\n]`) for internal tag whitespace. Both match `cmark` 0.31.2.
5. **Minor writer-harness note (non-blocking).** `checks/patterns.py` lists `title` twice in its `BLOCK` regex alternation (mirroring `scanners.re`); regex set membership is unaffected and `cm_scan.npk`'s `block_tag` checks each of the 62 tags once.

## Verification

Compiler pin `3a45b7c4`, Ubuntu LLVM / LLD `20.1.2`:

- `pin/npkc` SHA-256: `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`
- `pin/npkrt.o` SHA-256: `c8e5033ad17c70f838d567157738a6cc046af0ca3140ad92259fa71f0e747b4e`

1. **Writer check suite (`commonmark/src/scan/checks/scan_check.npk`).** Re-generated `cases.bin` from `checks/check.py` (`199,271` cases across `8,576` corpus strings, SHA-256 `ac5c5dedf67a4d315a56ebe42a49d3455dc39c42563199a49dac9d1228185b93`, matching `checks/scan.log`) and built/ran in `/tmp` without touching `src/scan/`:
   - `pin/npkc commonmark/src/scan/checks/scan_check.npk -o scan.O{0,2}.ll`
   - `opt-20 -O{0,2} -S scan.O{0,2}.ll -o scan.O{0,2}.opt.ll`
   - `llc-20 -O{0,2} -filetype=obj -relocation-model=static scan.O{0,2}.opt.ll -o scan.O{0,2}.o`
   - `ld.lld-20 -static -o scan.O{0,2} scan.O{0,2}.o pin/npkrt.o`
   - `-O0`: exit `0`, empty stderr, stdout `scan writer checks: PASS; cases=199271`
   - `-O2`: exit `0`, empty stderr, stdout `scan writer checks: PASS; cases=199271`

2. **Independent reviewer probe (`scan_review_probe.npk`, built and run in `/tmp` at `-O0` and `-O2` with the same `npkc` / `opt-20` / `llc-20` / `ld.lld-20` pipeline).** Verified:
   - Lent `base` non-consumption across all 22 scanners plus extreme `int64` offsets (`INT64_MIN`, `-2`, `-1`, `base.len`, `base.len + 1`, `INT64_MAX`, and `""` at `0`).
   - Raw binary bytes `0x00`, `0x7F`, `0x80`, and `0xFF` constructed via `cm_buffer`'s `buffer_putc` (avoiding string-literal `\xNN` UTF-8 encoding).
   - Seam cases (`scan_setext_heading_line`, `<SeArCh>`, `<script/>` vs `<script/>\n`, `--> foo -->` / `---> foo -->` / `---->` / `----->` / `--a--->`, `scan_html_pi` on `php?>` / `??>` / `???>`, `scan_html_declaration`, `scan_html_cdata` on `CDATA[x]]>` / `CDATA[]]]>`, `scan_html_tag` boolean and `/` attributes, and `scan_link_title` backslash-paren ambiguity).
   - 50,000-byte adversarial unclosed inputs (`"\"..."x` on `scan_link_title`, 10,000-attribute unclosed `<div ...` on `scan_html_tag` and `scan_html_block_start_7`, and `--` repeats without `-->` on `scan_html_comment` and `scan_html_block_end_2`).
   - Both `-O0` and `-O2` exited `0` with empty stderr and identical output (`PASS 1` .. `PASS 4`, `ALL SCAN REVIEW PROBES PASSED`).

*(Note: `tests/seams/scan/` is queued separately under Sonnet in `QUEUE.md` and has not been delivered yet.)*

## Compiler notes

No possible compiler faults observed; `-O0` and `-O2` builds succeeded cleanly and produced identical results across all 199,271 writer cases and all reviewer probes.
