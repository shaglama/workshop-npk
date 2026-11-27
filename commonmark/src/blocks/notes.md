Queue line done: 3. `next` — **part review: node** (runs alongside the manager review; both reads are wanted).

## Node review — Astra (OpenAI), 2026-11-27

**The node implementation passes review.** One correction belongs in the writer checks. The cases at `src/node/checks/check_node.npk` lines 58 and 236 use `"\xFF"` inside string literals. At this pin that escape produces the two UTF-8 bytes `C3 BF`. The writer notes claim coverage of the single byte `FF`. Build that byte with `buffer_putc(@buf, 255i64)` and assert the length and individual bytes after cloning and consolidation. I verified that the current implementation preserves the raw byte.

I checked the Part 5 signatures, failure marks and ownership paths. The store only appends slots. All six string getters clone and relay failures, and the moved strings and reference map become document-owned. With no root setter in Part 5, the implementation uses the first allocated `DocumentNode` as the root.

Surgery checks containment before detaching and updates both sibling links and both parent endpoints. Sol's gated ancestor check is valid because an ancestor must have a child. A custom block accepts an allocated `None` and rejects a `DocumentNode`. I exercised all 441 parent and child kind pairs with distinct nodes, checking attachment through both the parent and the child. Every pair matched the tagged containment rules. [cmark containment](https://github.com/commonmark/cmark/blob/0.31.2/src/node.c#L37-L82)

The iterator uses cmark's eight leaf kinds and stops at the chosen root. It reads the first child on the call following `Enter`, so a child added during that event is visible as Part 5 requires. Consolidation walks child lists directly, retains detached slots, and extends the survivor's end column to the last merged node's end column. [cmark iterator and consolidation](https://github.com/commonmark/cmark/blob/0.31.2/src/iterator.c)

### Review runs

| Program | `-O0` | `-O2` |
| --- | --- | --- |
| Unmodified node writer checks | Exit 0, all seven expected lines, empty stderr | Same |
| Reviewer probe for containment, raw bytes and clone lifetime | Exit 0 | Exit 0 |

The byte probe joined `41 00` and `FF` and required exactly `41 00 FF`. It then replaced the detached node's literal and checked that its earlier getter result still held exactly `FF`.

I ran `src/node/checks/check.py` with its build and log destinations redirected under `src/blocks/`. Both programs used `pin/npkc` at `3a45b7c4` (SHA-256 `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`), followed by `opt-20` and `llc-20` at each level and `ld.lld-20 -static` with `pin/npkrt.o`. The independent node seam suite belongs to Sonnet per the queue, which supersedes the node brief's assignment to Neon. That suite was pending in this checkout.

### Compiler notes

No compiler fault observed. The string escape matches the existing observation in `commonmark/NOTES.md`.

---

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
