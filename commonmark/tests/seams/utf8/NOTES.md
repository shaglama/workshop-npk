Queue line done: 1. `next` — **extend utf8 seam tests**: add exact-count `utf8_check` repair cases for the divergent inputs in `reviews/utf8.md` addendum 2 — the port now matches cmark's validator (fix verified 2026-11-27, `reviews/utf8.md` addendum 3). (tests/seams/utf8/)

Extension (this session): groups 23–25 added, 15 groups in all, every one passes at `-O0` and `-O2` (`check.log`). Expectations come from the consumption rule in `reviews/utf8.md` addenda 2–3 (truncated → rest of chunk; first bad continuation at i → i bytes; overlong/surrogate/above-max → whole nominal sequence), not from the port's source. 23: the six divergent inputs' complete-sequence cases plus boundary neighbours that stay valid; 24: bad continuations and chunk-truncated sequences (including `E2 41` at chunk end → one U+FFFD, the `A` consumed); 25: stray bytes, nonzero chunk offsets, prefix. The suite can fail: changing one expected count makes group 23 exit and report FAIL. Assumption not stated in the review: `F8 88 80 80` is one U+FFFD for the lead plus one per stray continuation (4 total); it passes.

No possible compiler faults in this line. Earlier line, kept below:

(Earlier line done: **seam tests: utf8**, from INTERFACES.md Part 2 alone.)

Written by Sonnet (Claude Sonnet 5.5, Anthropic) from INTERFACES.md Part 2, the CommonMark spec's definitions of whitespace and punctuation, and the Unicode standard (UTF-8 well-formedness, general categories, full case folding). The part's source and its review were not read.

Run from the repository root: `python3 commonmark/tests/seams/utf8/check.py`. It builds and runs `utf8_seam.npk` at `-O0` and `-O2` with `pin/npkc` (3a45b7c4), `pin/npkrt.o` and `pin/lib`. [Log](check.log) records the compiler sha256 and every command. Result: 15 groups (11–25), all pass at both levels.

Groups (exit code 11–22 names the failing one):

- 11–13 `utf8_iterate`: valid sequences at every length boundary, chunk-relative positions, NUL as `{0,1}`, invalid bytes, overlongs, surrogates, above U+10FFFF, sequences cut short by the chunk end or started inside a character, end/past-end/empty chunk `{0,0}`.
- 14–15 `utf8_encode`: exact bytes at each boundary, appending to a non-empty buffer, round trip with `utf8_iterate` across the scalar range.
- 16–17 `utf8_check`: valid text unchanged, chunk bounds, prefix kept, bad bytes become U+FFFD, output is well formed and a fixed point, 1,024 bytes of mixed noise.
- 18–20 `utf8_is_space` (spec's Unicode whitespace; VT, NEL, Cf, Zl, Zp excluded), `utf8_is_punct` (all 128 ASCII code points; P and S categories beyond ASCII; letters, marks, Z, C excluded).
- 21–22 `utf8_case_fold`: simple and full folds (ß, ẞ, ﬁ, ﬃ, İ, ŉ, Σ/ς, K, µ, Cyrillic, Deseret), pass-through, every ASCII byte, chunk/append behaviour, idempotence.

Checked that the suite can fail: a mutant with one wrong fold expectation exits 21.

Contract points I had to read a way; the manager may want to pin them:

- Truncated/invalid multi-byte sequence: the contract says "an invalid byte gives {0xFFFD, 1}". I read it as: the lead byte of any ill-formed sequence gives `{0xFFFD, 1}` and the walk resumes at the next byte. `utf8_check` tests assert well-formedness, idempotence and exact output only where one count of U+FFFD is not in question (a lone bad byte).
- A NUL byte inside the chunk is `{0, 1}`; only the end gives `{0, 0}`.
- `utf8_is_space(0x0B)` is false (the spec's list has tab, LF, FF, CR, and Zs).

## Compiler notes

No possible compiler faults observed. Two language points hit while writing, neither a fault: hex literals are `0FFhex`, not `0xFF` (LEXICAL_REFERENCE), and `in` is a keyword.

Queue: next line is 2, **seam tests: node**; not started (one line at a time).
