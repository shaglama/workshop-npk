#!/usr/bin/env python3
"""Reproduce the frozen contract's reserved-name blocker with the pinned compiler."""

import hashlib
from pathlib import Path
import shlex
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
COMPILER = ROOT / "pin/npkc"
SOURCE = HERE / "reserved_name.npk"


def main():
    lines = [
        "Compiler commit: 3a45b7c4 (public pin supplied with this workspace)",
        "npkc sha256: " + hashlib.sha256(COMPILER.read_bytes()).hexdigest(),
        "Expected: exit 1, NITPICK-RESOLVE-001 naming reserved builtin buffer_new.",
        "This is a negative compilation check, not a passing buffer implementation.",
        "npkc emits LLVM IR; optimization flags belong to opt/llc, after resolution.",
        "",
    ]
    ok = True
    for level in (0, 2):
        output = HERE / f"reserved_name.O{level}.ll"
        output.unlink(missing_ok=True)
        command = [str(COMPILER.relative_to(ROOT)), str(SOURCE.relative_to(ROOT)),
                   "-o", str(output.relative_to(ROOT))]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        lines.extend([
            f"-O{level} build pipeline:",
            "$ " + shlex.join(command),
            f"exit: {result.returncode}",
            "stdout: " + (result.stdout.rstrip() or "(empty)"),
            "stderr: " + (result.stderr.rstrip() or "(empty)"),
            f"opt/llc -O{level}, link against pin/npkrt.o, run: NOT REACHED; no IR emitted.",
            "",
        ])
        ok = ok and result.returncode == 1 and not output.exists()
        ok = ok and "NITPICK-RESOLVE-001" in result.stderr
        ok = ok and "`buffer_new` is a builtin" in result.stderr
    lines.append("Reserved-name reproduction: " + ("PASS" if ok else "FAIL"))
    log = "\n".join(lines) + "\n"
    (HERE / "blocker.log").write_text(log)
    print(log, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
