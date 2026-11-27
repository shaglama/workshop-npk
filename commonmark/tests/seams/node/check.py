"""Build and run the cm_node seam test with the repository's compiler pin."""

from hashlib import sha256
from pathlib import Path
from shlex import join
from subprocess import PIPE, STDOUT, run
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[4]
SEAM = Path(__file__).resolve().parent.relative_to(ROOT)
PIN = Path("pin")
CASES = {
    11: "create: empty document, node_new kinds, unattached links, empty strings",
    12: "append/prepend: links, re-parenting detaches from old siblings",
    13: "insert_before/after, unlink, replace",
    14: "strings: literal, code info, link, custom; clones, NUL, growth",
    15: "plain setters: list, fence, heading, html type, sourcepos, flags",
    16: "iterator: order, bounds, raw events, independence, Done",
    17: "walk mutation: children added to the entered node are visited",
    18: "consolidate_text_nodes: runs, breaks, subtree, unlinking",
    19: "doc_ref_lookup through doc_set_refs: normalised labels, replace",
    20: "growth: 3000 nodes, references stay valid, depth 2000",
    21: "root: first DocumentNode becomes the root (contract reading)",
    22: "prepend into an empty parent",
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
    ir = build / "node.ll"
    optimized = build / "node.opt.ll"
    obj = build / "node.o"
    exe = build / "node_seam"
    steps = (
        (PIN / "npkc", SEAM / "node_seam.npk", "-o", ir),
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
