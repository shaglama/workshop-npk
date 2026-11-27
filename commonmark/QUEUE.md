# Work queue — CommonMark port

Manager-owned (Muse Wonder, Meta), like `PLAN.md`, `INTERFACES.md` and `assign/`. This file is the **order of work** for the whole project. The assign files say where each worker may write; the briefs say how a part is done; this queue says **what happens next**.

## The rule

Take the **first line with your name on it** whose state is `next` or `ready`. Work only on that line until it is done or blocked. If your top line is `blocked`, say so in your notes and take the next unblocked line with your name.

- **Fixes and reviews of parts already written rank above new parts.** A part with an open fix list is not finished, however good the new-part work looks.
- One line at a time. Do not start a second line before the first is handed back.
- **Seam tests: the named folder starts empty on purpose.** Writing the test program, the harness and the NOTES.md in it — from the named contract part alone, without reading the part's implementation — *is* the work. An empty or missing folder is the starting state, never a blocker; do not wait for test files to be provided.
- When you finish a line, say so at the top of your part notes ("Queue line done: <the line>"), so the manager can strike it and promote the next one.
- The manager updates this file after every review. If the queue and a brief disagree, the queue wins on order, the brief wins on content — and flag the disagreement in your notes.

States: `next` (first unblocked line for that worker) · `ready` (can start when reached) · `blocked: <what it waits on>` · `done` (struck by the manager after review).

## Queue

### Neon (Google)

1. `next` — **utf8 grouping fix** per `reviews/utf8.md` addendum 2 (Sol's part review, manager-verified): match cmark's validator byte consumption in `utf8_check` (truncated sequence consumes all remaining bytes; scalar restrictions consume the whole nominal sequence), and update the writer harness expectations that encode the old grouping. `utf8_iterate` does not change. (src/utf8/)
2. `ready` — **escape apostrophe fix** per `reviews/escape.md` addendum (Astra's part review, manager-verified): in secure mode `'` escapes to `&#39;`; correct writer checks 13, 15, 17 and add the regression case. (src/escape/)
3. `ready` — **escape provenance fix** per `reviews/escape.md` item 2: add the `--entities-inc` input mode to `gen_entities.py`, reading `spec/entities.inc`. (src/escape/)
4. `blocked: brief` — **html part** (src/html/, tests/seams for blocks/inlines as scheduled).

### Sol (OpenAI)

1. `blocked: manager review` — **node part** (src/node/). Delivered 2026-11-27 (written by Sol 6.1, before the launcher fix) and under manager review — do not rewrite it. Sol 6.2's first session made two small changes over that base (a gated cycle check; custom blocks accepting an allocated `None` node), with added checks — the manager review covers both layers.
2. `next` — **part review: references**.

### Astra (OpenAI)

1. `blocked: brief` — **blocks part** (src/blocks/). Brief: `briefs/blocks.md` (manager to post). Note the scan seam from `reviews/scan.md`: scanners return match lengths, not cmark's classification codes — derive heading level / block type from the matched text.
2. `blocked: manager review` — **buffer seam confirmation pass** (tests/seams/buffer/). Delivered 2026-11-27 by the real Astra: two groups added over Sol 6.2's five, all seven pass at `-O0`/`-O2`. Under manager review.
3. `next` — **part review: node** (runs alongside the manager review; both reads are wanted).

### Carbon (Google)

1. `blocked: brief` — **inlines part** (src/inlines/). Brief: `briefs/inlines.md` (manager to post). Note the scan seam from `reviews/scan.md`, as for blocks.
2. `next` — **seam tests: references** (tests/seams/references/), from INTERFACES.md Part 6 alone. The folder starts empty; you write the tests.
3. `ready` — **part review: scan**.

### Sonnet

1. `next` — **seam tests: utf8** (tests/seams/utf8/), from INTERFACES.md Part 2 alone.
2. `ready` — **seam tests: node** (tests/seams/node/), from INTERFACES.md Part 5 alone. The folder starts empty; you write the tests.
3. `ready` — **seam tests: scan** (tests/seams/scan/), from INTERFACES.md Part 4 alone. The folder starts empty; you write the tests. Note the seam from `reviews/scan.md`: scanners return match lengths, not cmark's classification codes.

### GPT-OSS

1. `next` — **seam tests: escape** (tests/seams/escape/), from INTERFACES.md Part 3 alone. The folder starts empty — you write the test program and harness (see the seam-test rule above); replace the blocked-status NOTES.md from the first attempt with the real notes.

### Manager (Muse)

- Briefs: node posted (`briefs/node.md`). Still to post: blocks, inlines, html (in that order).
- Driver part last, after html is reviewed; then the step PRs to `main` per step, with the credits table in `commonmark/README.md`.
- 2026-11-27: **Sonnet** (Claude Sonnet 5.5, Anthropic) and **GPT-OSS** (GPT-OSS 120B, OpenAI) joined via management's launcher on the agy Claude+GPT group. Their sessions stop by themselves at the group's 75 % line, so their queue lines are kept short. Reassignments to seat them: utf8 seam tests Carbon → Sonnet; node seam tests Neon → Sonnet; scan seam tests Astra → Sonnet (via GPT-OSS, see below); escape seam tests Sol → GPT-OSS.
- 2026-11-27: **GPT-OSS is the smallest model in the rotation** (Randy's assessment: a 120B open model — capable, but not in the Sol/Astra/Claude/Gemini league; its first session waited for seam-test files to be provided instead of writing them). Reserve it for mechanical work where reasoning is not the bottleneck: harness re-runs, table-regeneration checks, example tabulation — the driver step's 652-example run is earmarked for it. It keeps the escape seam tests (the most bounded suite: six functions, byte-level expectations); the scan seam tests moved to Sonnet, whose utf8 seam work landed well.
- 2026-11-27: **launcher fault, fixed by management.** Until now the launcher started Astra without naming its model, so the workshop's Astra sessions actually ran Sol 6.2. The buffer seam tests delivered under Astra's name were therefore written by Sol 6.2 — the buffer part's own author — and the credits will say so; the real Astra (gpt-6.2-astra from now on) has the confirmation-pass line above. Management's note scopes this to the workshop launcher.
- 2026-11-27: **Sol's launcher entry was likewise hardcoded to 6.1** (Randy, confirmed and fixed the same day): the workshop's Sol sessions so far — buffer, scan, and the node part delivered today — ran Sol 6.1; Sol is 6.2 from now on. The manager reviews of buffer and scan stand as written: they rest on the manager's own re-runs against the contract and cmark, not on who held the pen.

## Done (for the record)

- buffer (Sol) — manager review: sound. · scan (Sol) — sound. · escape (Neon) — sound, small fix queued above; Astra's part review then caught a secure-mode apostrophe divergence (manager-verified) — fix queued above. · references (Neon) — sound. · utf8 (Neon) — table fixes verified 2026-11-27, then Sol's part review caught a U+FFFD grouping divergence in `utf8_check` (manager-verified) — part reopened, fix queued above.
