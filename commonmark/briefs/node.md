# Brief: part 5 — `node` (module `cm_node`)

**Writer:** Sol (OpenAI). **Reviewer:** Astra (OpenAI). **Seam tests:** Neon, in `tests/seams/node/`, written from the contract alone.
**Repo:** `shaglama/workshop-npk`, branch `work/commonmark`, folder `commonmark/`. **Compiler pin:** `3a45b7c4`.
**You may write only:** the folders in `commonmark/assign/sol.txt` that this brief names — for this part, `src/node/`.

## Read first

- `commonmark/INTERFACES.md` — the frozen contract: the shared conventions, the failure section, and Part 5. You code to it exactly. Part 5 is the contract's longest part; the iterator rules and the surgery rules are stated there in full and are part of the spec of this part, not commentary.
- `commonmark/PLAN.md` — where this part sits: everything above it (both parsers, the renderer, the driver) holds nodes only through this part's calls.
- cmark 0.31.2: `src/node.h` and `src/node.c` — the node structure, the tree surgery (`cmark_node_append_child`, `_prepend_child`, `_insert_before`, `_insert_after`, `_unlink`, `_replace`), the iterator (`src/iterator.c`), and `cmark_consolidate_text_nodes` in `src/inlines.c`. The port's store-and-index design replaces cmark's pointers; the *behaviour* of each operation is cmark's.
- The lab's `lab/context/known-issues.md` (in the outside-exchange repo) — open compiler faults to recognise, not rediscover.

## The job

Implement `cm_node` in `src/node/`: the `Document` and its node store, the node accessors and setters, the tree surgery calls, `consolidate_text_nodes`, and the event iterator — every signature in Part 5, exactly as written, with its stated failure mark (`never fails` or `Result`).

Points the contract settles that are easy to get subtly wrong:

- **Nodes are never removed from the store.** Unlinking detaches a node from its parent and siblings; the node stays in the store, unreachable from the root, and its `NodeRef` stays valid. Do not compact, reuse slots, or free.
- **Reading is split.** `node_info` hands out plain data by copy (including the link fields, which are a read view). Strings never travel inside a returned struct: each is reached through its own getter (a clone, hence `Result`) and setter (takes the new string by `move`).
- **`doc_set_refs` is `never fails`** and takes the `RefMap` by `move` — the one step that installs the parser's map into the document (called by `parser_finish` in `cm_blocks`). `doc_ref_lookup` answers from the document's own map.
- **The iterator is plain state** — it holds no borrow; the document is passed to each `iter_next`. Event order and the walk rule are cmark's: a walk may add children to the node whose `Enter` it has just been given and edit that node's own fields; it may not unlink, replace, add siblings, or touch any other node's children. `consolidate_text_nodes` is the contract's one named exception: it traverses child lists directly and unlinks merged nodes, outside any walk.
- `node_new` appends an unattached, literal-empty node of the given kind; the surgery calls detach a child from any previous siblings first, as cmark's do.

## Checks

Include in `src/node/checks/` a small harness program that exercises the whole surface: build a small tree by hand (document, heading, paragraph, text, link, list with items, code block), read it back through `node_info` and the string getters, set and re-read every payload kind (list, heading, code fence, custom, link, sourcepos, flags), run each surgery call and verify the resulting link structure through `node_info`, walk the tree with the iterator and record the event sequence against a hand-written expectation (including `Exit` events and the `Done` end), merge adjacent text nodes with `consolidate_text_nodes` and verify both the merged literal and that the detached node is still in the store, and install a `RefMap` with `doc_set_refs` and answer a `doc_ref_lookup` through the document. Built and run at **-O0 and -O2**, with a log recording the commands, the compiler commit, npkc's sha256, and the outputs. Expected results are worked by hand from the contract and cmark's behaviour — never from the part's output copied back.

## Rules that apply to every part

- If the contract cannot be implemented as written, **stop and say so** in a note in your folder; do not deviate silently. Contract changes go through the manager as a pull request.
- If something looks like a compiler fault: check `known-issues.md` first, cut it to the smallest program that shows it, and record it in a `notes.md` in your folder (program, compiler commit, expected vs actual) — then work around it and keep going. A crash, output that differs between -O0 and -O2, or output that changes from run to run is recorded as a possible compiler fault **before** you debug the port around it.
- Credit: a header line in the part's main file — "Written by Sol (OpenAI)."
- End in a commit on `work/commonmark` naming the part, with its checks.
