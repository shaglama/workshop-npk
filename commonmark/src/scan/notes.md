# Scan — Sol (OpenAI)

Part 4 implementation and writer checks are complete. `cm_scan.npk` implements
all 22 public scanner functions in INTERFACES.md Part 4, with the exact parameter
and return types, all `never fails`. It imports no other module, owns no storage,
and contains no main, failsafe, or error constants. Every loop has a decreasing
byte count. Bounds checks supply a virtual NUL at the end rather than modifying
the lent base; embedded NUL has the tagged patterns' sentinel behavior.

Porting source read in full: cmark tag `0.31.2`, commit
`eec0eeba6d31189fd828314576494566d539b1e3`,
[src/scanners.re](https://github.com/commonmark/cmark/blob/0.31.2/src/scanners.re).
The header `src/scanners.h` could not be fetched through the available web
service (cache miss); shell downloads have no DNS access in this workspace.
No generated `scanners.c` was used. This is a hand implementation of the source
patterns, with the existing BSD notices retained in `commonmark/LICENSES/COPYING`.

## Return convention and integration

The frozen port contract says **every scanner returns a byte match length**.
Accordingly, `scan_setext_heading_line` returns the line's matched byte count,
not cmark's heading-level code; `scan_html_block_start` and
`scan_html_block_start_7` return matched byte counts, not cmark's block-type codes.
For example, `===\n` returns 4, `<script>` returns 8, and `<widget>\n` returns 9.
Callers must derive a level/type from the input instead of treating the return
as a cmark classification. This is an explicit contract adaptation, not a
proposed change to INTERFACES.md.

Other details retained from the patterns:

- ATX and setext scans require their stated whitespace/newline terminators;
  no implicit newline is invented at end of input. CRLF consumes only CR where
  the pattern has a single `[\r\n]`.
- Fence return lengths include only the marker run; the required line-ending
  lookahead and any info/whitespace are excluded.
- Autolink and inline HTML-tag scans start **after** the initial `<`.
  HTML comment starts at `--`, PI scans its body prefix without `<?` or `?>`,
  declaration starts at its ASCII letter and excludes `>`, and CDATA starts at
  `CDATA[` and scans the body prefix without requiring/including `]]>`.
- HTML raw/block tag names and dangerous-URL literals are ASCII case-insensitive;
  `CDATA[` is case-sensitive. The exact block-tag list includes `search`.
- Block-end patterns return through the last possible terminator before LF/NUL,
  matching their greedy prefix. CR is permitted inside that prefix.
- Link titles retain regex ambiguity: an escaped closing quote/parenthesis can
  also close a shorter valid match if there is no longer valid title. Backslashes
  can be literal body characters too, including repeated backslashes.
- Dangerous data URLs keep cmark's prefix whitelist exactly, including
  `data:image/png-extra`; there is no added media-type boundary check.
- Invalid offsets (negative or beyond the base) return 0 defensively.

## Checks

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 commonmark/src/scan/checks/check.py
```

PASS: **199,271 cases at each of -O0 and -O2**, exit 0, identical stdout,
empty stderr. The supplied compiler `pin/npkc` emits IR, then LLVM 20.1.2
`opt-20` and `llc-20` apply the selected level; `ld.lld-20` statically links
with `pin/npkrt.o`. The harness imports reporting functions from `pin/lib/nio.npk`
and uses binary stdin, preserving arbitrary bytes and line endings.

`checks/scan.log` records commands, statuses, output, LLVM versions, the compiler
commit `3a45b7c4`, compiler/runtime SHA-256, and a hash of the complete test input.
The runner removes its generated IR, objects, input and executables on success.

Expectations are independent of Nitpick output:

- `checks/vectors.py`: 218 hand-computed cases covering every scanner's matches,
  failures, shared-prefix near-misses and exact input boundaries, also repeated
  at nonzero offset 2. Per-scanner invalid offsets and empty/binary bases follow.
- `checks/patterns.py`: a separate byte-regex transcription of the tagged source
  patterns. Explicit longest-prefix matching models re2c maximal munch; fence
  lookahead is excluded from its returned length. Equivalent nested repetition
  is flattened to prevent Python backtracking blowups.
- 8,576 strings (all byte values, truncations, case variants, NUL suffixes,
  CommonMark spec lines, deterministic random bytes and mutations of worked
  examples) are cross-scanned by all 22 functions. Exhaustive small alphabets
  additionally check title escapes and comment/PI/CDATA body boundaries.

These are the brief's writer checks. Astra's independent seam suite and Carbon's
review are not supplied in this copy and remain external work. This is scanner
validation, not a claim that the full converter passes the spec examples.

## Compiler notes

No possible compiler fault observed. Read
`/home/outside/jobs/lab/context/known-issues.md` before implementation.
Both optimization levels compile, link, and run without crashes, diagnostics,
or differing output. No compiler-fault reproducer is needed.

## Handoff

Writes are confined to `commonmark/src/scan/` plus the wording correction in
`commonmark/src/buffer/notes.md` requested by the existing manager review: the
reserved-name negative reproduction and blocker log remain present. Both
folders are permitted by `commonmark/assign/sol.txt`.

No node work or other next piece has been started. A commit on `work/commonmark`
is unavailable in this copy: `.git` is an empty read-only directory, and Git
reports that this is not a repository. No Git metadata was written.
