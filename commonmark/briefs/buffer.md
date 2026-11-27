# Brief: part 1 — `buffer` (module `cm_buffer`)

**Writer:** Sol (OpenAI). **Reviewer:** Neon (Google). **Seam tests:** Astra, in `tests/seams/buffer/`, written from the contract alone.
**Repo:** `shaglama/workshop-npk`, branch `work/commonmark`, folder `commonmark/`. **Compiler pin:** `3a45b7c4`.
**You may write only:** the folders in `commonmark/assign/sol.txt` that this brief names — for this part, `src/buffer/`.

## Read first

- `commonmark/INTERFACES.md` — the frozen contract: the shared conventions, the failure section, and Part 1. You code to it exactly.
- `commonmark/PLAN.md` — where this part sits and who depends on it (everyone does).
- cmark 0.31.2: `src/buffer.c`, `src/buffer.h`, `src/chunk.h` — the behaviour you are porting.
- The lab's `lab/context/known-issues.md` (in the outside-exchange repo) — open compiler faults to recognise, not rediscover.

## The job

Implement `cm_buffer` in `src/buffer/`: the growable byte buffer and the chunk helpers, with the contract's exact signatures and failure marks. Points the contract already decided — do not re-decide them: `buffer_detach` consumes the buffer; a `Chunk` is `{ off, len }` and always travels with its lent base; lengths are `int64` bytes.

## Checks

Include in `src/buffer/checks/` a small harness program that exercises every function (append by chunk/string/byte, clear and reuse, detach, chunk trim/eq/to_string, growth past the initial capacity), built and run at **-O0 and -O2**, with a log recording the commands, the compiler commit, npkc's sha256, and the outputs. The harness's expected results come from cmark's documented behaviour and your own hand computation — never from the part's output copied back.

## Rules that apply to every part

- If the contract cannot be implemented as written, **stop and say so** in a note in your folder; do not deviate silently. Contract changes go through the manager as a pull request.
- If something looks like a compiler fault: check `known-issues.md` first, cut it to the smallest program that shows it, and record it in a `notes.md` in your folder (program, compiler commit, expected vs actual) — then work around it and keep going. A crash, output that differs between -O0 and -O2, or output that changes from run to run is recorded as a possible compiler fault **before** you debug the port around it.
- Credit: a header line in the part's main file — "Written by Sol (OpenAI)."
- End in a commit on `work/commonmark` naming the part, with its checks.
