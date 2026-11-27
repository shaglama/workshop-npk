#!/usr/bin/env python3
"""Build/run scan writer checks at O0/O2 using only the supplied compiler pin.

Expected results come from hand-worked vectors and a separate byte-regex
transcription of scanners.re, never from Nitpick output. This is not Astra's
independent seam suite. Generated artifacts stay inside this assigned folder.
"""
import hashlib
import itertools
from pathlib import Path
import random
import shlex
import shutil
import struct
import subprocess

from patterns import NAMES, expected
from vectors import VECTORS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BUILD = HERE / 'build'


def make_cases():
    cases = []
    for name in NAMES:
        for base, want in VECTORS[name]:
            oracle = expected(name, base, 0)
            if oracle != want:
                raise ValueError(f'hand vector / pattern disagreement: {name} {base!r}: hand={want}, regex={oracle}')
            cases.append((name, base, 0, want))
            cases.append((name, b'xx' + base, 2, want))
        for base in (b'', b'x', b'\x00', b'\xff', b'\r\n'):
            for at in (-1, len(base), len(base) + 1):
                cases.append((name, base, at, 0))

    # Every raw byte, every prefix/truncation of the worked cases, and realistic
    # spec lines. Cross-scan these so no scanner's corpus depends on its code.
    corpus = {bytes([b]) for b in range(256)}
    for vectors in VECTORS.values():
        for base, _ in vectors:
            corpus.update(base[:i] for i in range(len(base) + 1))
            corpus.update((base.lower(), base.upper(), base + b'\x00tail', base + b'\n'))
    spec = (ROOT / 'commonmark/spec/spec.txt').read_bytes()
    corpus.update(spec.splitlines(keepends=True))
    rng = random.Random(0x31_2)
    alphabet = b'aZ09-:=<>/?![]()\'"`~#\\ \t\v\f\r\n\x00\x80\xff'
    for _ in range(1800):
        corpus.add(bytes(rng.choices(alphabet, k=rng.randrange(0, 50))))
    # Mutation of valid prefixes creates near-misses deeper than uniform noise.
    seeds = [s for pairs in VECTORS.values() for s, _ in pairs]
    for _ in range(1800):
        s = bytearray(rng.choice(seeds))
        if s:
            s[rng.randrange(len(s))] = rng.choice(alphabet)
        corpus.add(bytes(s))
    for base in sorted(corpus):
        for name in NAMES:
            cases.append((name, base, 0, expected(name, base, 0)))

    # Exhaustive small alphabets target the ambiguous body grammars directly.
    for name, alphabet, prefix in (
        ('link_title', b'"\\a', b'"'),
        ('link_title', b'()\\a', b'('),
        ('html_comment', b'->a', b'--'),
        ('html_pi', b'?>a', b''),
        ('html_cdata', b']>a', b'CDATA['),
    ):
        for n in range(7):
            for parts in itertools.product(alphabet, repeat=n):
                base = prefix + bytes(parts)
                cases.append((name, base, 0, expected(name, base, 0)))
    return cases, len(corpus)


def main():
    lines = [
        'Compiler commit: 3a45b7c4 (public pin supplied with this workspace)',
        'npkc sha256: ' + hashlib.sha256((ROOT / 'pin/npkc').read_bytes()).hexdigest(),
        'npkrt.o sha256: ' + hashlib.sha256((ROOT / 'pin/npkrt.o').read_bytes()).hexdigest(),
        'Runtime: pin/npkrt.o; library: pin/lib/nio.npk',
        'References: cmark 0.31.2 src/scanners.re; CommonMark 0.31.2 spec lines.',
        'Expectations: hand lengths in vectors.py and independent regex oracle in patterns.py.',
        'All 22 scanners return match lengths per the frozen contract.',
        'npkc emits IR; -O0/-O2 applied to both opt and llc (LLVM 20).',
    ]
    BUILD.mkdir(exist_ok=True)
    ok = False
    cases = []

    def run(command, input_data=None, want=None):
        command = [str(s) for s in command]
        lines.append('$ ' + shlex.join(command))
        p = subprocess.run(command, cwd=ROOT, input=input_data,
                           capture_output=True, timeout=60)
        out = p.stdout.decode(errors='replace')
        err = p.stderr.decode(errors='replace')
        lines.extend([f'exit: {p.returncode}', 'stdout: ' + (out.rstrip() or '(empty)'),
                      'stderr: ' + (err.rstrip() or '(empty)')])
        if p.returncode or err or (want is not None and out != want):
            # Persist failure evidence before investigating implementation or
            # possible compiler behavior, per the project's compiler-notes rule.
            if out.startswith('FAIL case '):
                idx = int(out.split()[2])
                lines.append('Failing input: ' + repr(cases[idx]))
            (HERE / 'scan.log').write_text('\n'.join(lines) + '\n')
            raise RuntimeError('command failed, emitted diagnostics, or differed from expected output')
        return out

    try:
        cases, corpus_count = make_cases()
        lines.extend([f'Hand-computed vectors: {sum(map(len, VECTORS.values()))}; each also tested at offset 2.',
                      f'Cross-scanned byte/spec/random/mutation corpus: {corpus_count} strings.',
                      f'Total cases including invalid offsets and exhaustive grammars: {len(cases)}.'])
        packed = b''.join(struct.pack('<BIII', NAMES.index(name), at + 1, want, len(base)) + base
                          for name, base, at, want in cases)
        (BUILD / 'cases.bin').write_bytes(packed)
        lines.append('cases.bin sha256: ' + hashlib.sha256(packed).hexdigest())
        want = f'scan writer checks: PASS; cases={len(cases)}\n'
        run(['opt-20', '--version'])
        run(['llc-20', '--version'])
        run(['ld.lld-20', '--version'])
        build = BUILD.relative_to(ROOT)
        for level in (0, 2):
            ir = build / f'scan.O{level}.ll'
            optimized = build / f'scan.O{level}.opt.ll'
            obj = build / f'scan.O{level}.o'
            binary = build / f'scan.O{level}'
            lines.append(f'\n-O{level} build and run:')
            run(['pin/npkc', 'commonmark/src/scan/checks/scan_check.npk', '-o', ir])
            run(['opt-20', f'-O{level}', '-S', ir, '-o', optimized])
            run(['llc-20', f'-O{level}', '-filetype=obj', '-relocation-model=static', optimized, '-o', obj])
            run(['ld.lld-20', '-static', '-o', binary, obj, 'pin/npkrt.o'])
            run([binary], packed, want)
            lines.append(f'-O{level}: PASS')
        ok = True
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        lines.append('FAIL: ' + str(error))
    finally:
        if ok:
            shutil.rmtree(BUILD)
        lines.append('\nScan writer checks: ' + ('PASS' if ok else 'FAIL'))
        log = '\n'.join(lines) + '\n'
        (HERE / 'scan.log').write_text(log)
        print(log, end='')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
