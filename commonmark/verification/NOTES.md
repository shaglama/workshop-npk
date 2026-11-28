Queue line done: 1. `next` — verification re-run: escape writer harness.

# Escape writer harness verification

**Commands run**:
```
python3 commonmark/src/escape/checks/check.py
```

**Compiler info**:
- Compiler commit: `3a45b7c4`
- `npkc` SHA256: `23022ef161268018fb83227c8f5f0f26d80917eff715af738c7e7e54a41f90a0`
- `npkrt.o` SHA256: `c8e5033ad17c70f838d567157738a6cc046af0ca3140ad92259fa71f0e747b4e`

**Results**:
- `-O0` build and run: PASS (all checks passed)
- `-O2` build and run: PASS (all checks passed)

**Output excerpt**:
```
PASS: escape_html_into
PASS: escape_href_into
PASS: unescape_entities_into
PASS: unescape_backslashes_into
PASS: clean_url & clean_title
ALL cm_escape CHECKS PASSED
-O0: PASS
-O2: PASS
Escape writer checks: PASS
```

No errors encountered.
