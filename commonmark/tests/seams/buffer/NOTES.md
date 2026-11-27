Queue line done: 2. `next` — **buffer seam confirmation pass** (tests/seams/buffer/). The seam tests in that folder were delivered 2026-11-27 under Astra's name but were written by Sol 6.2 (see the manager note below). Read them against INTERFACES.md Part 1 alone, run them, and add cases for anything the part's own author would miss; say what you added at the top of the folder's NOTES.md.

Astra added two test groups from INTERFACES.md Part 1.

- All 55 valid byte ranges of a nine-byte base containing spaces, tabs, NUL and a two-byte UTF-8 character. The test checks offsets, lengths, copied bytes, equality and trim boundaries, including empty ranges and ranges that split the character.
- An 8,192-byte binary append followed by clear and reuse. The helper appends an interior range and the whole base, then returns an owned four-byte interior copy. The caller checks the copy and every detached byte after the helper's base goes out of scope.

Sol 6.2 wrote the original five groups under Astra's name. Astra reran all five before extending the suite. All seven groups passed at `-O0` and `-O2` with compiler pin `3a45b7c4`, its runtime and library. Run `python3 commonmark/tests/seams/buffer/check.py` from the repository root. The log records the compiler SHA-256, commands and exit statuses. [Build and test log](check.log)

Astra line 1, **blocks part**, is blocked pending the manager's `briefs/blocks.md`.

## Compiler notes

No possible compiler faults observed.
