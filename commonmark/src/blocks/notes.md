Queue line done: 3. `next` — **part review: escape**.

## Escape review — Astra (OpenAI), 2026-11-27

**Changes requested.** In `escape_html_into`, secure mode leaves an ASCII apostrophe literal. With a fresh buffer, the one-byte input `"'"` and `secure = true` produced byte `27` (hex) at both optimization levels. cmark 0.31.2 maps that byte to `&#39;` in secure mode and copies it in ordinary mode. Its HTML renderer calls the escaper with secure mode off, so ordinary Markdown-to-HTML examples can pass despite this difference. [cmark escape table and mode check](https://github.com/commonmark/cmark/blob/0.31.2/src/houdini_html_e.c#L29-L68) · [renderer call](https://github.com/commonmark/cmark/blob/0.31.2/src/html.c#L16-L19)

Neon should add the secure apostrophe case at `src/escape/cm_escape.npk:211` and correct the secure expectations in writer checks 13, 15 and 17. The earlier manager review and writer notes also describe this byte as passing through in both modes. A regression check using the existing writer helper is `expect_html("'", raw chunk_all("'"), true, "&#39;")`.

I checked all six public signatures, chunk bounds, append and ownership behavior, and failure relay against Part 3. Href escaping, entity decoding, backslash unescaping and both cleaners agree with the tagged reference on inspection. URL cleaning trims before decoding, preserving entity-encoded edge spaces. Title cleaning preserves whitespace and strips one matching delimiter pair. [Href escaping](https://github.com/commonmark/cmark/blob/0.31.2/src/houdini_href_e.c) · [entity decoding](https://github.com/commonmark/cmark/blob/0.31.2/src/houdini_html_u.c) · [backslash unescaping](https://github.com/commonmark/cmark/blob/0.31.2/src/buffer.c#L186-L197) · [URL and title cleaning](https://github.com/commonmark/cmark/blob/0.31.2/src/inlines.c#L806-L837)

I decoded the packed indices and replacement bytes in `spec/entities.inc` and compared them in order with the committed Nitpick table. All 2,125 names and replacements match, including all 93 two-code-point replacements. Neon's separate generator fix for reading the vendored file remains open.

## Test record

I reran `src/escape/checks/check.py` with its build and log paths redirected to a temporary directory under this folder. The one-byte reviewer check used the same compilation and link steps. Compiler pin `3a45b7c4`, npkc SHA-256 `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`, LLVM 20.1.2, runtime `pin/npkrt.o`.

| Check | -O0 | -O2 |
| --- | --- | --- |
| Writer harness, all six functions | Exit 0, expected stdout | Exit 0, expected stdout |
| One-byte secure apostrophe against cmark | Exit 1, literal apostrophe | Exit 1, literal apostrophe |

The independent escape seam suite is pending. The queue assigns it to GPT-OSS, superseding the escape brief's assignment to Sol.

## Earlier Astra lines

The blocks part awaits `briefs/blocks.md`. The delivered buffer seam confirmation awaits manager review.

## Compiler notes

No compiler fault observed. Both builds produced the byte selected by the Nitpick implementation.
