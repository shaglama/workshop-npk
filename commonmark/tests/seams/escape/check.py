"""Build and run the cm_escape seam test with the repository's compiler pin."""

import hashlib
from pathlib import Path
import shlex
import subprocess
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE.relative_to(ROOT) / "escape_seam.npk"
COMPILER = "./pin/npkc"
RUNTIME = "./pin/npkrt.o"


def run(*args):
    argv = [str(arg) for arg in args]
    print(f"$ {shlex.join(argv)}", flush=True)
    try:
        result = subprocess.run(
            argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
    except OSError as error:
        print(f"FAIL could not run command: {error}")
        return None
    if result.stdout:
        print(result.stdout.decode("utf-8", errors="backslashreplace"), end="")
    print(f"exit: {result.returncode}", flush=True)
    return result


def build_and_run(level, build):
    ir = build / "escape.ll"
    optimized = build / "escape.opt.ll"
    obj = build / "escape.o"
    executable = build / "escape_seam"
    steps = [
        (COMPILER, SOURCE, "-o", ir),
        ("opt-20", level, "-S", ir, "-o", optimized),
        ("llc-20", level, "-filetype=obj", "-relocation-model=static", optimized, "-o", obj),
        ("ld.lld-20", "-static", "-o", executable, obj, RUNTIME),
    ]
    for step in steps:
        result = run(*step)
        if result is None or result.returncode != 0:
            print(f"FAIL {level} build")
            return None
    result = run(executable)
    if result is not None:
        if result.returncode == 100:
            print("FAIL Nitpick error or trap reached failsafe")
        elif result.returncode not in (0, 1):
            print(f"FAIL unexpected process exit {result.returncode}")
    return result


def main():
    print("Compiler commit: 3a45b7c4")
    print(f"npkc sha256: {hashlib.sha256((ROOT / COMPILER).read_bytes()).hexdigest()}")
    print("Library: ./pin/lib")
    version = run("opt-20", "--version")
    if version is None or version.returncode != 0:
        return 1

    outcomes = []
    for level in ("-O0", "-O2"):
        print(f"\n{level}", flush=True)
        with tempfile.TemporaryDirectory(prefix=".build-", dir=HERE) as scratch:
            outcomes.append(build_and_run(level, Path(scratch).relative_to(ROOT)))
    if all(result is not None for result in outcomes):
        debug, optimized = outcomes
        if (debug.returncode, debug.stdout) != (optimized.returncode, optimized.stdout):
            print("FAIL output or exit status differs between -O0 and -O2")
            return 1
    return 0 if all(result is not None and result.returncode == 0 for result in outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
