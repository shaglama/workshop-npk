# Manager's review: part 4 — `scan` (cm_scan)

**Writer:** Sol (OpenAI). **Manager's review:** Muse Wonder (Meta). **Part review (PLAN):** Carbon (Google) — still to come. **Seam tests (PLAN):** Astra, `tests/seams/scan/` — still to come.
**Verdict: sound.**

## What was checked

- `cm_scan.npk` read against INTERFACES.md Part 4: all 22 scanners present with the contract's signatures, every one `never fails`; no imports, no storage, no `main`/`failsafe`/error constants. The implementation works from the `scanners.re` patterns directly (the sandbox could not fetch `scanners.h` or the generated `scanners.c`; the `.re` file is the source of truth in any case). Boundary handling replaces cmark's sentinel write with a virtual NUL at the string's end — the right adaptation for a lent base that must not be modified.
- Detail reads spot-checked against the patterns: the block-tag list is cmark 0.31.2's exact alternation (including `search`); `scan_dangerous_url` keeps the data-image prefix whitelist exactly as loose as cmark's pattern (a `data:image/png-extra` prefix passes, as in cmark — recorded in Sol's notes rather than silently tightened); `scan_link_title` models the patterns' ambiguity (an escaped closing delimiter can still close a shorter match); the five block-end scanners use the greedy-prefix semantics of `[^\n\x00]*` plus terminator.
- **Re-ran the writer checks on cloud3** (LLVM 20.1.8, the pin's toolchain; pin hash-verified, npkc `23022ef1…`, npkrt.o `c8e5033a…`): `check.py` exit 0, **199,271 cases PASS at -O0 and again at -O2** — the same case count as Sol's log (which used LLVM 20.1.2). The expectations are independent of the port: 218 hand-computed vectors (each also at a nonzero offset), a separate Python regex transcription of the tagged patterns with explicit maximal-munch modelling, an 8,576-string cross-scan corpus (all byte values, truncations, case variants, NUL suffixes, spec lines, seeded random and mutated inputs), and exhaustive small-alphabet checks for the title/comment/PI/CDATA boundaries.

## Notes

1. **The return convention is the seam to watch.** Per the contract, every scanner returns a byte match length — including `scan_setext_heading_line`, `scan_html_block_start` and `scan_html_block_start_7`, where cmark returns a classification code instead. Sol followed the contract and flagged the consequence plainly: callers (`blocks`, `inlines`) must derive the heading level / block type from the matched text. The manager will carry this line into the `blocks` and `inlines` briefs, and Astra's seam tests should pin it down.
2. Sol also applied the wording fix from the manager's `buffer` review (the blocker log and negative reproduction "remain in `checks/`" — verified on the branch). That item is closed.
3. The check runner reads `commonmark/spec/spec.txt` as corpus input — one more reason the spec file belongs in the repo (it is, since the step-2 setup commit).

## Compiler notes

None. No possible compiler fault observed by the writer or on the re-run; -O0 and -O2 agree on all 199,271 cases.
