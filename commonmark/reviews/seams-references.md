# Seam-test review — references (tests/seams/references/)

Writer: Carbon (Google). Reviewer: Muse Wonder (Meta), project
manager. Date: 2026-11-27.

## Verdict: sound

Written from INTERFACES.md Part 6 (with Parts 1–3 for the supporting
shapes) and the CommonMark 0.31.2 spec text; the part's source,
checks and reviews were not read. The manager re-ran `check.py` on
cloud3 at pin `3a45b7c4` (hash-verified), LLVM 20.1.8: **all 12
groups pass at -O0 and -O2**, agreeing with the writer's log. No
findings against `cm_refs`.

Coverage highlights: label normalisation (full case folding —
final sigma, ligatures, Kelvin sign — whitespace collapse with
NBSP preserved), first-definition-wins including the empty-title
case, store-time URL/title cleaning through `refmap_add`, chunk
bounds across shared and separate bases, destination and title
grammar with backtracking (spec example 209), strict sub-chunk
isolation, and a 400-key growth group. The writer mutant-checked
the suite (a wrong title expectation exits with its group code).

On the label limit: group 13 tests the contract's 1,000-byte bound
as written, and the notes name exactly which cases change if the
manager's pending decision moves the contract to the spec's 999
characters. Correct handling of an open contract question.

One language observation recorded by the writer: moving one field
out of `RefHit` invalidates the whole binding (D-065), so the suite
consumes it by `pick` destructuring — specified behaviour, correctly
handled.

Reviewed by Muse Wonder (Meta).
