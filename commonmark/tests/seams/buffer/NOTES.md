Queue line done: 2. `next` — **seam tests: buffer** (tests/seams/buffer/), from INTERFACES.md Part 1 alone.

Astra line 1, **blocks part**, remains blocked pending the manager's `briefs/blocks.md`.

The seam program calls all eleven public functions. Its expected values come from the Part 1 contract and direct byte counts and comparisons. The ownership checks keep two buffers live, consume them independently, and check a copied chunk after its base has gone out of scope.

Run `python3 commonmark/tests/seams/buffer/check.py` from the repo root. All five test groups passed at `-O0` and `-O2` using the compiler pin `3a45b7c4`, its runtime and library, and the sandbox's LLVM 20.1.2 tools. [Build and test log](check.log)

## Compiler notes

No possible compiler faults observed.
