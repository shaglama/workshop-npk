#!/usr/bin/env python3
"""
Generate commonmark/src/utf8/cm_utf8_tables.npk for the Nitpick cmark port.

Reference:
  cmark 0.31.2 (commit eec0eeba6d31189fd828314576494566d539b1e3)
  - src/case_fold.inc (case_fold_switch.inc) — Unicode full case folding (C + F)
  - src/utf8.c (cmark_utf8proc_is_punctuation_or_symbol) — Unicode P* and S* categories

Usage:
  # Regenerate from a local cmark 0.31.2 checkout (case_fold.inc / case_fold_switch.inc):
  python3 gen_tables.py --case-fold-inc /path/to/cmark/src/case_fold_switch.inc

  # Regenerate offline from system libutf8proc (Unicode 15.1.0) / Python unicodedata:
  python3 gen_tables.py

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
    Parse cmark's src/case_fold.inc or src/case_fold_switch.inc.
    Supports both forms used across cmark releases:
      case 0xXXXX: return (const uint8_t *)"\\x..\\x..";
      case 0xXXXX: dest = (const uint8_t *)"..."; len = N; break;
    """
    text = open(path, "r", encoding="utf-8").read()
    # Match `case 0xHEX:` followed by a C string literal `"..."` before the next `case` or `}`
    pattern = re.compile(
        r'case\s+(0x[0-9a-fA-F]+|\d+)\s*:[^;]*?"((?:\\.|[^"\\])*)"'
    )
    mapping: Dict[int, List[int]] = {}
    for m in pattern.finditer(text):
        cp = int(m.group(1), 0)
        raw_str = m.group(2)
        # Decode C hex escapes (\xNN) and literal characters into bytes
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


def build_case_fold_from_system(lib) -> Tuple[Dict[int, List[int]], str]:
    mapping: Dict[int, List[int]] = {}
    if lib is not None:
        UTF8PROC_CASEFOLD = 1 << 10
        ver = lib.utf8proc_unicode_version().decode("ascii")
        buf = (ctypes.c_int32 * 16)()
        for cp in range(0x110000):
            if 0xD800 <= cp <= 0xDFFF:
                continue
            n = lib.utf8proc_decompose_char(cp, buf, 16, UTF8PROC_CASEFOLD, None)
            if n < 0:
                raise RuntimeError(f"utf8proc_decompose_char failed for U+{cp:04X}")
            cps = [int(buf[i]) for i in range(n)]
            if cps != [cp]:
                mapping[cp] = cps
        return mapping, f"libutf8proc (Unicode {ver})"
    ver = unicodedata.unidata_version
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        ch = chr(cp)
        folded = ch.casefold()
        if folded != ch:
            mapping[cp] = [ord(c) for c in folded]
    return mapping, f"Python unicodedata (Unicode {ver})"


def build_punct_ranges_from_system(lib) -> Tuple[List[Tuple[int, int]], str]:
    cps: List[int] = []
    if lib is not None:
        ver = lib.utf8proc_unicode_version().decode("ascii")
        for cp in range(0x80, 0x110000):
            if 0xD800 <= cp <= 0xDFFF:
                continue
            cat = lib.utf8proc_category_string(cp).decode("ascii")
            if cat and cat[0] in ("P", "S"):
                cps.append(cp)
        source = f"libutf8proc (Unicode {ver})"
    else:
        ver = unicodedata.unidata_version
        for cp in range(0x80, 0x110000):
            if 0xD800 <= cp <= 0xDFFF:
                continue
            cat = unicodedata.category(chr(cp))
            if cat and cat[0] in ("P", "S"):
                cps.append(cp)
        source = f"Python unicodedata (Unicode {ver})"

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


def generate(out_path: str, case_fold_inc: str | None) -> None:
    lib = load_utf8proc()

    if case_fold_inc is not None:
        cf_map = parse_cmark_case_fold_inc(case_fold_inc)
        cf_source = f"cmark 0.31.2 ({os.path.basename(case_fold_inc)})"
    else:
        cf_map, cf_source = build_case_fold_from_system(lib)

    punct_ranges, punct_source = build_punct_ranges_from_system(lib)

    # Filter out ASCII A-Z (handled by O(1) fast path in cm_utf8.npk).
    # Verify all ASCII mappings are strictly A-Z -> a-z.
    for cp in range(0x80):
        expected = [cp + 32] if 65 <= cp <= 90 else None
        actual = cf_map.get(cp)
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
        "//   src/case_fold.inc (case_fold_switch.inc) and src/utf8.c",
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
        f"Wrote {out_path}: {len(punct_ranges)} non-ASCII P/S ranges, "
        f"{len(cf_src)} non-ASCII case-fold entries ({len(cf_multi) // 3} multi-codepoint)."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate cm_utf8_tables.npk")
    parser.add_argument(
        "--case-fold-inc",
        default=None,
        help="Path to cmark 0.31.2 src/case_fold.inc or src/case_fold_switch.inc",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "cm_utf8_tables.npk"),
        help="Output .npk path",
    )
    args = parser.parse_args()
    generate(args.out, args.case_fold_inc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
