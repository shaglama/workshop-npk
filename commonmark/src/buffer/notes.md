# Buffer — Sol (OpenAI)

Part 1 implementation and writer checks are complete. Every function in the
current frozen contract is implemented in `cm_buffer.npk`, using the approved
constructor name `buffer_create`. The previous reserved-name blocker is resolved;
the obsolete `buffer_new` negative reproduction and blocker log were removed.

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
