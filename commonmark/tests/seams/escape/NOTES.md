Queue line done: 2. `next` — **seam tests: escape — REDO** (tests/seams/escape/), from INTERFACES.md Part 3 alone. The first delivery was removed by the manager: it was a verbatim copy of the part's writer harness (`src/escape/checks/check_escape.npk`), which defeats the purpose of a seam suite and cannot even build in the seam folder's layout. Write the tests yourself from the contract; do not copy or adapt the writer's checks. The folder starts empty; you write the tests, the runner and the notes.

Sol's preceding node line is blocked on manager review. The seam brief refers to the earlier queue number and uses two different unescape names. This delivery follows the current queue and the `unescape_entities_into` and `unescape_backslashes_into` names in Part 3.

Run `python3 commonmark/tests/seams/escape/check.py` from the repository root. Both builds succeeded with `npkc` at `3a45b7c4`, the pinned runtime and library, and LLVM 20. Each run reported 34 passes and one failure and exited 1. The outputs matched byte for byte at `-O0` and `-O2`. [Commands, compiler SHA-256 and results](check.log)

## Coverage and sources

- HTML and href escaping cover secure and nonsecure HTML output, reserved href characters, existing percent escapes, uppercase byte escapes, and NUL and `FF` bytes. [Part 3](../../../INTERFACES.md#part-3--escape-module-cm_escape) · [cmark HTML escaping](https://github.com/commonmark/cmark/blob/0.31.2/src/houdini_html_e.c) · [cmark href escaping](https://github.com/commonmark/cmark/blob/0.31.2/src/houdini_href_e.c)
- Entity and backslash decoding cover multi-scalar entities, decimal and hex digit limits, malformed references, replacement characters, one-pass decoding, and all 32 ASCII punctuation characters. [CommonMark 0.31.2 examples](../../../spec/spec.txt) · [cmark entity unescaping](https://github.com/commonmark/cmark/blob/0.31.2/src/houdini_html_u.c)
- URL and title cleaning cover the operation order, raw and decoded whitespace, all three title delimiter pairs, and the handoff from a cleaned URL to href escaping. The suite uses bounded chunks for all six calls, checks empty interior chunks and verifies that append operations preserve the prefilled buffer. [Part 3](../../../INTERFACES.md#part-3--escape-module-cm_escape) · [cmark URL and title cleaning](https://github.com/commonmark/cmark/blob/0.31.2/src/inlines.c#L806-L838) · [cmark ASCII whitespace and punctuation](https://github.com/commonmark/cmark/blob/0.31.2/src/cmark_ctype.c)

## Findings

`escape_html_into` with base `"'"`, chunk `{off: 0, len: 1}` and `secure: true` appends `'`. cmark 0.31.2 appends `&#39;`. With the seam's prefilled buffer, the expected result is `kept<&|'/:&#39;` and the actual result is `kept<&|'/:'` at both optimization levels. This reproduces Neon's queued escape apostrophe fix. [cmark HTML escaping](https://github.com/commonmark/cmark/blob/0.31.2/src/houdini_html_e.c#L35-L73) · [Work queue](../../../QUEUE.md#neon-google)

## Compiler notes

No possible compiler faults observed.
