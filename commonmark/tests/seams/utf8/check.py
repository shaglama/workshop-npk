"""Build and run the cm_utf8 seam test with the repository's compiler pin."""

from hashlib import sha256
from pathlib import Path
from shlex import join
from subprocess import PIPE, STDOUT, run
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[4]
SEAM = Path(__file__).resolve().parent.relative_to(ROOT)
PIN = Path("pin")
CASES = {
    11: "iterate: valid sequences, chunk-relative positions, length-class boundaries, NUL",
    12: "iterate: invalid bytes, overlongs, surrogates, >U+10FFFF, truncation by the chunk",
    13: "iterate: at and past the end of the chunk",
    14: "encode: exact bytes at every length boundary, appending",
    15: "encode/iterate round trip across the scalar range",
    16: "check: valid text unchanged, chunk bounds, prefix kept",
    17: "check: invalid sequences repaired to U+FFFD, idempotent, well formed",
    18: "is_space: Zs, tab, LF, FF, CR; not VT, NEL, Cf, Zl, Zp",
    19: "is_punct: all 128 ASCII code points",
    20: "is_punct: P and S categories beyond ASCII; letters, marks, Z, C not",
    21: "case_fold: simple and full folds, pass-through, ASCII",
    22: "case_fold: chunks, appending, idempotence, label equality",
    23: "check exact counts: overlong, surrogate, >U+10FFFF are one U+FFFD",
    24: "check exact counts: bad continuation, truncation by the chunk",
    25: "check exact counts: stray bytes, chunk offsets, prefix",
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
    ir = build / "utf8.ll"
    optimized = build / "utf8.opt.ll"
    obj = build / "utf8.o"
    exe = build / "utf8_seam"
    steps = (
        (PIN / "npkc", SEAM / "utf8_seam.npk", "-o", ir),
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
