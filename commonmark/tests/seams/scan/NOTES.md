Queue line done: 1. `next` — **seam tests: scan** (tests/seams/scan/), from INTERFACES.md Part 4 alone.

Written by Sonnet (Claude Sonnet 5.5, Anthropic) from INTERFACES.md Part 4, the scanners.re patterns the contract points to, and the CommonMark 0.31.2 spec (its tag list, `spec/spec.txt`). The part's source was not read before the tests were written (afterwards I read `src/scan/notes.md` once, only to understand the failure below).

Run from anywhere: `python3 commonmark/tests/seams/scan/check.py`. It builds and runs `scan_seam.npk` at `-O0` and `-O2` with `pin/npkc` (3a45b7c4), `pin/npkrt.o` and `pin/lib`; [check.log](check.log) has every command and the compiler sha256. Groups run four to a program, each exiting with a bitmask, so one failing group never hides the others. `scan_seam.npk` is generated from the case tables in `gen.py` (908 cases, each run at offset 0 and again at offset 3 behind a `xyz` prefix to catch look-behind); `probe.py <scanner> <text> [at]` prints one scanner's result.

## Result

**15 of 16 groups pass at both levels; group 23 fails identically at `-O0` and `-O2`** (a finding about the contract, not a compiler fault).

| Group | Covers | Result |
|---|---|---|
| 11 | atx start | pass |
| 12 | setext line (length includes the line end) | pass |
| 13–14 | open/close fence (trailing-context: fence length only) | pass |
| 15 | html block start 1–6, every spec tag name, case, `/>`, no-match prefixes — lengths, not type codes | pass |
| 16 | html block start 7 | pass |
| 17 | html block end 1–5 (greedy to the last terminator, never across `\n`) | pass |
| 18 | spacechars | pass |
| 19 | scheme (2–32 chars, colon included) | pass |
| 20 | autolink uri | pass |
| 21 | autolink email (label limit 63) | pass |
| 22 | html tag: open and close tags | pass |
| **23** | **html comment, PI, declaration, CDATA** | **FAIL** |
| 24 | link title (escapes, ambiguous closers) | pass |
| 25 | dangerous url (data:image whitelist) | pass |
| 26 | every scanner on an empty base and at the end of a base | pass |

## Finding: comment / PI / declaration / CDATA scanners (group 23)

INTERFACES.md says every scanner "returns the length matched, or 0 for no match", with offsets as in cmark (the inline scanners are called just after the `<`). Read that way, `scan_html_comment("!-- a -->")` is 9 and `scan_html_pi("?x")` is 0. The port instead returns a **prefix of the body** and does not require the terminator: `scan_html_pi("?php?>", 0)` = 4, `scan_html_pi("?x", 0)` = 2 (an unterminated PI "matches"), while `scan_html_comment` returns 0 on `"!---->"`, `"<!---->"` and `"!-- a -->"` alike, and `scan_html_cdata` / `scan_html_declaration` return 0 on `"![CDATA[x]]>"` and `"!DOCTYPE html>"` (and on the same with a leading `<`). The writer's notes (src/scan/notes.md) say this is deliberate (comment starts at `--`, PI scans its body without `<?`/`?>`, declaration starts at its letter, CDATA at `CDATA[`, terminators neither required nor included), so the callers must find the terminator themselves.

That is a contract gap rather than a plain bug: nothing in INTERFACES.md says it, and the tests cannot be written from it. The consequence to settle before the inlines part is written: either INTERFACES.md Part 4 states these four scanners' real input offset and result (body prefix, terminator checked by the caller), or the scanners return complete matches like the other eighteen. Until then group 23 is kept as the contract's plain reading, so it fails. If the manager picks the body-prefix reading, group 23 needs rewriting to it; every other group is unaffected.

Smaller points where I made a call (all pass):

- Scanners return 0 for a missing line end where the pattern needs one (`scan_open_code_fence("```")` is 0, a lone `#` is not an ATX start, `scan_setext_heading_line("==")` is 0), matching the virtual-NUL adaptation.
- `scan_html_block_start("<!a")` — I dropped this case: cmark's `[<][!][A-Z]` says no, the spec says an ASCII letter; the port follows the spec (returns 3). Worth knowing; not asserted.
- Not asserted because the contract does not decide them: `data:image/pngx` (cmark's pattern is loose; the manager's review already notes it), declarations without whitespace (`<!DOCTYPE>`) or in lower case (cmark's `[A-Z]+ spacechar+` vs the spec's "ASCII letter"), `scan_html_block_start_7` over `\n\n` runs, negative or past-the-end offsets (the port returns 0).

## Compiler notes

No possible compiler faults observed: all 908 cases give the same results at `-O0` and `-O2`. Language points hit: narrowing is `=>!`, not `as`; `failsafe` must name every reachable error in its `pick`.

Queue: next line is 2, **extend utf8 seam tests**; not started (one line at a time).
