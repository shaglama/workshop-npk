"""Build and run the cm_buffer seam test with the repository's compiler pin."""

from hashlib import sha256
from pathlib import Path
from shlex import join
from subprocess import PIPE, STDOUT, run
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[4]
SEAM = Path(__file__).resolve().parent.relative_to(ROOT)
PIN = Path("pin")
CASES = {
    11: "empty buffers, independent owners, append order, clear and reuse",
    12: "byte ranges, empty chunks, equality and copying inside UTF-8",
    13: "trim spaces and tabs within the chunk's bounds",
    14: "binary append and an owned copy that outlives its base",
    15: "growth across 16,388 bytes using all three append calls",
    16: "all byte ranges of a base containing whitespace, NUL and UTF-8",
    17: "large appends after clear and an interior copy that outlives its base",
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
    ir = build / "buffer.ll"
    optimized = build / "buffer.opt.ll"
    obj = build / "buffer.o"
    exe = build / "buffer_seam"
    steps = (
        (PIN / "npkc", SEAM / "buffer_seam.npk", "-o", ir),
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
