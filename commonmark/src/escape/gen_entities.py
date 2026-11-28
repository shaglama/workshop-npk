#!/usr/bin/env python3
"""
Generate commonmark/src/escape/cm_escape_entities.npk for the Nitpick cmark port.

Reference:
  cmark 0.31.2 (commit eec0eeba6d31189fd828314576494566d539b1e3)
  - src/entities.inc (copied verbatim to commonmark/spec/entities.inc)

Usage:
  # Regenerate from the in-repo cmark 0.31.2 entities.inc (default):
  python3 gen_entities.py
  python3 gen_entities.py --entities-inc ../../spec/entities.inc

  # Regenerate from a local WHATWG entities.json (same input cmark's tools/make_entities_inc.py uses):
  python3 gen_entities.py --entities-json /path/to/entities.json

  # Regenerate offline from Python stdlib html.entities.html5 (identical 2,125 WHATWG HTML5
  # semicolon-terminated named character references):
  python3 gen_entities.py --stdlib

The generated file (cm_escape_entities.npk) is committed; do not hand-edit it.
"""

from __future__ import annotations

import argparse
import html.entities
import json
import os
import re
import sys
from typing import Dict, List, Tuple


def load_from_entities_inc(path: str) -> Tuple[Dict[str, List[int]], str]:
    """Parse cmark 0.31.2's packed src/entities.inc (cmark_entities + cmark_entity_text)."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    ent_m = re.search(r"cmark_entities\s*\[\s*(\d+)\s*\]\s*=\s*\{([^}]*)\}", text, re.S)
    txt_m = re.search(r"cmark_entity_text\s*\[\s*(\d+)\s*\]\s*=\s*\{([^}]*)\}", text, re.S)
    if not ent_m or not txt_m:
        raise ValueError(f"{path}: could not find cmark_entities / cmark_entity_text arrays")

    decl_ent_len = int(ent_m.group(1))
    decl_txt_len = int(txt_m.group(1))
    ent_vals = [int(x, 0) for x in re.findall(r"0x[0-9a-fA-F]+|\d+", ent_m.group(2))]
    txt_vals = [int(x, 0) for x in re.findall(r"0x[0-9a-fA-F]+|\d+", txt_m.group(2))]

    if len(ent_vals) != decl_ent_len:
        raise ValueError(
            f"{path}: cmark_entities length mismatch (parsed {len(ent_vals)}, declared {decl_ent_len})"
        )
    if len(txt_vals) != decl_txt_len:
        raise ValueError(
            f"{path}: cmark_entity_text length mismatch (parsed {len(txt_vals)}, declared {decl_txt_len})"
        )
    if any(b < 0 or b > 0xFF for b in txt_vals):
        raise ValueError(f"{path}: byte value out of range in cmark_entity_text")

    size_m = re.search(r"#define\s+ENT_TABLE_SIZE\s+(\d+)", text)
    if size_m and int(size_m.group(1)) != len(ent_vals):
        raise ValueError(
            f"{path}: ENT_TABLE_SIZE ({size_m.group(1)}) != cmark_entities length ({len(ent_vals)})"
        )

    raw_bytes = bytes(txt_vals)
    mapping: Dict[str, List[int]] = {}
    for x in ent_vals:
        text_idx = x & 0x7FFF
        name_size = (x >> 15) & 0x1F
        repl_size = x >> 20
        if name_size == 0 or repl_size == 0 or text_idx + name_size + repl_size > len(raw_bytes):
            raise ValueError(
                f"{path}: invalid entity descriptor 0x{x:X} "
                f"(idx={text_idx}, name_size={name_size}, repl_size={repl_size})"
            )
        name = raw_bytes[text_idx : text_idx + name_size].decode("ascii")
        repl = raw_bytes[text_idx + name_size : text_idx + name_size + repl_size].decode("utf-8")
        if name in mapping:
            raise ValueError(f"{path}: duplicate entity name {name!r}")
        mapping[name] = [ord(ch) for ch in repl]

    if not mapping:
        raise ValueError(f"No entities parsed from {path}")
    return mapping, f"cmark 0.31.2 ({os.path.basename(path)})"


def load_from_entities_json(path: str) -> Tuple[Dict[str, List[int]], str]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    mapping: Dict[str, List[int]] = {}
    for key, entry in data.items():
        if key.startswith("&") and key.endswith(";"):
            name = key[1:-1]
            cps = [int(cp) for cp in entry["codepoints"]]
            mapping[name] = cps
    if not mapping:
        raise ValueError(f"No semicolon-terminated entities parsed from {path}")
    return mapping, f"WHATWG entities.json ({os.path.basename(path)})"


def load_from_stdlib() -> Tuple[Dict[str, List[int]], str]:
    mapping: Dict[str, List[int]] = {}
    for key, val in html.entities.html5.items():
        if key.endswith(";"):
            name = key[:-1]
            mapping[name] = [ord(ch) for ch in val]
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return mapping, f"Python {ver} html.entities.html5 (WHATWG HTML5)"


def format_u32_array(name: str, values: List[int], per_line: int = 8) -> str:
    lines = [f"pub fixed uint32[{len(values)}]:{name} = ["]
    for i in range(0, len(values), per_line):
        chunk = values[i : i + per_line]
        items = ", ".join(f"{v}u32" for v in chunk)
        comma = "," if i + per_line < len(values) else ""
        lines.append(f"    {items}{comma}")
    lines.append("];")
    return "\n".join(lines)


def format_u8_array(name: str, values: bytes, per_line: int = 16) -> str:
    lines = [f"pub fixed uint8[{len(values)}]:{name} = ["]
    for i in range(0, len(values), per_line):
        chunk = values[i : i + per_line]
        items = ", ".join(f"{v}u8" for v in chunk)
        comma = "," if i + per_line < len(values) else ""
        lines.append(f"    {items}{comma}")
    lines.append("];")
    return "\n".join(lines)


def generate(
    out_path: str,
    entities_inc: str | None,
    entities_json: str | None,
    use_stdlib: bool,
) -> None:
    if entities_inc is not None:
        ent_map, source = load_from_entities_inc(entities_inc)
    elif entities_json is not None:
        ent_map, source = load_from_entities_json(entities_json)
    elif use_stdlib:
        ent_map, source = load_from_stdlib()
    else:
        raise ValueError("No entity data source specified")

    # Validate invariants expected by cm_escape.npk
    for name, cps in ent_map.items():
        if not (name.isascii() and name.isalnum()):
            raise ValueError(f"Non-ASCII-alnum entity name: {name!r}")
        if not (1 <= len(cps) <= 2):
            raise ValueError(f"Unexpected codepoint count {len(cps)} for &{name};")
        for cp in cps:
            if cp <= 0 or (0xD800 <= cp <= 0xDFFF) or cp > 0x10FFFF:
                raise ValueError(f"Invalid codepoint U+{cp:X} for &{name};")

    # Sort lexicographically by ASCII byte order for binary search in cm_escape.npk
    items = sorted(ent_map.items(), key=lambda kv: kv[0].encode("ascii"))

    min_len = min(len(k) for k, _ in items)
    max_len = max(len(k) for k, _ in items)

    names_buf = bytearray()
    name_offs: List[int] = [0]
    cp1_list: List[int] = []
    cp2_list: List[int] = []

    for name, cps in items:
        names_buf.extend(name.encode("ascii"))
        name_offs.append(len(names_buf))
        cp1_list.append(cps[0])
        cp2_list.append(cps[1] if len(cps) == 2 else 0)

    names_str = names_buf.decode("ascii")

    parts = [
        "// GENERATED FILE — DO NOT HAND-EDIT.",
        "//",
        "// Generated by: commonmark/src/escape/gen_entities.py",
        "// Target reference: cmark 0.31.2 (commit eec0eeba6d31189fd828314576494566d539b1e3)",
        "//   src/entities.inc (commonmark/spec/entities.inc — HTML5 named character references)",
        f"// Entity data source: {source}",
        "//",
        "// Derived from cmark / WHATWG HTML5 entity table (see commonmark/LICENSES/COPYING).",
        "// Written by Neon (Google).",
        "",
        "mod:cm_escape_entities;",
        "",
        f"pub fixed int64:ENTITY_COUNT = {len(items)}i64;",
        f"pub fixed int64:ENTITY_MIN_LEN = {min_len}i64;",
        f"pub fixed int64:ENTITY_MAX_LEN = {max_len}i64;",
        f'pub fixed string:ENTITY_NAMES = "{names_str}";',
        "",
        format_u32_array("ENTITY_NAME_OFF", name_offs),
        "",
        format_u32_array("ENTITY_CP1", cp1_list),
        "",
        format_u32_array("ENTITY_CP2", cp2_list),
        "",
    ]

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts))

    multi_count = sum(1 for c2 in cp2_list if c2 != 0)
    print(
        f"Wrote {out_path}: {len(items)} HTML5 entities "
        f"(len {min_len}..{max_len}, {len(names_buf)} name bytes, {multi_count} 2-codepoint)."
    )


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    default_inc = os.path.normpath(os.path.join(here, "..", "..", "spec", "entities.inc"))

    parser = argparse.ArgumentParser(description="Generate cm_escape_entities.npk")
    src_group = parser.add_mutually_exclusive_group()
    src_group.add_argument(
        "--entities-inc",
        default=None,
        help="Path to cmark 0.31.2 src/entities.inc (default when no source flag is given: ../../spec/entities.inc)",
    )
    src_group.add_argument(
        "--entities-json",
        default=None,
        help="Path to WHATWG HTML5 entities.json (same source as cmark 0.31.2 src/entities.inc)",
    )
    src_group.add_argument(
        "--stdlib",
        action="store_true",
        help="Read HTML5 entities from Python stdlib html.entities.html5 instead of entities.inc",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(here, "cm_escape_entities.npk"),
        help="Output .npk path",
    )
    args = parser.parse_args()

    entities_inc = args.entities_inc
    if entities_inc is None and args.entities_json is None and not args.stdlib:
        entities_inc = default_inc

    generate(args.out, entities_inc, args.entities_json, args.stdlib)
    return 0


if __name__ == "__main__":
    sys.exit(main())
