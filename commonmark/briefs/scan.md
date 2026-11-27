# Brief: part 4 — `scan` (module `cm_scan`)

**Writer:** Sol (OpenAI). **Reviewer:** Carbon (Google). **Seam tests:** Astra, in `tests/seams/scan/`, written from the contract alone.
**Repo:** `shaglama/workshop-npk`, branch `work/commonmark`, folder `commonmark/`. **Compiler pin:** `3a45b7c4`.
**You may write only:** the folders in `commonmark/assign/sol.txt` that this brief names — for this part, `src/scan/`.

## Read first

- `commonmark/INTERFACES.md` — the frozen contract: the shared conventions, the failure section, and Part 4. You code to it exactly.
- `commonmark/PLAN.md` — where this part sits and who calls it (both parsers).
- cmark 0.31.2: `src/scanners.re` and `src/scanners.h` — the patterns you are porting. `scanners.re` is the source of truth; the generated `scanners.c` shows the same patterns as state machines if a pattern's reading is unclear.
- The lab's `lab/context/known-issues.md` (in the outside-exchange repo) — open compiler faults to recognise, not rediscover.

## The job

Implement `cm_scan` in `src/scan/`: every scanner in the contract's Part 4 list, hand-written from the `scanners.re` patterns. Each scans a lent base from a byte position and returns the length matched, or 0 for no match; all are `never fails`. Match the patterns exactly — including the HTML block start/end conditions and the dangerous-URL pattern — rather than approximating them; the spec examples will find any difference.

## Checks

Include in `src/scan/checks/` a small harness program that exercises every scanner with matching and non-matching inputs (including matches that end exactly at the end of the input, and near-misses that share a prefix with a real match), built and run at **-O0 and -O2**, with a log recording the commands, the compiler commit, npkc's sha256, and the outputs. Expected match lengths come from the patterns themselves, worked by hand — never from the part's output copied back.

## Rules that apply to every part

- If the contract cannot be implemented as written, **stop and say so** in a note in your folder; do not deviate silently. Contract changes go through the manager as a pull request.
- If something looks like a compiler fault: check `known-issues.md` first, cut it to the smallest program that shows it, and record it in a `notes.md` in your folder (program, compiler commit, expected vs actual) — then work around it and keep going. A crash, output that differs between -O0 and -O2, or output that changes from run to run is recorded as a possible compiler fault **before** you debug the port around it.
- Credit: a header line in the part's main file — "Written by Sol (OpenAI)."
- End in a commit on `work/commonmark` naming the part, with its checks.
