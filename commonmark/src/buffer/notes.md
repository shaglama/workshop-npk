Queue line done: 2. `next` — **part review: utf8**.

Queue line blocked: 1. `blocked: manager review` — **node part** (src/node/).

# UTF-8 part review — Sol (OpenAI), 2026-11-27

**Changes requested for `utf8_check`.** This review is recorded here because
`assign/sol.txt` includes the buffer folder and the manager owns
`reviews/utf8.md`.

## Finding

The shared text convention calls for cmark's repair behavior under
`validate_utf8`. The port's `valid_utf8_len` implements Unicode
maximal-subpart grouping. The tagged cmark validator checks nominal width
against the remaining bytes first. For a complete nominal sequence, it checks
continuations before applying scalar restrictions. This changes how many bytes
one U+FFFD consumes. [Interface contract](../../INTERFACES.md)
[Port validator](../utf8/cm_utf8.npk#L138)
[cmark 0.31.2 validator](https://raw.githubusercontent.com/commonmark/cmark/0.31.2/src/utf8.c)

The following differences were reproduced against the tagged C functions with
a byte-output adapter. Each output was identical across `-O0` and `-O2`.

| Input bytes | cmark 0.31.2 | Nitpick port |
|---|---|---|
| `C0 AF` | 1 × U+FFFD | 2 × U+FFFD |
| `ED A0 80` | 1 × U+FFFD | 3 × U+FFFD |
| `F4 90 80 80` or `F5 80 80 80` | 1 × U+FFFD | 4 × U+FFFD |
| `E2 41` at the end of a chunk | U+FFFD | U+FFFD, then `A` |
| `E0 80 41` | U+FFFD, then `A` | 2 × U+FFFD, then `A` |

In a copy of the writer harness, change the `expect_check(ov2, raw chunk_all(ov2), fffd2)`
expectation from `fffd2` to `fffd`. The harness exits 84 at both levels.
The surrogate and above-maximum cases in the harness likewise expect the port's
current output. [Writer harness](../utf8/checks/check_utf8.npk#L264)

Match the tagged validator's byte consumption in `utf8_check` and update its
writer expectations. Include a short nominal sequence at a nonzero chunk
offset to exercise the chunk boundary. Keep `utf8_iterate`'s contractually
specified one-byte advance on invalid input.

## Checks

- All six groups in the supplied `check_utf8.npk` harness passed with the real
  `cm_buffer` at `-O0` and `-O2` using the IR, opt, llc, and static link
  commands from the writer log. The six direct
  signatures and failure marks match Part 2, and the fallible calls relay
  buffer errors unchanged. [Writer log](../utf8/checks/check.log)
- Compared ten byte ranges with the tagged C implementations at both levels.
  Repair differed on six inputs and case folding matched on all ten. Both
  the Nitpick probe and C oracle exited 0 at both levels.
- Table regeneration was byte-identical on Python with Unicode 15.0.0 data.
  A separate comparison matched all 1,559 non-ASCII folds, including 104
  expansions, to `spec/case_fold.inc`, and all 8,580 non-ASCII punctuation and
  symbol code points to the tagged C predicate.
  [cmark 0.31.2 `src/utf8.c`](https://raw.githubusercontent.com/commonmark/cmark/0.31.2/src/utf8.c)
- Compiler pin `3a45b7c4`, LLVM 20.1.2.
  `npkc` SHA-256 `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`.
  `npkrt.o` SHA-256 `c8e5033ad17c70f838d567157738a6cc046af0ca3140ad92259fa71f0e747b4e`.

## Compiler notes

Checked the lab's known issues. No new compiler fault observed. The existing
`"\xFF"` documentation example exited 2 at both `-O0` and `-O2`.
[UTF-8 notes](../utf8/notes.md)

# Buffer — Sol (OpenAI)

Part 1 implementation and writer checks are complete. Every function in the
current frozen contract is implemented in `cm_buffer.npk`, using the approved
constructor name `buffer_create`. The previous reserved-name blocker is resolved;
the `buffer_new` negative reproduction and blocker log remain in `checks/`
as a documented negative check.

## Implementation

Import with `use "<relative path>/src/buffer/cm_buffer.npk".*;`.
The module imports no other part or library. `Buffer` owns a managed Nitpick
`buffer` cell and a used-byte count, with hidden fields. Appends grow capacity
geometrically; clear retains that cell and resets its used count. No raw
allocation, manual free, error constants, main, or failsafe occur in the module.

`buffer_detach` consumes its owner and returns an owned string. The pinned
runtime has no buffer-to-owned-string transfer, so detach copies the used bytes
with the never-failing `string_concat` floor constructor before the old cell
drops. This is linear in the content length and may trap on allocation failure,
as allowed for a `never fails` function. No borrowed view leaves the call.

`chunk_to_string` uses the fallible owned-copy `string_slice` and relays its
failure unchanged. `buffer_puts` similarly relays `buffer_put` without remapping
errors. All public success types and failure marks follow Part 1 exactly.
Chunk positions and lengths remain byte counts, including arbitrary binary data.
`chunk_trim` strips only space and tab, as the port contract specifies.

Porting references read: cmark 0.31.2's
[buffer.c](https://github.com/commonmark/cmark/blob/0.31.2/src/buffer.c),
[buffer.h](https://github.com/commonmark/cmark/blob/0.31.2/src/buffer.h), and
[chunk.h](https://github.com/commonmark/cmark/blob/0.31.2/src/chunk.h).
The existing project licence notices remain in `commonmark/LICENSES/COPYING`.

## Checks

From the repository root:

```sh
python3 commonmark/src/buffer/checks/check.py
```

PASS at both `-O0` and `-O2`: npkc emission, opt, llc, static link with the
supplied `pin/npkrt.o`, then execution with identical expected output and exit 0.
The harness imports the supplied `pin/lib/nio.npk` for reporting. The script
removes generated IR, objects and executables after the checks. Exact commands,
statuses, outputs, LLVM versions, compiler commit `3a45b7c4` and npkc SHA-256
are in `checks/buffer.log`.

The writer harness `checks/buffer_check.npk` exercises every API function:
empty creation/detach; whole and offset chunks; owned copies that outlive a local
base; equality, inequality and length mismatch; empty and all-space/tab chunks;
preserving CR/LF; mixed appends; moving a buffer across a call; 20,000 one-byte
appends; whole-string and nonzero-offset chunk appends through growth; every
binary byte value including NUL and invalid UTF-8; clear on empty and grown
buffers; repeated reuse; and detach immediately after clear. Expected values
are hand-computed byte ranges and formulas, with cmark's append/clear semantics.
No expected value was copied from the port's output.

These are the brief's writer checks. Astra's independent seam tests in
`tests/seams/buffer/` are not supplied in this copy; Neon review remains external.

## Compiler notes

No possible compiler fault observed. Checked
`/home/outside/jobs/lab/context/known-issues.md` before implementation.
Both optimization levels compile and run without diagnostics or divergence.

The earlier `buffer_new` collision was a documented builtin-name restriction,
not a compiler fault; the current approved `buffer_create` contract fixes it.

## Handoff

All writes are confined to `commonmark/src/buffer/`, permitted by
`commonmark/assign/sol.txt`. This work stops after Part 1; scan and node have
not been started. A commit on `work/commonmark` is unavailable in this copy:
`.git` is an empty read-only directory, so Git reports that this is not a
repository. No Git metadata or files outside the assignment were written.
