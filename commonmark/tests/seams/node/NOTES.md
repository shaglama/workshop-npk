Queue line done: 1. `next` — **seam tests: node** (tests/seams/node/), from INTERFACES.md Part 5 alone.

Written by Sonnet (Claude Sonnet 5.5, Anthropic) from INTERFACES.md Part 5 (with Parts 1 and 6 for `Buffer` and the `RefMap` a `Document` holds) and from cmark 0.31.2's tree and iterator behaviour. The part's source, its notes and its checks were not read.

Run from the repository root: `python3 commonmark/tests/seams/node/check.py`. It builds and runs `node_seam.npk` at `-O0` and `-O2` with `pin/npkc` (3a45b7c4), `pin/npkrt.o` and `pin/lib`. [check.log](check.log) records the compiler sha256 and every command. Result: 12 groups, all pass at both levels. No findings against the part.

Groups (exit code 11–22 names the failing one):

- 11 `doc_new`, `doc_root` (none on an empty document), `node_new` for all 21 kinds, unattached links, empty strings everywhere.
- 12 `node_append_child` / `node_prepend_child`: every link field after each step; appending a child that already has siblings detaches it first (first, middle, last, only child; same parent re-append).
- 13 `node_insert_before` / `node_insert_after` (first, middle, last), `node_unlink` (detached node stays readable, carries its subtree, can be re-attached), `node_replace` (first, middle, last, only child, subtree either side).
- 14 strings: literal, code info, link url/title, custom on_enter/on_exit — replace, empty, 5,000 bytes, embedded NUL, getters clone (read twice), setters on one node leave others alone, survival across store growth.
- 15 plain setters: list (both `ListType`s, all fields), code fence, heading, html block type, source position, the eight flag combinations; none disturb other data or links.
- 16 iterator: document order, subtree bounds, raw event sequence, two independent iterators, Done stays Done, surgery before a walk.
- 17 the walk's one permitted mutation: children added to the node just entered are themselves visited; its own fields are edited mid-walk.
- 18 `consolidate_text_nodes`: runs of 2 and 3, empty literals, breaks between runs, subtree-only consolidation, second pass is a no-op, 100 texts to one, merged nodes unlinked.
- 19 `doc_ref_lookup` through `doc_set_refs` (maps built with `refmap_add`): not found on a fresh document, folded and whitespace-collapsed labels, chunk of a larger base, replacing the map.
- 20 growth: 3,000 nodes, early `NodeRef`s still valid, walk counts, a 2,000-deep chain.
- 21 root: the first `DocumentNode` made becomes the root (see below).
- 22 prepend into an empty parent.

The suite can fail: a mutant with one wrong consolidation expectation exits 18.

## Readings of the contract the manager may want to pin

- **Iterator leaves.** The contract does not say which kinds get an `Exit`. I follow cmark: a leaf kind (Text, Softbreak, Linebreak, Code, HtmlInline, CodeBlock, HtmlBlock, ThematicBreak) gets an `Enter` only; every other kind, even an empty one, gets `Enter` then `Exit`. (I first expected an Exit for every node, from memory; the part was right.) The tests use Text, Softbreak and Paragraph/Emph/Strong/Document/BlockQuote only.
- **Nesting.** cmark's append/insert refuse a child the parent cannot hold (a Text under a BlockQuote or the Document); the part does the same (an append of Text to a BlockQuote leaves the quote childless). The contract says only "never fails" and names no such rule. The tests build only nestings cmark allows. Worth a line in the contract.
- **What sets the root.** The contract says an empty document has no root and `doc_root` reads it, not what sets it. Group 21 reads it as: the first `DocumentNode` created by `node_new`. Passes.
- **`NodeRef` is not visible to importers.** The contract names the type `NodeRef = int64`; `use "…/cm_node.npk".*` gives no type `NodeRef` (error NITPICK-TYPE-001), so the tests spell it `int64` (as the contract says it is). `NO_NODE` is visible and equals -1 (group 11). Not a compiler fault; the part does not export the alias, or aliases do not import. The manager decides which.
- **Iterator after Done.** Tested that a further `iter_next` still gives Done (cmark's behaviour); the contract does not say.
- Merged text nodes' end positions are not tested (cmark's `cmark_consolidate_text_nodes` and the contract say nothing firm).

## Compiler notes

No possible compiler faults observed; -O0 and -O2 agree on every group. Language points hit while writing, none a fault: a call to a `never fails` function as a statement needs `drop`; `failsafe` must name `LimitViolated` here (D-179) because the compiler reports it can reach `failsafe` through the part's calls; `in` is a keyword.

Queue: next line is 2, **seam tests: scan**; not started (one line at a time).
