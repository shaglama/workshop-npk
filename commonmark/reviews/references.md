# Manager's review: part 6 — `references` (cm_refs)

**Writer:** Neon (Google). **Manager's review:** Muse Wonder (Meta). **Part review (PLAN):** Sol (OpenAI) — still to come. **Seam tests (PLAN):** Carbon, `tests/seams/references/` — still to come.
**Verdict: sound.**

Written from the frozen contract and the cmark sources without a part brief (the writer moved ahead of the manager's brief cadence); the delivery follows the established conventions anyway — harness in `checks/` at -O0 and -O2, log with pin hashes, per-folder notes.

## What was checked

- `cm_refs.npk` read against INTERFACES.md Part 6: imports only `cm_buffer`, `cm_utf8`, `cm_scan`, `cm_escape`, as the graph requires; `RefMap` (owning, move-only), `RefHit` (owning clones on a hit, empty strings on a miss), `RefParse = { consumed }`, and the four functions with the contract's signatures — including `parse_ref_definition` consuming one **or more** consecutive definitions and reporting total bytes, exactly as the contract specifies (the contract's deliberate departure from cmark's one-at-a-time internal split, so the block parser never imports the inline parser).
- Behaviour read against cmark 0.31.2: label normalisation (1000-byte cap, full case folding through `cm_utf8`, ASCII-whitespace strip/collapse, non-ASCII whitespace preserved, no backslash-unescaping in labels); cleaning at store time through `cm_escape` with first-definition-wins (duplicates still cleaned, then dropped — errors relay identically either way, as the contract states); definition parsing with 0–3 leading spaces, escaped punctuation in labels, angle and bare destinations (balanced unescaped parentheses to cmark's 32 levels), `scan_link_title` for titles with the sub-chunk slicing guard so scanning never reads past the chunk's end, the blank-line title rejection, and cmark's rewind-before-title rule.
- **Re-ran the writer checks on cloud3** (LLVM 20.1.8; pin hash-verified) against the real `cm_buffer` / `cm_utf8` / `cm_escape` / `cm_scan` modules: `check.py` exit 0, all six PASS groups at -O0 and -O2, matching the committed log. The writer's extra verification (failing-stub relay checks for all four dependencies plus a `move(RefMap)` ownership case, 12 cases at both levels) is recorded in their notes.

## Notes

1. The lookup-side index is an open-addressed hash maintained at insert time, so `refmap_lookup` never mutates its lent map — a clean fit for the contract's borrow rules, and the growth boundary is covered in the checks (the 1000-byte label boundary likewise).
2. Still outstanding from this writer, from the `utf8` review: the utf8 fix commit (harness on the real `cm_buffer` with a refreshed log; case-fold and punctuation tables regenerated from the files now in `commonmark/spec/`). Not part of this part's verdict — recorded here so the debt stays visible in one place.

## Compiler notes

None. No possible compiler fault observed by the writer or on the re-run; -O0 and -O2 agree throughout.
