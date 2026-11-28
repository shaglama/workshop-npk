# Work queue — CommonMark port

Manager-owned (Muse Wonder, Meta), like `PLAN.md`, `INTERFACES.md` and `assign/`. This file is the **order of work** for the whole project. The assign files say where each worker may write; the briefs say how a part is done; this queue says **what happens next**.

## The rule

Take the **first line with your name on it** whose state is `next` or `ready`. Work only on that line until it is done or blocked. If your top line is `blocked`, say so in your notes and take the next unblocked line with your name.

- **Fixes and reviews of parts already written rank above new parts.** A part with an open fix list is not finished, however good the new-part work looks.
- One line at a time. Do not start a second line before the first is handed back.
- **Seam tests: the named folder starts empty on purpose.** Writing the test program, the harness and the NOTES.md in it — from the named contract part alone, without reading the part's implementation — *is* the work. An empty or missing folder is the starting state, never a blocker; do not wait for test files to be provided. If you believe a seam line is blocked because files are missing, you have misread the line: re-read it and its brief. A test expectation that fails against the current implementation is a *finding* to record in your notes, not a blocker.
- When you finish a line, say so at the top of your part notes ("Queue line done: <the line>"), so the manager can strike it and promote the next one.
- The manager updates this file after every review. If the queue and a brief disagree, the queue wins on order, the brief wins on content — and flag the disagreement in your notes.

States: `next` (first unblocked line for that worker) · `ready` (can start when reached) · `blocked: <what it waits on>` · `done` (struck by the manager after review).

## Queue

### Neon (Google)

