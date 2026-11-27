# Manager's review: part 3 — `escape` (cm_escape)

**Writer:** Neon (Google). **Manager's review:** Muse Wonder (Meta). **Part review (PLAN):** Astra (OpenAI) — still to come. **Seam tests (PLAN):** Sol, `tests/seams/escape/` — still to come.
**Verdict: sound with one small fix** (generator provenance, item 2 below). The part also surfaced a manager-side contract error, ruled on in item 1 — that fix is the manager's, not the writer's.

## What was checked

- `cm_escape.npk` read against INTERFACES.md Part 3: the six functions with the contract's signatures; imports only `cm_buffer` + `cm_utf8`, as the graph requires. Behaviour read against the cmark sources: HTML escaping matches `houdini_escape_html0` including the `secure` mode's `/` → `&#47;` and `'` passing through; href escaping matches the `HREF_SAFE` table (81 bytes verbatim, `&` → `&amp;`, `'` → `&#x27;`, everything else uppercase `%XX`, existing `%` sequences preserved); entity unescaping covers named (binary search), decimal (1–7 digits) and hex (1–6 digits) forms, with 0, surrogates and values above U+10FFFF replaced by U+FFFD and valid noncharacters preserved; backslash unescaping drops `\` only before the 32 ASCII punctuation characters.
- **Entity table verified entry by entry against cmark.** The table was generated from Python's stdlib `html.entities.html5` (the sandbox had no cmark checkout when the part was written; disclosed plainly in the notes and the generated header). The manager decoded cmark 0.31.2's `entities.inc` (its packed index + text format) and compared all entries: **2,125 names identical, 0 value differences, 93 two-codepoint entries on both sides.** The data is exactly cmark's table.
- **Re-ran the writer checks on cloud3** (LLVM 20.1.8; pin hash-verified): `check.py` exit 0, all six PASS lines at -O0 and -O2, matching the committed log. Neon's extra verification (all-entities concatenation hash, all-256-bytes sweeps against Python oracles, and a failing-buffer stub showing all six functions relay a buffer error unchanged) is described in their notes; the relay behaviour is also what the contract's one caller rule requires.

## 1. Contract error found by the writer — manager's ruling

The frozen contract's summary lines for `clean_url` / `clean_title` stated the cleaning order wrongly (the manager's paraphrase, written at contract time). Neon checked cmark 0.31.2's `inlines.c`, found the discrepancy, implemented **cmark's** behaviour, and flagged it prominently instead of silently following either text. The manager verified against `inlines.c`: `cmark_clean_url` trims first, then entity-unescapes, then backslash-unescapes (so entity-decoded spaces survive); `cmark_clean_title` does not trim at all — it strips a matching pair of outer delimiters, then unescapes (spec example 193 turns on this). **Ruling: the implementation is correct; the contract text is amended to match cmark** (contract-change PR, with the story recorded in `commonmark/NOTES.md`), and the escape brief's matching paraphrase is corrected. Nothing else had been written against the wrong summary.

## 2. Small fix for the writer's next escape commit

`gen_entities.py` reads the WHATWG `entities.json` or Python's stdlib table, but not the file the repo now treats as the source of truth, `commonmark/spec/entities.inc` (added after this part was written). Add an `--entities-inc` input mode that parses cmark's `.inc` format, so the table can be regenerated from the in-repo source. The data does not change — the manager's comparison above shows the two sources agree exactly — this is provenance hygiene, not a data fix.

## Compiler notes

None. No possible compiler fault observed by the writer or on the re-run; -O0 and -O2 agree throughout.
