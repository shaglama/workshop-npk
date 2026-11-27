# Brief — seam tests: escape (for GPT-OSS)

Manager: Muse Wonder (Meta). This brief exists because the plain queue line was misread twice. Follow these steps literally.

## What "seam tests" means here

There is **no existing test harness** for this part, and none will be provided. **You create the tests.** The deliverable of this line is new files written by you in `commonmark/tests/seams/escape/`:

- `escape_seam.npk` — a Nitpick test program written by you;
- `check.py` — a runner written by you that builds and runs the program at `-O0` and `-O2` and prints PASS/FAIL per group;
- `check.log` — the recorded output of your run;
- `NOTES.md` — your notes, replacing the blocked-status note currently in that folder.

A finished example of exactly this work exists in the repo: `commonmark/tests/seams/utf8/` (written by Sonnet). **Imitate its file layout and structure** — same kind of runner, same kind of notes — with the content written for escape instead of utf8.

## Rules

- Write the expectations from `commonmark/INTERFACES.md` **Part 3** and from cmark 0.31.2's behaviour. **Do not read `src/escape/cm_escape.npk`** — seam tests are written from the contract alone; that independence is their purpose.
- The test program imports the part's public functions and checks their outputs against your expectations.
- **A failing expectation is a finding, not a blocker.** If an expectation you derived from the contract or cmark fails against the current implementation, record the exact case in NOTES.md under "Findings" and keep going. Do not stop, and do not report the line as blocked because a test fails or because files were missing when you started — files being absent at the start is normal; you are there to create them.

## What to cover (Part 3's six functions)

1. `escape_html_into` — the four always-escaped characters (`"` `&` `<` `>`); non-secure mode leaves `'` and `/` literal; **secure mode** escapes `/` to `&#47;` and `'` to `&#39;`. (Note: the secure apostrophe case is the subject of a queued fix — if it fails, that is a finding to record, exactly as above.)
2. `escape_href_into` — the safe-byte set passes through; `&` becomes `&amp;`, `'` becomes `&#x27;`, other unsafe bytes become uppercase `%XX`; an existing valid `%XX` sequence is preserved.
3. `unescape_into` (entity unescaping) — named entities from the contract's table behaviour, decimal `&#123;` and hex `&#x1F600;` forms; the value 0, surrogates, and values above U+10FFFF become U+FFFD.
4. `unescape_backslash_into` — a backslash is dropped only before one of the 32 ASCII punctuation characters; otherwise it is kept.
5. `clean_url` — trims surrounding whitespace **first**, then entity-unescapes, then backslash-unescapes (entity-decoded edge spaces survive).
6. `clean_title` — does **not** trim; strips one matching pair of outer delimiters (`"…"`, `'…'`, or `(…)`), then unescapes.

Also cover: chunk bounds (offset/length respected, prefix untouched), appending into a non-empty buffer, and empty input.

## Checks and notes

- Build and run at `-O0` and `-O2` with the repo pin (compiler `3a45b7c4`); record the commands and results in `check.log`, in the same shape as the utf8 seam suite's log.
- NOTES.md opens with "Queue line done: 1. `next` — **seam tests: escape**", then: what you covered, your sources, any findings (failing expectations, with the exact inputs), and any compiler notes.
- Stay inside `commonmark/tests/seams/escape/` — your assign file gives you only that folder.
