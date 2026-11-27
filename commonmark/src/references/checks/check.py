#!/usr/bin/env python3
"""Build and run cm_refs writer checks at -O0 and -O2 with the supplied pin.

Uses LLVM 20 tools (opt-20, llc-20, ld.lld-20) and writes check.log in this folder.
All temporary build outputs are removed on exit.
"""

import hashlib
from pathlib import Path
import shlex
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
COMPILER = ROOT / "pin/npkc"
RUNTIME = ROOT / "pin/npkrt.o"
BUILD = HERE / "build"
EXPECTED = (
    "PASS: refmap_new & empty lookup\n"
    "PASS: refmap_add & refmap_lookup normalisation\n"
    "PASS: refmap_add cleaning, first-wins & clones\n"
    "PASS: refmap hash growth & 1000-byte boundary\n"
    "PASS: parse_ref_definition spec examples\n"
    "PASS: parse_ref_definition edge cases & sub-chunks\n"
    "ALL cm_refs CHECKS PASSED\n"
)


def main() -> int:
    lines = [
        "# Check log — Part 6: `references` (module `cm_refs`)",
        "",
        "Writer: Neon (Google)",
        "Compiler commit: 3a45b7c4 (public pin supplied with this workspace)",
        "npkc sha256: " + hashlib.sha256(COMPILER.read_bytes()).hexdigest(),
        "npkrt.o sha256: " + hashlib.sha256(RUNTIME.read_bytes()).hexdigest(),
        "Writer checks: every Part 6 function; independent seam suite by Carbon is separate.",
        "Expected: exit 0 and the seven literal PASS lines below, at both -O0 and -O2.",
        "",
    ]
    BUILD.mkdir(exist_ok=True)

    def run(command, expected=None):
        command = [str(arg) for arg in command]
        lines.append("$ " + shlex.join(command))
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, timeout=60
        )
        lines.extend([
            f"exit: {result.returncode}",
            "stdout: " + (result.stdout.rstrip() or "(empty)"),
            "stderr: " + (result.stderr.rstrip() or "(empty)"),
        ])
        if result.returncode != 0 or result.stderr:
            raise RuntimeError("command failed or emitted diagnostics")
        if expected is not None and result.stdout != expected:
            raise RuntimeError("output differs from hand-written expectation")

    ok = False
    try:
        run(["opt-20", "--version"])
        run(["llc-20", "--version"])
        run(["ld.lld-20", "--version"])
        build = BUILD.relative_to(ROOT)
        ir = build / "check_refs.ll"
        lines.append("\nCompile to LLVM IR:")
        run(["pin/npkc", "commonmark/src/references/checks/check_refs.npk", "-o", ir])
        for level in (0, 2):
            lines.append(f"\n-O{level} build and run:")
            optimized = build / f"check_refs.O{level}.ll"
            obj = build / f"check_refs.O{level}.o"
            binary = build / f"check_refs.O{level}"
            run(["opt-20", f"-O{level}", "-S", ir, "-o", optimized])
            run([
                "llc-20", f"-O{level}", "-filetype=obj",
                "-relocation-model=static", optimized, "-o", obj,
            ])
            run(["ld.lld-20", "-static", "-o", binary, obj, "pin/npkrt.o"])
            run([binary], EXPECTED)
            lines.append(f"-O{level}: PASS")
        ok = True
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        lines.append("FAIL: " + str(error))
    finally:
        shutil.rmtree(BUILD, ignore_errors=True)
        lines.append("\nReferences writer checks: " + ("PASS" if ok else "FAIL"))
        log = "\n".join(lines) + "\n"
        (HERE / "check.log").write_text(log, encoding="utf-8")
        print(log, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
