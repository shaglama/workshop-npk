# Manager's review: part 2 — `utf8` (cm_utf8)

**Writer:** Neon (Google). **Manager's review:** Muse Wonder (Meta). **Part review (PLAN):** Sol (OpenAI) — still to come. **Seam tests (PLAN):** Carbon, `tests/seams/utf8/` — still to come.
**Verdict: sound with fixes.** The module itself is right; the fixes are in its checks and its generated tables.

## What was checked

- `cm_utf8.npk` read against INTERFACES.md Part 2: all six functions present with the contract's signatures and failure marks; the stated edge results are implemented as written (invalid byte → `{ 0xFFFD, 1 }`; position at/past the end → `{ 0, 0 }`); `utf8_is_space` matches cmark's `utf8.c` list exactly (21 code points); failures from `cm_buffer` are relayed unchanged (Neon's failing-stub seam check demonstrates this, and the code reads that way). No `main`, no `failsafe`, no error constants.
- **The tables were compared against cmark 0.31.2's own data, entry by entry** (the manager fetched `src/case_fold.inc` and `src/utf8.c` at tag 0.31.2):
  - *Case folding:* every one of Neon's 1,504 entries matches cmark exactly — no wrong folds, no extra entries. **But 55 code points are missing** (U+1C89, U+A7CB–U+A7DC, U+10D50 and neighbours, …): cmark 0.31.2's table is Unicode 16 data, while the system `libutf8proc` Neon generated from is Unicode 15.1.0. Neon's notes claim the two match; for these 55 they do not.
  - *Punctuation/symbol ranges:* the sets agree except **5 code points Neon counts as punct and cmark does not**: U+2FFC–U+2FFF and U+31EF. Here Neon's Unicode 15.1 data is *newer* than cmark's hand-kept list in `utf8.c` — but the port's oracle is cmark, so cmark's list governs.
- **Re-ran the checks on cloud3** (LLVM 20.1.8; pin hash-verified, npkc `23022ef1…`): as committed, the harness does not build — `NITPICK-RESOLVE-007 … cm_buffer.npk has no buffer_new` — because `check_utf8.npk` still uses the pre-rename constructor. Neon's log is honest about this: their PASS was produced against a temporary stub buffer in /tmp, since their sandbox tree had no `src/buffer/` (the parallel-build/symlink problem, since fixed). With the single identifier changed to `buffer_create` (import + 8 call sites, review copy only), the harness builds against the real `cm_buffer` and prints all six PASS lines at -O0 and -O2, exit 0.
- Neon's exhaustive sweep (all 1,114,112 code points: class checks, encode→iterate round-trip, case-fold digest, matched against a libutf8proc oracle at both optimisation levels) is strong evidence for everything except the table deltas above, which the same-version oracle could not see.

## Fixes for Neon (next utf8 commit)

1. `check_utf8.npk`: `buffer_new` → `buffer_create` throughout, and refresh `check.log` with a run against the real `src/buffer/` in the normal tree layout (no stub), at -O0 and -O2.
2. Regenerate `cm_utf8_tables.npk` from cmark 0.31.2's own files: `gen_tables.py --case-fold-inc` against the real `case_fold.inc` (adds the 55 missing folds), and take the punct ranges from `utf8.c`'s list (removes the 5 extra code points). The generator already supports the first; the manager can supply `case_fold.inc` (52 KB, public) through the launch if the sandbox still has no cmark checkout.
3. `notes.md`: the "Contract note for management" section describes the pre-rename contract as current. PR #3 has since landed the rename; update or remove that section.

## Compiler notes

None against the compiler. One spec-wording observation from Neon, verified by the manager (smallest program in Neon's `notes.md`; re-run on cloud3 at -O0, exit 2 as reported): in a `string` literal, `"\xFF"` is the character U+00FF — two UTF-8 bytes — while a `char8` literal `'\xFF'` is one byte (TYPE §2.2). `LEXICAL_REFERENCE.md` §6.3 does not state the string-literal behaviour. Consistent behaviour, unstated in the spec; recorded in `commonmark/NOTES.md`.
