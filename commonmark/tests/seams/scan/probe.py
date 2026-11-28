"""Probe: python3 probe.py scan_fn 'text' [at] -> prints the scanner's result (exit code of a tiny program)."""
import subprocess, sys, tempfile, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen import lit
here = pathlib.Path(__file__).resolve().parent
root = here.parents[3]
pairs = list(zip(sys.argv[1::3], sys.argv[2::3], (sys.argv[3::3] + ["0"] * 99)))
fn_, s_, at_ = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0
src = f'''mod:scan_seam;
use "../../../../src/scan/cm_scan.npk".*;
func:main = int32(cstring[]:_~argv) {{
    int64:r = raw {fn_}({lit(s_)}, {at_}i64);
    exit (r =>! int32);
}};
func:failsafe = int32(Error:err) {{
    pick (err) {{
        (Unreachable, HeapOom, HeapBadRequest, WildLeak, StackExhausted,
         MachineFault, DivByZero, DivOverflow, IntOverflow, OutOfBounds,
         DecreasesViolated) {{ exit 100i32; }},
        (*) {{ exit 100i32; }}
    }}
}};
'''
d = pathlib.Path(tempfile.mkdtemp(dir=here))
(d / "scan_seam.npk").write_text(src)
sh = f"cd {root} && pin/npkc {d}/scan_seam.npk -o {d}/d.ll && opt-20 -O0 -S {d}/d.ll -o {d}/o.ll && llc-20 -O0 -filetype=obj -relocation-model=static {d}/o.ll -o {d}/d.o && ld.lld-20 -static -o {d}/d {d}/d.o pin/npkrt.o"
r = subprocess.run(sh, shell=True, capture_output=True, text=True)
if r.returncode: print(r.stdout, r.stderr)
else: print(subprocess.run([str(d / "d")]).returncode)
subprocess.run(["rm", "-rf", str(d)])
