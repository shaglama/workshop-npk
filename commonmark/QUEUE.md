# Work queue — CommonMark port

Manager-owned (Muse Wonder, Meta), like `PLAN.md`, `INTERFACES.md` and `assign/`. This file is the **order of work** for the whole project. The assign files say where each worker may write; the briefs say how a part is done; this queue says **what happens next**.

## The rule

Take the **first line with your name on it** whose state is `next` or `ready`. Work only on that line until it is done or blocked. If your top line is `blocked`, say so in your notes and take the next unblocked line with your name.

- **Fixes and reviews of parts already written rank above new parts.** A part with an open fix list is not finished, however good the new-part work looks.
- One line at a time. Do not start a second line before the first is handed back.
- When you finish a line, say so at the top of your part notes ("Queue line done: <the line>"), so the manager can strike it and promote the next one.
- The manager updates this file after every review. If the queue and a brief disagree, the queue wins on order, the brief wins on content — and flag the disagreement in your notes.

States: `next` (first unblocked line for that worker) · `ready` (can start when reached) · `blocked: <what it waits on>` · `done` (struck by the manager after review).

## Queue

### Neon (Google)

1. `next` — **escape provenance fix** per `reviews/escape.md` item 2: add the `--entities-inc` input mode to `gen_entities.py`, reading `spec/entities.inc`. (src/escape/)
2. `blocked: brief` — **html part** (src/html/, tests/seams for blocks/inlines as scheduled).

### Sol (OpenAI)

1. `next` — **node part** (src/node/). Brief: `briefs/node.md`.
2. `ready` — **part review: utf8**.

### Astra (OpenAI)

1. `blocked: brief` — **blocks part** (src/blocks/). Brief: `briefs/blocks.md` (manager to post). Note the scan seam from `reviews/scan.md`: scanners return match lengths, not cmark's classification codes — derive heading level / block type from the matched text.
2. `next` — **buffer seam confirmation pass** (tests/seams/buffer/). The seam tests in that folder were delivered 2026-11-27 under Astra's name but were written by Sol 6.2 (see the manager note below). Read them against INTERFACES.md Part 1 alone, run them, and add cases for anything the part's own author would miss; say what you added at the top of the folder's NOTES.md.
3. `ready` — **part review: escape**.

### Carbon (Google)

1. `blocked: brief` — **inlines part** (src/inlines/). Brief: `briefs/inlines.md` (manager to post). Note the scan seam from `reviews/scan.md`, as for blocks.
2. `next` — **seam tests: references** (tests/seams/references/), from INTERFACES.md Part 6 alone.
3. `ready` — **part review: scan**.

### Sonnet

1. `next` — **seam tests: utf8** (tests/seams/utf8/), from INTERFACES.md Part 2 alone.
2. `ready` — **seam tests: node** (tests/seams/node/), from INTERFACES.md Part 5 alone.

### GPT-OSS

1. `next` — **seam tests: scan** (tests/seams/scan/), from INTERFACES.md Part 4 alone. Note the seam from `reviews/scan.md`: scanners return match lengths, not cmark's classification codes.
2. `ready` — **seam tests: escape** (tests/seams/escape/), from INTERFACES.md Part 3 alone.

### Manager (Muse)

- Briefs: node posted (`briefs/node.md`). Still to post: blocks, inlines, html (in that order).
- Driver part last, after html is reviewed; then the step PRs to `main` per step, with the credits table in `commonmark/README.md`.
- 2026-11-27: **Sonnet** (Claude Sonnet 5.5, Anthropic) and **GPT-OSS** (GPT-OSS 120B, OpenAI) joined via management's launcher on the agy Claude+GPT group. Their sessions stop by themselves at the group's 75 % line, so their queue lines are kept short. Reassignments to seat them: utf8 seam tests Carbon → Sonnet; node seam tests Neon → Sonnet; scan seam tests Astra → GPT-OSS; escape seam tests Sol → GPT-OSS.
- 2026-11-27: **launcher fault, fixed by management.** Until now the launcher started Astra without naming its model, so the workshop's Astra sessions actually ran Sol 6.2. The buffer seam tests delivered under Astra's name were therefore written by Sol 6.2 — the buffer part's own author — and the credits will say so; the real Astra (gpt-6.2-astra from now on) has the confirmation-pass line above. Management's note scopes this to the workshop launcher.
- 2026-11-27: **Sol's launcher entry was likewise hardcoded to 6.1** (Randy, confirmed and fixed the same day): the workshop's Sol sessions so far — buffer, scan, and the node part delivered today — ran Sol 6.1; Sol is 6.2 from now on. The manager reviews of buffer and scan stand as written: they rest on the manager's own re-runs against the contract and cmark, not on who held the pen.

## Done (for the record)

- buffer (Sol) — manager review: sound. · scan (Sol) — sound. · escape (Neon) — sound, small fix queued above. · references (Neon) — sound. · utf8 (Neon) — sound with fixes; fixes verified 2026-11-27 (see the addendum in `reviews/utf8.md`) — part closed.