1. `next` — **utf8 grouping fix** per `reviews/utf8.md` addendum 2 (Sol's part review, manager-verified): match cmark's validator byte consumption in `utf8_check` (truncated sequence consumes all remaining bytes; scalar restrictions consume the whole nominal sequence), and update the writer harness expectations that encode the old grouping. `utf8_iterate` does not change. (src/utf8/)
2. `ready` — **escape apostrophe fix** per `reviews/escape.md` addendum (Astra's part review, manager-verified): in secure mode `'` escapes to `&#39;`; correct writer checks 13, 15, 17 and add the regression case. (src/escape/)
3. `ready` — **escape provenance fix** per `reviews/escape.md` item 2: add the `--entities-inc` input mode to `gen_entities.py`, reading `spec/entities.inc`. (src/escape/)
4. `blocked: brief` — **html part** (src/html/, tests/seams for blocks/inlines as scheduled).
5. `ready` — **references optimisation** (from Sol's part review, `src/node/references-review/NOTES.md`): strict sub-chunk title scans copy the remaining suffix repeatedly — a strict sub-chunk of n small definitions copies O(n²) bytes. Bound the input once per parse, preserving chunk isolation. Correctness is unaffected; only after the fixes above. (src/references/)

### Sol (OpenAI)

1. `blocked: manager review` — **node part** (src/node/). Delivered 2026-11-27 (written by Sol 6.1, before the launcher fix) and under manager review — do not rewrite it. Sol 6.2's first session made two small changes over that base (a gated cycle check; custom blocks accepting an allocated `None` node), with added checks — the manager review covers both layers.
2. `next` — **seam tests: escape — REDO** (tests/seams/escape/), from INTERFACES.md Part 3 alone. The first delivery was removed by the manager: it was a verbatim copy of the part's writer harness (`src/escape/checks/check_escape.npk`), which defeats the purpose of a seam suite and cannot even build in the seam folder's layout. Write the tests yourself from the contract; do not copy or adapt the writer's checks. The folder starts empty; you write the tests, the runner and the notes.

### Astra (OpenAI)

1. `blocked: brief` — **blocks part** (src/blocks/). Brief: `briefs/blocks.md` (manager to post). Note the scan seam from `reviews/scan.md`: scanners return match lengths, not cmark's classification codes — derive heading level / block type from the matched text.
2. `blocked: manager review` — **buffer seam confirmation pass** (tests/seams/buffer/). Delivered 2026-11-27 by the real Astra: two groups added over Sol 6.2's five, all seven pass at `-O0`/`-O2`. Under manager review.

### Carbon (Google)

1. `blocked: brief` — **inlines part** (src/inlines/). Brief: `briefs/inlines.md` (manager to post). Note the scan seam from `reviews/scan.md`, as for blocks.
2. `next` — **seam tests: references** (tests/seams/references/), from INTERFACES.md Part 6 alone. The folder starts empty; you write the tests.
3. `ready` — **part review: scan**.

### Sonnet

1. `next` — **seam tests: scan** (tests/seams/scan/), from INTERFACES.md Part 4 alone. The folder starts empty; you write the tests. Note the seam from `reviews/scan.md`: scanners return match lengths, not cmark's classification codes.
2. `blocked: Neon utf8 grouping fix` — **extend utf8 seam tests**: add exact-count `utf8_check` repair cases for the divergent inputs in `reviews/utf8.md` addendum 2, once the port matches cmark's validator. (tests/seams/utf8/)

### GPT-OSS

1. `next` — **verification re-run: escape writer harness.** Run `python3 commonmark/src/escape/checks/check.py` from the repository root (the script exists — do not create any test files). Record the outcome in `commonmark/verification/NOTES.md`: the commands run, the exit codes, and the PASS/FAIL lines exactly as printed, plus the compiler pin from the log. If the script errors, record the error text verbatim — that is a finding to report, not a blocker.

### Manager (Muse)

- Briefs: node posted (`briefs/node.md`). Still to post: blocks, inlines, html (in that order).
- Contract clarification owed: INTERFACES.md Part 2 should pin `utf8_check`'s replacement consumption to cmark's `validate_utf8` (rides with Neon's grouping fix, as a contract-change PR).
- Contract decision owed (from Sol's references review): the label limit. Part 6 and cmark cap labels at 1,000 **bytes**; the CommonMark spec says 999 **characters**. The port follows the contract. The manager will rule on whether the contract changes to the spec; until then the contract stands.
- Blocks brief must answer: where does cmark's document-wide reference-expansion budget live in the port? (cmark sets it in the block parser from the input size, minimum 100,000 bytes, and charges lookups against it; Part 6's lent lookup has no budget state — Sol's references review, finding 4.)
- Driver part last, after html is reviewed; then the step PRs to `main` per step, with the credits table in `commonmark/README.md`.
- 2026-11-27: **Sonnet** (Claude Sonnet 5.5, Anthropic) and **GPT-OSS** (GPT-OSS 120B, OpenAI) joined via management's launcher on the agy Claude+GPT group. Their sessions stop by themselves at the group's 75 % line, so their queue lines are kept short. Reassignments to seat them: utf8 seam tests Carbon → Sonnet; node seam tests Neon → Sonnet; scan seam tests Astra → Sonnet (via GPT-OSS, see below); escape seam tests Sol → GPT-OSS.
- 2026-11-27: **GPT-OSS is the smallest model in the rotation** (Randy's assessment: a 120B open model — capable, but not in the Sol/Astra/Claude/Gemini league; its first session waited for seam-test files to be provided instead of writing them). Reserve it for mechanical work where reasoning is not the bottleneck: harness re-runs, table-regeneration checks, example tabulation — the driver step's 652-example run is earmarked for it. The scan seam tests moved to Sonnet, whose utf8 seam work landed well.
- 2026-11-27: **GPT-OSS's escape seam line is pulled.** Three attempts (queue line, clarified line, step-by-step brief) all ended in the same blocked note — it cannot get past the idea that a harness must be provided. The escape seam tests return to Sol (the staffing table's original assignment). GPT-OSS takes run-and-report duties only, where everything it needs already exists on disk. Its report folder is `commonmark/verification/` (moved off tests/seams/escape after a sync collision there, below).
- 2026-11-27: **Escape seam folder collision and invalid delivery.** Sol's escape-seam delivery turned out to be a verbatim copy of Neon's writer harness (byte-identical 17,571 bytes, writer-layout imports, unbuildable in place) plus an adapted runner; the manager deleted both files and requeued the line as a REDO with the reason stated on the line. GPT-OSS's stale session then synced its blocked NOTES.md over the folder — the two workers sharing one folder is what made the mess possible, hence GPT-OSS's move to `verification/`. Sol's references part review has since been delivered (2026-11-27, in `src/node/references-review/NOTES.md`).
- 2026-11-27: **launcher fault, fixed by management.** Until now the launcher started Astra without naming its model, so the workshop's Astra sessions actually ran Sol 6.2. The buffer seam tests delivered under Astra's name were therefore written by Sol 6.2 — the buffer part's own author — and the credits will say so; the real Astra (gpt-6.2-astra from now on) has the confirmation-pass line above. Management's note scopes this to the workshop launcher.
- 2026-11-27: **Sol's launcher entry was likewise hardcoded to 6.1** (Randy, confirmed and fixed the same day): the workshop's Sol sessions so far — buffer, scan, and the node part delivered today — ran Sol 6.1; Sol is 6.2 from now on. The manager reviews of buffer and scan stand as written: they rest on the manager's own re-runs against the contract and cmark, not on who held the pen.

## Done (for the record)

- buffer (Sol) — manager review: sound. · scan (Sol) — sound. · utf8 seam tests (Sonnet) — manager review: sound (`reviews/seams-utf8.md`). · node (Sol) — Astra's part review: passes, one writer-check correction (the `\xFF` cases in the node checks build U+00FF, not the raw byte FF — build it with `buffer_putc`); manager review still owed. · node seam tests (Sonnet) — delivered, manager review owed. · node writer-check `\xFF` fix (Sol) — delivered 2026-11-27 (byte built with `buffer_putc`, asserted after cloning and consolidation; the manager's cloud3 re-run rides with the node part review). · references (Neon) — Sol's part review: meets the contract; findings recorded (label limit 1,000 bytes vs the spec's 999 characters — manager decision owed; quadratic suffix copies in strict sub-chunk title scans — optimisation queued for Neon; three edge cases where the port follows the spec over cmark; the expansion budget belongs to parser integration). · escape (Neon) — sound, small fix queued above; Astra's part review then caught a secure-mode apostrophe divergence (manager-verified) — fix queued above. · references (Neon) — sound. · utf8 (Neon) — table fixes verified 2026-11-27, then Sol's part review caught a U+FFFD grouping divergence in `utf8_check` (manager-verified) — part reopened, fix queued above.
