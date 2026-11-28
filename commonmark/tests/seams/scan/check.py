"""Build and run the cm_scan seam test with the repository's compiler pin.

Run from anywhere: python3 commonmark/tests/seams/scan/check.py
Groups run in batches of four per program, so one failing group never hides the rest:
each batch exits with a bitmask of its failed groups (100 = a Nitpick error or trap).
"""

import json
from hashlib import sha256
from pathlib import Path
from re import S, sub
from shlex import join
from subprocess import PIPE, STDOUT, run
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
SEAM = HERE.relative_to(ROOT)
PIN = Path("pin")
CASES = {int(k): v for k, v in json.loads((HERE / "groups.json").read_text()).items()}


def command(*args, quiet=False):
    argv = [str(arg) for arg in args]
    print(f"$ {join(argv)}", flush=True)
    result = run(argv, cwd=ROOT, stdout=PIPE, stderr=STDOUT, text=True)
    if result.stdout and not quiet:
        print(result.stdout, end="")
    print(f"exit: {result.returncode}", flush=True)
    return result.returncode


def batch_source(groups):
    src = (HERE / "scan_seam.npk").read_text().replace('"../../../src', '"../../../../src')
    lines = ["func:check_all = int32() {", "    int32:mask = 0i32;"]
    for bit, g in enumerate(groups):
        lines.append(f"    if (!(relay g{g}())) {{ mask = mask + {1 << bit}i32; }}")
    lines += ["    pass mask;", "};"]
    return sub(r"func:check_all = int32\(\) \{.*?\n\};", "\n".join(lines), src, flags=S)


def build_and_test(build, level, groups):
    """Returns the set of failing groups, or None when the build or run broke."""
    (ROOT / build / "scan_seam.npk").write_text(batch_source(groups))
    ir, optimized = build / "scan.ll", build / "scan.opt.ll"
    obj, exe = build / "scan.o", build / "scan_seam"
    steps = (
        (PIN / "npkc", build / "scan_seam.npk", "-o", ir),
        ("opt-20", level, "-S", ir, "-o", optimized),
        ("llc-20", level, "-filetype=obj", "-relocation-model=static", optimized, "-o", obj),
        ("ld.lld-20", "-static", "-o", exe, obj, PIN / "npkrt.o"),
    )
    for step in steps:
        if command(*step):
            return None
    status = command(exe)
    if status >= 16:
        print("FAIL Nitpick error, trap or crash")
        return None
    return {g for bit, g in enumerate(groups) if status & (1 << bit)}


def main():
    print("Compiler commit: 3a45b7c4")
    print(f"npkc sha256: {sha256((ROOT / PIN / 'npkc').read_bytes()).hexdigest()}")
    for tool in ("opt-20", "llc-20", "ld.lld-20"):
        if command(tool, "--version", quiet=True):
            return 1
    ordered = sorted(CASES)
    batches = [ordered[i:i + 4] for i in range(0, len(ordered), 4)]
    ok = True
    for level in ("-O0", "-O2"):
        print(f"\n{level}")
        failed, broken = set(), False
        with TemporaryDirectory(prefix=".build-", dir=ROOT / SEAM) as temp:
            for groups in batches:
                got = build_and_test(Path(temp).relative_to(ROOT), level, groups)
                if got is None:
                    broken = True
                else:
                    failed |= got
        for g in ordered:
            print(f"{'FAIL' if g in failed else 'PASS'} [{g}] {CASES[g]}")
        if failed or broken:
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
