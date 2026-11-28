"""Build and run the cm_refs seam test with the repository's compiler pin."""

from hashlib import sha256
from pathlib import Path
from shlex import join
from subprocess import PIPE, STDOUT, run
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[4]
SEAM = Path(__file__).resolve().parent.relative_to(ROOT)
PIN = Path("pin")
CASES = {
    11: "empty map, basic add/lookup, independent maps, owned clones",
    12: "label normalisation: ASCII and Unicode case fold, whitespace, raw escapes",
    13: "first-definition precedence, blank labels, 1000-byte label limit",
    14: "store-time clean_url and clean_title behaviour via refmap_add",
    15: "chunk bounds and shared/distinct bases in refmap_add and refmap_lookup",
    16: "parse_ref_definition: basics, 0..3 vs 4-space/tab indent, line endings, EOF",
    17: "parse_ref_definition: angle and bare destinations, parens, escapes, controls",
    18: "parse_ref_definition: titles, multi-line, blank-line rule, next-line backtrack",
    19: "parse_ref_definition: label brackets, escapes, empty/blank, multi-line labels",
    20: "parse_ref_definition: consecutive definitions, duplicates, trailing paragraph",
    21: "parse_ref_definition: strict sub-chunk offsets and truncated lengths",
    22: "growth and scale across 400 definitions (refmap_add + sub-chunk parse)",
}


def command(*args):
    argv = [str(arg) for arg in args]
    print(f"$ {join(argv)}", flush=True)
    result = run(argv, cwd=ROOT, stdout=PIPE, stderr=STDOUT, text=True)
    if result.stdout:
        print(result.stdout, end="")
    print(f"exit: {result.returncode}", flush=True)
    return result.returncode


def build_and_test(build, level):
    ir = build / "references.ll"
    optimized = build / "references.opt.ll"
    obj = build / "references.o"
    exe = build / "references_seam"
    steps = (
        (PIN / "npkc", SEAM / "references_seam.npk", "-o", ir),
        ("opt-20", level, "-S", ir, "-o", optimized),
        ("llc-20", level, "-filetype=obj", "-relocation-model=static", optimized, "-o", obj),
        ("ld.lld-20", "-static", "-o", exe, obj, PIN / "npkrt.o"),
    )
    for step in steps:
        if command(*step):
            return False

    status = command(exe)
    if status == 0:
        for case in CASES.values():
            print(f"PASS {case}")
        return True
    if status == 100:
        print("FAIL Nitpick error or trap reached failsafe")
    else:
        print(f"FAIL {CASES.get(status, 'unexpected process exit')}")
    return False


def main():
    print("Compiler commit: 3a45b7c4")
    print(f"npkc sha256: {sha256((ROOT / PIN / 'npkc').read_bytes()).hexdigest()}")
    for tool in ("opt-20", "llc-20", "ld.lld-20"):
        if command(tool, "--version"):
            return 1

    results = []
    for level in ("-O0", "-O2"):
        print(f"\n{level}")
        with TemporaryDirectory(prefix=".build-", dir=ROOT / SEAM) as temp:
            results.append(build_and_test(Path(temp).relative_to(ROOT), level))
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
