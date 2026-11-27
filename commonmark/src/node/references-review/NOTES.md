Queue line done: 2. `next` — **part review: references**.

# Part 6 review — Sol (OpenAI)

The node part remains blocked on manager review. These review notes live in
Sol’s assigned `src/node/` handback folder.

The references implementation meets the reviewed Part 6 contract. All six
writer check groups passed at both `-O0` and `-O2`. The public entry points
follow the import and ownership rules, relay fallible calls, and keep the
first normalized definition while cleaning later duplicates. Lookups clone
the URL and title from the lent map. The parser adds consecutive definitions
from the start of the supplied chunk and reports their total byte count.
The label folding, trimming and whitespace collapse follow cmark.
[Part 6 contract](../../../INTERFACES.md#part-6--references-module-cm_refs)
[cmark reference store](https://github.com/commonmark/cmark/blob/0.31.2/src/references.c)
[cmark whitespace normalization](https://github.com/commonmark/cmark/blob/0.31.2/src/buffer.c#L166-L184)

## Findings

- **Strict sub-chunks can take quadratic copy work.** Each optional title
  scan copies the remaining suffix if the chunk ends before the base ends.
  This happens even when the next byte is `[` and there is no title. A
  strict sub-chunk containing `n` copies of `[x]: /u\n` therefore copies
  `4 * n * (n - 1)` bytes across those scans. Bounding the input once per
  parse would preserve chunk isolation and eliminate the repeated suffix
  copies. [Port source](../../references/cm_refs.npk#L558-L570)
- **The port follows the spec in three edge cases where cmark 0.31.2
  differs.** After a next-line title followed by junk, the port rewinds and
  clears the title, as CommonMark example 210 describes. The tagged cmark
  parser rewinds its position and retains the title chunk. The port also
  rejects a bare destination containing byte `0x01` and an angle destination
  containing a backslash followed by LF. The spec excludes both, while the
  C scanners allow them. The port results below were measured. The cmark
  results were inferred from the tagged C source.
  [CommonMark example 210](https://spec.commonmark.org/0.31.2/#example-210)
  [CommonMark link destinations](https://spec.commonmark.org/0.31.2/#link-destination)
  [cmark title rewind](https://github.com/commonmark/cmark/blob/0.31.2/src/inlines.c#L1379-L1405)
  [cmark destination scanners](https://github.com/commonmark/cmark/blob/0.31.2/src/inlines.c#L982-L1047)
- **The frozen lookup contract leaves cmark’s document-wide expansion
  budget out of Part 6.** The C block parser sets the budget from the input
  size, with a 100,000-byte minimum, and lookup charges the URL and title
  bytes against it. The port’s lent lookup has no budget state to update.
  This remains a fidelity decision for the parser integration.
  [cmark budget setup](https://github.com/commonmark/cmark/blob/0.31.2/src/blocks.c#L484-L497)
  [cmark lookup accounting](https://github.com/commonmark/cmark/blob/0.31.2/src/references.c#L104-L136)

## Verification

Compiler commit `3a45b7c4` and LLVM/LLD `20.1.2`.

- `pin/npkc` SHA-256 `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`
- `pin/npkrt.o` SHA-256 `c8e5033ad17c70f838d567157738a6cc046af0ca3140ad92259fa71f0e747b4e`

I ran the existing references writer harness with its build and log
directories redirected to temporary storage under `src/node/`. The
harness compiled `check_refs.npk` with `pin/npkc`, built with `opt-20` and
`llc-20` at each level, and linked with `ld.lld-20 -static` and
`pin/npkrt.o`. Both binaries exited 0 with empty stderr and printed the
same output. [Writer harness](../../references/checks/check.py)

```text
PASS: refmap_new & empty lookup
PASS: refmap_add & refmap_lookup normalisation
PASS: refmap_add cleaning, first-wins & clones
PASS: refmap hash growth & 1000-byte boundary
PASS: parse_ref_definition spec examples
PASS: parse_ref_definition edge cases & sub-chunks
ALL cm_refs CHECKS PASSED
```

A scratch Nitpick probe called `parse_ref_definition` with the whole input
chunk, then looked up `x` in a fresh map for each input. It used the same
build and link sequence. Both binaries exited 0 with empty stderr.

| Input as a string literal | Result at both levels |
| --- | --- |
| `"[x]: /u\n\"t\" trailing\n"` | Consumed 8 bytes. Hit with URL `/u` and an empty title. |
| `"[x]: a\x01b\n"` | Consumed 0 bytes. Miss. |
| `"[x]: <a\\\nb>\n"` | Consumed 0 bytes. Miss. |

## Compiler notes

No possible compiler fault arose during the review.
