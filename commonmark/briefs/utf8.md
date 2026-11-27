# Brief: part 2 — `utf8` (module `cm_utf8`)

**Writer:** Neon (Google). **Reviewer:** Sol (OpenAI). **Seam tests:** Carbon, in `tests/seams/utf8/`, written from the contract alone.
**Repo:** `shaglama/workshop-npk`, branch `work/commonmark`, folder `commonmark/`. **Compiler pin:** `3a45b7c4`.
**You may write only:** the folders in `commonmark/assign/neon.txt` that this brief names — for this part, `src/utf8/`.

## Read first

- `commonmark/INTERFACES.md` — the frozen contract: the shared conventions, the failure section, and Part 2. You code to it exactly.
- `commonmark/PLAN.md` — where this part sits; note the "Data tables" section.
- cmark 0.31.2: `src/utf8.c`, `src/utf8.h`, `src/case_fold.inc` — the behaviour and the data you are porting.
- The lab's `lab/context/known-issues.md` (in the outside-exchange repo) — open compiler faults to recognise, not rediscover.

## The job

Implement `cm_utf8` in `src/utf8/`: iterate / encode / validate-and-repair, the space and punctuation classes, and case folding, with the contract's exact signatures and failure marks. Edge results the contract states — implement them as written: an invalid byte decodes as `{ 0xFFFD, 1 }`; a position at or past the chunk's end gives `{ 0, 0 }`.

The case-folding table is **generated data**: write a small generator script that produces the Nitpick data module from cmark's `case_fold.inc` at tag 0.31.2, keep the script beside the table in `src/utf8/`, name the source file and tag in the generated module's header, and commit both. Nobody hand-edits the generated table.

## Checks

Include in `src/utf8/checks/` a small harness program that exercises every function (ASCII, multi-byte characters, invalid sequences and their repair, folding of cased characters, class checks at the boundaries), built and run at **-O0 and -O2**, with a log recording the commands, the compiler commit, npkc's sha256, and the outputs. Expected results come from the Unicode/cmark behaviour and your own hand computation — never from the part's output copied back.

## Rules that apply to every part

- If the contract cannot be implemented as written, **stop and say so** in a note in your folder; do not deviate silently. Contract changes go through the manager as a pull request.
- If something looks like a compiler fault: check `known-issues.md` first, cut it to the smallest program that shows it, and record it in a `notes.md` in your folder (program, compiler commit, expected vs actual) — then work around it and keep going. A crash, output that differs between -O0 and -O2, or output that changes from run to run is recorded as a possible compiler fault **before** you debug the port around it.
- Credit: a header line in the part's main file — "Written by Neon (Google)."
- End in a commit on `work/commonmark` naming the part, with its checks.
