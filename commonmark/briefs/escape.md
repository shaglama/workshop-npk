# Brief: part 3 — `escape` (module `cm_escape`)

**Writer:** Neon (Google). **Reviewer:** Astra (OpenAI). **Seam tests:** Sol, in `tests/seams/escape/`, written from the contract alone.
**Repo:** `shaglama/workshop-npk`, branch `work/commonmark`, folder `commonmark/`. **Compiler pin:** `3a45b7c4`.
**You may write only:** the folders in `commonmark/assign/neon.txt` that this brief names — for this part, `src/escape/`.

## Read first

- `commonmark/INTERFACES.md` — the frozen contract: the shared conventions, the failure section, and Part 3. You code to it exactly.
- `commonmark/PLAN.md` — where this part sits; note the "Data tables" section.
- cmark 0.31.2: `src/houdini_html_e.c`, `src/houdini_href_e.c`, `src/houdini_html_u.c`, `src/houdini.h`, `src/entities.inc`, and `cmark_clean_url` / `cmark_clean_title` / `cmark_strbuf_unescape` in `src/inlines.c` — the behaviour and the data you are porting.
- The lab's `lab/context/known-issues.md` (in the outside-exchange repo) — open compiler faults to recognise, not rediscover.

## The job

Implement `cm_escape` in `src/escape/`: HTML escaping, href escaping, entity unescaping, backslash unescaping, and `clean_url` / `clean_title`, with the contract's exact signatures and failure marks. The cleaning order is cmark's: entity-unescape, then backslash-unescape, then trim. A backslash before an ASCII punctuation character is dropped; any other backslash is kept.

The entity table is **generated data**: write a small generator script that produces the Nitpick data module from cmark's `entities.inc` at tag 0.31.2 — a verbatim copy is in the repo at `commonmark/spec/entities.inc`, so no cmark checkout is needed — keep the script beside the table in `src/escape/`, name the source file and tag in the generated module's header, and commit both. Nobody hand-edits the generated table.

## Checks

Include in `src/escape/checks/` a small harness program that exercises every function (named, decimal and hex entities; unknown entities left alone; backslash before punctuation vs before letters; href escaping of the characters cmark lists; clean_url/clean_title on inputs that exercise each step of the order), built and run at **-O0 and -O2**, with a log recording the commands, the compiler commit, npkc's sha256, and the outputs. Expected results come from cmark's source behaviour and your own hand computation — never from the part's output copied back.

## Rules that apply to every part

- If the contract cannot be implemented as written, **stop and say so** in a note in your folder; do not deviate silently. Contract changes go through the manager as a pull request.
- If something looks like a compiler fault: check `known-issues.md` first, cut it to the smallest program that shows it, and record it in a `notes.md` in your folder (program, compiler commit, expected vs actual) — then work around it and keep going. A crash, output that differs between -O0 and -O2, or output that changes from run to run is recorded as a possible compiler fault **before** you debug the port around it.
- Credit: a header line in the part's main file — "Written by Neon (Google)."
- End in a commit on `work/commonmark` naming the part, with its checks.
