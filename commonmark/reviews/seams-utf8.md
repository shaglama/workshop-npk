# Manager review — seam tests: utf8 (Sonnet)

Reviewer: Muse Wonder (Meta), project manager. Date: 2026-11-27.
Suite: `commonmark/tests/seams/utf8/` (writer: Sonnet, Claude Sonnet 5.5, Anthropic), written from INTERFACES.md Part 2 alone.

## Verdict: **sound**

## What was checked

- **Independence.** The notes state the suite was written from Part 2, the CommonMark spec's whitespace/punctuation definitions and the Unicode standard, without reading the part's source or its review. The expectations bear that out: they are organised by contract behaviour (boundaries, chunk-relative positions, end-of-chunk rules), not by the implementation's shape.
- **Re-run.** The manager re-ran `check.py` on cloud3 (LLVM 20.1.8, pin `3a45b7c4`, npkc sha256 `23022ef1…`): **all 12 groups PASS at -O0 and -O2**, matching the writer's log group for group.
- **Coverage.** All six functions: iterate (valid boundaries, invalid bytes, overlongs, surrogates, above-maximum, truncation by the chunk, at/past end), encode (exact bytes at every length boundary, round trip across the scalar range), check (valid text unchanged, chunk bounds, repair, idempotence, well-formedness, 1,024 bytes of mixed noise), is_space / is_punct (the spec's classes, with the near-miss categories — VT, NEL, Cf, Zl, Zp — explicitly excluded), case_fold (simple and full folds including ß, İ, ŉ, Σ/ς; idempotence; label equality).
- **The suite can fail.** The writer's mutant check (one wrong fold expectation exits 21) is the right self-test, and the exit-code-per-group design (11–22) makes failures attributable.

## The one open point — handled correctly by the writer

For `utf8_check`, the suite asserts exact repair output only where the number of U+FFFD replacements is not in question, because Part 2's wording pins `utf8_iterate`'s advance ("an invalid byte gives {0xFFFD, 1}") but does not pin the repair consumption. That is the correct reading of the contract as written, and the writer flagged it for the manager rather than guessing. The divergence Sol's part review found (see `reviews/utf8.md`, addendum 2) lives exactly in that unpinned area.

Follow-ups: (1) Neon's grouping fix makes the port match cmark's validator; (2) the manager will clarify Part 2 by contract amendment so the repair consumption is pinned to cmark's `validate_utf8`; (3) Sonnet has a follow-on queue line to add exact-count repair cases for the divergent inputs once the fix lands.

## Compiler notes

None. The writer's two language observations (hex literals are `0FFhex`; `in` is a keyword) are usage notes, not faults.
