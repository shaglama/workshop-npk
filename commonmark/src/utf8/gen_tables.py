#!/usr/bin/env python3
"""
Generate commonmark/src/utf8/cm_utf8_tables.npk for the Nitpick cmark port.

Reference:
  cmark 0.31.2 (commit eec0eeba6d31189fd828314576494566d539b1e3)
  - src/case_fold.inc (copied verbatim to commonmark/spec/case_fold.inc)
  - src/utf8.c (cmark_utf8proc_is_punctuation_or_symbol — Unicode 15.0.0 P* and S* set)

Usage:
  python3 gen_tables.py --case-fold-inc ../../spec/case_fold.inc

The generated file (cm_utf8_tables.npk) is committed; do not hand-edit it.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import os
import re
import sys
import unicodedata
from typing import Dict, List, Tuple


# Code points added to Unicode P/S in Unicode 15.1.0 that are NOT in cmark 0.31.2's
# src/utf8.c (cmark_utf8proc_is_punctuation_or_symbol uses the Unicode 15.0.0 P/S set).
CMARK_0_31_2_EXCLUDED_15_1_PS = frozenset({0x2FFC, 0x2FFD, 0x2FFE, 0x2FFF, 0x31EF})
CMARK_0_31_2_NON_ASCII_PS_COUNT = 8580


def load_utf8proc():
    path = ctypes.util.find_library("utf8proc")
    if not path:
        return None
    lib = ctypes.CDLL(path)
    lib.utf8proc_unicode_version.restype = ctypes.c_char_p
    lib.utf8proc_category_string.argtypes = [ctypes.c_int32]
    lib.utf8proc_category_string.restype = ctypes.c_char_p
    lib.utf8proc_decompose_char.argtypes = [
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32),
        ctypes.c_ssize_t,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
    ]
    lib.utf8proc_decompose_char.restype = ctypes.c_ssize_t
    return lib


def parse_cmark_case_fold_inc(path: str) -> Dict[int, List[int]]:
    """
    Parse cmark 0.31.2's src/case_fold.inc (cf_table + cf_repl compact table format),
    with fallback support for the older switch-statement case_fold_switch.inc format.
    """
    text = open(path, "r", encoding="utf-8").read()

    # Format 1 (cmark 0.31.2 src/case_fold.inc):
    #   #define CF_CODE_POINT(x)  ((x) & 0x1FFFF)
    #   #define CF_REPL_IDX(x)    ((((x) >> 17) & 0xFFF) * 2)
    #   #define CF_REPL_SIZE(x)   ((x) >> 29)
    #   static const uint32_t cf_table[N] = { ... };
    #   static const unsigned char cf_repl[M] = { ... };
    tbl_m = re.search(r"cf_table\s*\[\s*(\d+)\s*\]\s*=\s*\{([^}]*)\}", text, re.S)
    repl_m = re.search(r"cf_repl\s*\[\s*(\d+)\s*\]\s*=\s*\{([^}]*)\}", text, re.S)
    if tbl_m and repl_m:
        decl_tbl_len = int(tbl_m.group(1))
        decl_repl_len = int(repl_m.group(1))
        tbl_vals = [int(x, 0) for x in re.findall(r"0x[0-9a-fA-F]+|\d+", tbl_m.group(2))]
        repl_vals = [int(x, 0) for x in re.findall(r"0x[0-9a-fA-F]+|\d+", repl_m.group(2))]
        if len(tbl_vals) != decl_tbl_len:
            raise ValueError(
                f"{path}: cf_table length mismatch (parsed {len(tbl_vals)}, declared {decl_tbl_len})"
            )
        if len(repl_vals) != decl_repl_len:
            raise ValueError(
                f"{path}: cf_repl length mismatch (parsed {len(repl_vals)}, declared {decl_repl_len})"
            )
        mapping: Dict[int, List[int]] = {}
        for x in tbl_vals:
            cp = x & 0x1FFFF
            repl_idx = ((x >> 17) & 0xFFF) * 2
            repl_size = (x >> 29) & 0x7
            if repl_size == 0 or repl_idx + repl_size > len(repl_vals):
                raise ValueError(
                    f"{path}: invalid replacement slice for U+{cp:04X}: idx={repl_idx} size={repl_size}"
                )
            folded = bytes(repl_vals[repl_idx : repl_idx + repl_size]).decode("utf-8")
            cps = [ord(ch) for ch in folded]
            if cp in mapping:
                raise ValueError(f"{path}: duplicate case-fold entry for U+{cp:04X}")
            if cps == [cp]:
                raise ValueError(f"{path}: identity case-fold entry for U+{cp:04X}")
            mapping[cp] = cps
        if not mapping:
            raise ValueError(f"No case-fold entries parsed from {path}")
        return mapping

    # Format 2 (legacy switch form):
    #   case 0xXXXX: return (const uint8_t *)"\x..\x..";
    pattern = re.compile(
        r'case\s+(0x[0-9a-fA-F]+|\d+)\s*:[^;]*?"((?:\\.|[^"\\])*)"'
    )
    mapping = {}
    for m in pattern.finditer(text):
        cp = int(m.group(1), 0)
        raw_str = m.group(2)
        out_bytes = bytearray()
        i = 0
        while i < len(raw_str):
            if raw_str[i] == "\\" and i + 1 < len(raw_str):
                nxt = raw_str[i + 1]
                if nxt == "x" and i + 3 < len(raw_str):
                    out_bytes.append(int(raw_str[i + 2 : i + 4], 16))
                    i += 4
                elif nxt == "\\":
                    out_bytes.append(ord("\\"))
                    i += 2
                elif nxt == '"':
                    out_bytes.append(ord('"'))
                    i += 2
                elif nxt == "n":
                    out_bytes.append(10)
                    i += 2
                elif nxt == "r":
                    out_bytes.append(13)
                    i += 2
                elif nxt == "t":
                    out_bytes.append(9)
                    i += 2
                else:
                    raise ValueError(f"Unsupported escape in {path}: \\{nxt}")
            else:
                out_bytes.extend(raw_str[i].encode("utf-8"))
                i += 1
        folded = out_bytes.decode("utf-8")
        cps = [ord(ch) for ch in folded]
        if cps != [cp]:
            mapping[cp] = cps
    if not mapping:
        raise ValueError(f"No case-fold entries parsed from {path}")
    return mapping


def build_punct_ranges_cmark_0_31_2(lib) -> Tuple[List[Tuple[int, int]], str]:
    """
    Build the exact non-ASCII P/S code point ranges matching cmark 0.31.2's
    src/utf8.c (cmark_utf8proc_is_punctuation_or_symbol), which follows the
    Unicode 15.0.0 P/S categories (8,580 non-ASCII code points; excludes the
    5 Unicode 15.1.0 additions U+2FFC..U+2FFF and U+31EF).
    """
    if unicodedata.unidata_version == "15.0.0":
        cps = [
            cp
            for cp in range(0x80, 0x110000)
            if not (0xD800 <= cp <= 0xDFFF)
            and unicodedata.category(chr(cp))[0] in ("P", "S")
        ]
        source = (
            "cmark 0.31.2 src/utf8.c P/S set "
            "(Unicode 15.0.0 via Python unicodedata 15.0.0; excludes Unicode 15.1+ U+2FFC..U+2FFF, U+31EF)"
        )
        # Cross-check against libutf8proc 15.1.0 if present.
        if lib is not None and lib.utf8proc_unicode_version().decode("ascii") == "15.1.0":
            u8_cps = [
                cp
                for cp in range(0x80, 0x110000)
                if not (0xD800 <= cp <= 0xDFFF)
                and lib.utf8proc_category_string(cp).decode("ascii")[0] in ("P", "S")
            ]
            diff = set(u8_cps) - set(cps)
            if diff != set(CMARK_0_31_2_EXCLUDED_15_1_PS) or (set(cps) - set(u8_cps)):
                raise RuntimeError(
                    f"Unexpected diff vs libutf8proc 15.1.0: {sorted(hex(x) for x in diff)}"
                )
    elif lib is not None and lib.utf8proc_unicode_version().decode("ascii") == "15.1.0":
        cps = [
            cp
            for cp in range(0x80, 0x110000)
            if not (0xD800 <= cp <= 0xDFFF)
            and cp not in CMARK_0_31_2_EXCLUDED_15_1_PS
            and lib.utf8proc_category_string(cp).decode("ascii")[0] in ("P", "S")
        ]
        source = (
            "cmark 0.31.2 src/utf8.c P/S set "
            "(libutf8proc 15.1.0 minus Unicode 15.1 additions U+2FFC..U+2FFF, U+31EF)"
        )
    else:
        raise RuntimeError(
            f"Unsupported Unicode version for cmark 0.31.2 P/S table: "
            f"unicodedata={unicodedata.unidata_version}"
        )

    if len(cps) != CMARK_0_31_2_NON_ASCII_PS_COUNT:
        raise RuntimeError(
            f"Expected {CMARK_0_31_2_NON_ASCII_PS_COUNT} non-ASCII P/S code points "
            f"matching cmark 0.31.2 utf8.c, got {len(cps)}"
        )
    for excluded in CMARK_0_31_2_EXCLUDED_15_1_PS:
        if excluded in cps:
            raise RuntimeError(f"Excluded code point U+{excluded:04X} unexpectedly present")

    ranges: List[Tuple[int, int]] = []
    for cp in cps:
        if ranges and ranges[-1][1] + 1 == cp:
            ranges[-1] = (ranges[-1][0], cp)
        else:
            ranges.append((cp, cp))
    return ranges, source


def format_u32_array(name: str, values: List[int], per_line: int = 8) -> str:
    lines = [f"pub fixed uint32[{len(values)}]:{name} = ["]
    for i in range(0, len(values), per_line):
        chunk = values[i : i + per_line]
        items = ", ".join(f"{v}u32" for v in chunk)
        comma = "," if i + per_line < len(values) else ""
        lines.append(f"    {items}{comma}")
    lines.append("];")
    return "\n".join(lines)


def generate(out_path: str, case_fold_inc: str) -> None:
    lib = load_utf8proc()

    cf_map = parse_cmark_case_fold_inc(case_fold_inc)
    cf_source = f"cmark 0.31.2 ({os.path.basename(case_fold_inc)})"

    punct_ranges, punct_source = build_punct_ranges_cmark_0_31_2(lib)

    # ASCII A-Z is handled by an O(1) fast path in cm_utf8.npk.
    # cmark 0.31.2's case_fold.inc omits ASCII entries; if an alternate input
    # includes them, verify they are strictly A-Z -> a-z.
    for cp in range(0x80):
        actual = cf_map.get(cp)
        if actual is None:
            continue
        expected = [cp + 32] if 65 <= cp <= 90 else None
        if actual != expected:
            raise RuntimeError(
                f"Unexpected ASCII case fold for U+{cp:04X}: got {actual}, expected {expected}"
            )

    non_ascii_cf = sorted((cp, dst) for cp, dst in cf_map.items() if cp >= 0x80)

    # Encode destinations:
    #   - Single code point (len == 1): stored directly in CASE_FOLD_DST (<= 0x10FFFF).
    #   - Multi code point (len 2 or 3): CASE_FOLD_DST stores (0x200000 + multi_idx),
    #     where CASE_FOLD_MULTI holds 3 uint32 entries per multi-mapping: [c0, c1, c2]
    #     (with c2 == 0 for 2-codepoint folds).
    MULTI_TAG = 0x200000
    cf_src: List[int] = []
    cf_dst: List[int] = []
    cf_multi: List[int] = []

    for cp, dst in non_ascii_cf:
        cf_src.append(cp)
        if len(dst) == 1:
            assert dst[0] <= 0x10FFFF
            cf_dst.append(dst[0])
        elif len(dst) in (2, 3):
            multi_idx = len(cf_multi) // 3
            cf_dst.append(MULTI_TAG + multi_idx)
            cf_multi.append(dst[0])
            cf_multi.append(dst[1])
            cf_multi.append(dst[2] if len(dst) == 3 else 0)
        else:
            raise RuntimeError(f"Unsupported case-fold length {len(dst)} for U+{cp:04X}")

    punct_lo = [lo for lo, _ in punct_ranges]
    punct_hi = [hi for _, hi in punct_ranges]

    parts = [
        "// GENERATED FILE — DO NOT HAND-EDIT.",
        "//",
        "// Generated by: commonmark/src/utf8/gen_tables.py",
        "// Target reference: cmark 0.31.2 (commit eec0eeba6d31189fd828314576494566d539b1e3)",
        "//   src/case_fold.inc (commonmark/spec/case_fold.inc) and src/utf8.c",
        f"// Case-folding data source: {cf_source}",
        f"// Punctuation/symbol data source: {punct_source}",
        "//",
        "// Derived from cmark / utf8proc Unicode data (see commonmark/LICENSES/COPYING).",
        "// Written by Neon (Google).",
        "",
        "mod:cm_utf8_tables;",
        "",
        f"pub fixed int64:PUNCT_RANGE_COUNT = {len(punct_ranges)}i64;",
        format_u32_array("PUNCT_LO", punct_lo),
        "",
        format_u32_array("PUNCT_HI", punct_hi),
        "",
        f"pub fixed int64:CASE_FOLD_COUNT = {len(cf_src)}i64;",
        f"pub fixed int64:CASE_FOLD_MULTI_TAG = {MULTI_TAG}i64;",
        f"pub fixed int64:CASE_FOLD_MULTI_COUNT = {len(cf_multi) // 3}i64;",
        format_u32_array("CASE_FOLD_SRC", cf_src),
        "",
        format_u32_array("CASE_FOLD_DST", cf_dst),
        "",
        format_u32_array("CASE_FOLD_MULTI", cf_multi, per_line=9),
        "",
    ]

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts))

    print(
        f"Wrote {out_path}: {len(punct_ranges)} non-ASCII P/S ranges "
        f"({CMARK_0_31_2_NON_ASCII_PS_COUNT} code points), "
        f"{len(cf_src)} non-ASCII case-fold entries ({len(cf_multi) // 3} multi-codepoint)."
    )


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    default_cf = os.path.normpath(os.path.join(here, "..", "..", "spec", "case_fold.inc"))
    parser = argparse.ArgumentParser(description="Generate cm_utf8_tables.npk")
    parser.add_argument(
        "--case-fold-inc",
        default=default_cf,
        help="Path to cmark 0.31.2 src/case_fold.inc (default: ../../spec/case_fold.inc)",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(here, "cm_utf8_tables.npk"),
        help="Output .npk path",
    )
    args = parser.parse_args()
    generate(args.out, args.case_fold_inc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
