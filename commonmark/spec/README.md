# Reference material in this folder

- `spec.txt` — the CommonMark spec, version 0.31.2: the 652 examples the spec runner checks against. From cmark 0.31.2 (`test/spec.txt`).
- `case_fold.inc` — cmark 0.31.2's generated Unicode case-folding table (`src/case_fold.inc`, verbatim). The `utf8` part's table generator reads this file: `gen_tables.py --case-fold-inc spec/case_fold.inc`. Provided in the repo because the writers' sandboxes have no cmark checkout; generating from any other source (e.g. a system Unicode library) risks version drift — cmark 0.31.2's table is Unicode 16 data.
- `entities.inc` — cmark 0.31.2's generated HTML entity table (`src/entities.inc`, verbatim). The `escape` part's table generator reads this file.

All three are cmark material, under the notices in `../LICENSES/COPYING`. Nothing here is hand-edited; a replacement comes from the cmark repo at the pinned tag, whole.
