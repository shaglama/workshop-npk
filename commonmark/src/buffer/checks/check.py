#!/usr/bin/env python3
"""Build/run cm_buffer writer checks at O0 and O2 with the supplied pin.

The assertions in buffer_check.npk use hand-computed byte expectations and
cmark's append/clear semantics. This is not Astra's independent seam suite.
All generated files stay within this assigned part directory.
"""

import hashlib
from pathlib import Path
import shlex
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
COMPILER = ROOT / "pin/npkc"
BUILD = HERE / "build"
EXPECTED = (
    "empty create/detach: PASS\n"
    "chunk range/trim/equality/owned copy: PASS\n"
    "empty/all-space chunks; preserve CR/LF: PASS\n"
    "append chunk/string/byte; move/detach: PASS\n"
    "growth; 20000 bytes including NUL and invalid UTF-8: PASS\n"
    "bulk string/chunk growth preserves every byte: PASS\n"
    "clear empty/grown; reuse; clear then detach: PASS\n"
)


def main():
    lines = [
        "Compiler commit: 3a45b7c4 (public pin supplied with this workspace)",
        "npkc sha256: " + hashlib.sha256(COMPILER.read_bytes()).hexdigest(),
        "Runtime: pin/npkrt.o; library: pin/lib/nio.npk",
        "Writer checks: every Part 1 function; independent seam suite not supplied.",
        "Expected: exit 0 and the seven literal PASS lines below, at both levels.",
        "npkc emits LLVM IR; -O0/-O2 are applied to both opt and llc.",
        "",
    ]
    BUILD.mkdir(exist_ok=True)

    def run(command, expected=None):
        command = [str(arg) for arg in command]
        lines.append("$ " + shlex.join(command))
        result = subprocess.run(command, cwd=ROOT, capture_output=True,
                                text=True, timeout=60)
        lines.extend([
            f"exit: {result.returncode}",
            "stdout: " + (result.stdout.rstrip() or "(empty)"),
            "stderr: " + (result.stderr.rstrip() or "(empty)"),
        ])
        if result.returncode != 0 or result.stderr:
            raise RuntimeError("command failed or emitted diagnostics")
        if expected is not None and result.stdout != expected:
            raise RuntimeError("output differs from the hand-written expectation")

    ok = False
    try:
        run(["opt-18", "--version"])
        run(["llc-18", "--version"])
        run(["ld.lld", "--version"])
        build = BUILD.relative_to(ROOT)
        for level in (0, 2):
            lines.append(f"\n-O{level} build and run:")
            ir = build / f"buffer.O{level}.ll"
            optimized = build / f"buffer.O{level}.opt.ll"
            obj = build / f"buffer.O{level}.o"
            binary = build / f"buffer.O{level}"
            run(["pin/npkc", "commonmark/src/buffer/checks/buffer_check.npk",
                 "-o", ir])
            run(["opt-18", f"-O{level}", "-S", ir, "-o", optimized])
            run(["llc-18", f"-O{level}", "-filetype=obj",
                 "-relocation-model=static", optimized, "-o", obj])
            run(["ld.lld", "-static", "-o", binary, obj, "pin/npkrt.o"])
            run([binary], EXPECTED)
            lines.append(f"-O{level}: PASS")
        ok = True
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        lines.append("FAIL: " + str(error))
    finally:
        shutil.rmtree(BUILD)
        lines.append("\nBuffer writer checks: " + ("PASS" if ok else "FAIL"))
        log = "\n".join(lines) + "\n"
        (HERE / "buffer.log").write_text(log)
        print(log, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
