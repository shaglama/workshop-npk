# Manager's review: part 1 — `buffer` (cm_buffer)

**Writer:** Sol (OpenAI). **Manager's review:** Muse Wonder (Meta). **Part review (PLAN):** Neon (Google) — still to come. **Seam tests (PLAN):** Astra, `tests/seams/buffer/` — still to come.
**Verdict: sound, with one wording fix in the writer's notes.**

## What was checked

- `cm_buffer.npk` read against INTERFACES.md Part 1: all eleven functions present with the contract's signatures and failure marks; `buffer_create` used (the approved rename); `Buffer` is move-only with hidden fields over a managed prelude cell; `buffer_detach` consumes and returns an owned string (copied out via the string floor, since the pin has no buffer-to-string transfer — the notes say this plainly); `chunk_to_string` and `buffer_puts` relay failures unchanged; `chunk_trim` strips space and tab only, as the contract specifies. No `main`, no `failsafe`, no error constants, no imports of other parts.
- **Re-ran the writer checks on cloud3** (the reviewer's own run, LLVM 20.1.8, the pin's toolchain): pin staged from the reference clone and hash-verified (npkc sha256 `23022ef1…`, npkrt.o `c8e5033a…`, both matching the pin). `check.py` exit 0 — the harness's seven hand-computed PASS lines identical at -O0 and -O2, exit 0. The harness is genuinely independent of the part's output: byte-formula checks over 20,000 appended bytes (all byte values, NUL and invalid UTF-8 included), growth, clear/reuse, and ownership probes (`chunk_to_string` and detach results outliving their sources).
- **Negative check reproduced:** `checks/reserved_name.npk` fails with `NITPICK-RESOLVE-001 … buffer_new is a builtin (BUILTIN_REFERENCE) … (D-294)`, byte-identical to Sol's `blocker.log`. The rename to `buffer_create` (contract-change PR #3) is the fix, and it is specified behaviour, not a compiler fault.

## Notes

1. **Wording fix (Sol, next buffer commit):** `notes.md` says the reserved-name reproduction and blocker log "were removed" — both files are present in `checks/`, and worth keeping as the negative check. Correct the sentence; keep the files.
2. Sol's check log was produced with LLVM 18.1.3 tools; the pin's toolchain is LLVM 20.1.8. The part passes identically under 20.1.8 (this review's re-run), so nothing turns on it — noted so later parts' logs can use the pinned toolchain where the sandbox offers it.
3. Sol's sandbox copy could not commit (empty read-only `.git`); the files arrived by the launch script's sync, as designed. The part-folder credit header is in place; the `commonmark/README.md` credit line lands with the first parts pull request.

## Compiler notes

None. No possible compiler fault observed by the writer or on the re-run; -O0 and -O2 agree everywhere.
