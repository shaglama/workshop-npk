Queue line done: 1. `next` — **node part** (src/node/). Brief: `briefs/node.md`.

# Node — Sol (OpenAI)

Part 5 implementation and the brief's writer checks are complete. All writes
are under `commonmark/src/node/`, as permitted by `commonmark/assign/sol.txt`.
No other queue line was started.

## Implementation

`cm_node.npk` implements every Part 5 function and named payload shape. Import
it with `use "<relative path>/src/node/cm_node.npk".*;`. Its only part dependencies
are `cm_buffer` and `cm_refs`, as the frozen import graph requires.

`Document` owns a hidden `List<Node>`, its root index, and its `RefMap`. Slots
are append-only and never reused; unlinking and consolidation retain detached
nodes and their contents. All NodeRefs are `int64`, exactly the contract's
`NodeRef = int64` notation; Nitpick has no type-alias declaration. `NO_NODE` is
exported as -1. `doc_new` creates no nodes and has no root. Since the contract
has no root setter, the first `node_new(..., NodeKind.DocumentNode)` establishes
the root; later allocations leave that root unchanged.

`node_info` returns plain data by copy. Each string getter clones and relays
its allocation failure unchanged. Setters consume their string arguments;
`doc_set_refs` consumes and replaces the document's map without a fallible
operation, while `doc_ref_lookup` relays the reference service's result.
The library contains no main, failsafe, error constants, raw allocations, or
manual frees.

Surgery updates both sibling directions and both parent endpoints, detaching
existing attachments first. It checks cmark's containment and ancestor rules
before changing links. An incoming node with no children needs no ancestor
walk. A custom block accepts an allocated `None` node and rejects a
`DocumentNode`, as cmark does. Invalid containment or a root sibling operation is a
no-op (the contract returns NIL rather than cmark's boolean status); inserting
or replacing a node with itself is also a no-op. Accessors/setters otherwise
expect NodeRefs belonging to the supplied Document. `node_info` of an absent
reference returns None with absent links.

The iterator is plain state and reads the current node's children on the next
call, so children appended after Enter are visible, as the frozen walk rule
requires. It emits cmark's event sequence, including no Exit for leaf kinds,
and repeats Done with NO_NODE after completion. It does not traverse beyond
its chosen root. This deliberately defers successor selection until the next
call: cmark's C iterator precomputes it, which would miss newly added children.

Consolidation walks child lists directly, without the iterator or recursion.
It copies each adjacent Text run into one buffer, makes an owned string with
the never-failing floor constructor, then unlinks the merged nodes without
removing their store slots. As in cmark, it extends the first node's end_column
to the last merged node's end_column and retains the other source coordinates.
A Text selected as root also absorbs its following Text siblings, matching
cmark's special case. Allocation failure here may trap, as the contract permits
for never-failing functions. Work is linear in visited nodes and copied bytes.

Porting references read from the cmark 0.31.2 tag:
[node.c](https://raw.githubusercontent.com/commonmark/cmark/0.31.2/src/node.c),
[node.h](https://raw.githubusercontent.com/commonmark/cmark/0.31.2/src/node.h),
[iterator.c](https://raw.githubusercontent.com/commonmark/cmark/0.31.2/src/iterator.c),
and [inlines.c](https://raw.githubusercontent.com/commonmark/cmark/0.31.2/src/inlines.c).
Brief content correction for the manager: `cmark_consolidate_text_nodes` is in
`src/iterator.c`, rather than `src/inlines.c`. This does not affect queue order
or the frozen interfaces. Licence notices remain in `commonmark/LICENSES/COPYING`.

## Checks

Run from the repository root:

```sh
python3 commonmark/src/node/checks/check.py
```

PASS at both -O0 and -O2: npkc IR emission, opt, llc, static link against the
supplied `pin/npkrt.o`, and execution. Both runs exit 0, emit the same seven
expected lines, and have no stderr. `checks/check.log` records every command,
exit status, output, LLVM tool versions, compiler commit `3a45b7c4`, and hashes:

- npkc SHA-256: `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`
- npkrt.o SHA-256: `c8e5033ad17c70f838d567157738a6cc046af0ca3140ad92259fa71f0e747b4e`

`checks/check_node.npk` exercises every public call: empty creation; every kind;
root establishment; store growth; all plain payload fields and all string
getters/setters; independent clones surviving replacement; byte strings with
NUL and 0xFF; wide positions; every surgery with endpoint and sibling checks;
reparenting, adjacent replacement, idempotent unlink, invalid containment,
custom-block containment and cycle rejection; a hand-written full iterator trace with Exit and Done; subtree
and leaf walks; child creation on Enter; nested text consolidation, retained
detached nodes, end_column, idempotence, a Text root, and a 1024-node text run;
and moved reference maps, normalized sub-chunk lookup, map replacement, and
lookup clones surviving replacement. Expected results are hand-written from
the frozen contract and cmark behavior, never captured from the port's output.
The check functions return normally to exercise Document and node-store drops.

An initial harness run exited 61 because its URL expectation incorrectly
assumed clean_url removes angle brackets. Part 3 specifies whitespace trimming
and unescaping only. Corrected the input to ` a&amp;b ` with the independently
specified expectation `a&b`; no dependency implementation was changed.

These are the brief's writer checks. The brief names Neon for the independent
node seam suite, and the queue reassigns that suite to Sonnet. The independent
suite and Astra's review are pending handoff steps.

## Compiler notes

Checked `/home/outside/jobs/lab/context/known-issues.md` before implementation.
No possible compiler fault observed: no crash, optimization divergence, or
unstable output. Compiler diagnostics encountered during writing were ordinary
language rules (reserved `end`, cast precedence, and main/exit/relay restrictions)
and were corrected without a workaround or contract change.

## Handoff

Ready for the manager and reviewer; stopping after this queue line. A commit on
`work/commonmark` cannot be created in this supplied copy: `.git` is an empty,
read-only directory, and `git status` reports "not a git repository". No Git
metadata or files outside the assignment were written. The implementation,
source harness, reproducible runner, and passing log are all in this folder.
