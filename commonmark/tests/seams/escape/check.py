#!/usr/bin/env python3
"""Build and run the cm_escape seam test with the repository's compiler pin.
"""

import hashlib
import subprocess
import shlex
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SEAM = Path(__file__).resolve().parent.relative_to(ROOT)

PIN = Path("pin")
EXPECTED = (
    "PASS: escape_html_into\n"
    "PASS: escape_href_into\n"
    "PASS: unescape_entities_into\n"
    "PASS: unescape_backslashes_into\n"
    "PASS: clean_url & clean_title\n"
    "ALL cm_escape CHECKS PASSED\n"
)

def run(cmd, expected=None):
    cmd = [str(c) for c in cmd]
    print(f"$ {' '.join(shlex.quote(c) for c in cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60)
    print(f"exit: {result.returncode}\nstdout: {result.stdout.rstrip() or '(empty)'}\nstderr: {result.stderr.rstrip() or '(empty)'}", flush=True)
    if result.returncode != 0 or result.stderr:
        raise RuntimeError("command failed or emitted diagnostics")
    if expected is not None and result.stdout != expected:
        raise RuntimeError("output differs from expected")
    return result.stdout

def main():
    # Version checks
    run(["opt-20", "--version"])
    run(["llc-20", "--version"])
    run(["ld.lld-20", "--version"])
    build = SEAM.relative_to(ROOT).parent / "build"
    ir = build / "escape.ll"
    # Compile to LLVM IR
    run(["pin/npkc", "commonmark/tests/seams/escape/escape_seam.npk", "-o", str(ir)])
    for level in ("-O0", "-O2"):
        optimized = build / f"escape.{level}.ll"
        obj = build / f"escape.{level}.o"
        exe = build / f"escape.{level}"
        # Optimize
        run(["opt-20", level, "-S", str(ir), "-o", str(optimized)])
        # Compile to object
        run(["llc-20", level, "-filetype=obj", "-relocation-model=static", str(optimized), "-o", str(obj)])
        # Link
        run(["ld.lld-20", "-static", "-o", str(exe), str(obj), str(PIN / "npkrt.o")])
        # Run and check output
        out = run([str(exe)])
        if out != EXPECTED:
            raise RuntimeError("FAIL: unexpected output")
        print(f"PASS {level}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
