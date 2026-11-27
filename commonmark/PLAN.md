# Plan: a Nitpick port of cmark (CommonMark → HTML)

Manager: Muse Wonder (Meta). Process: the repo's `WORKFLOW.md` and the project guide from management (2026-11-27).

## What is being ported

- **Source:** cmark, the reference C implementation of CommonMark — https://github.com/commonmark/cmark
- **Release tag:** `0.31.2` (commit `eec0eeba6d31189fd828314576494566d539b1e3`)
- **Spec implemented by that tag:** CommonMark **0.31.2**; its `test/spec.txt` carries **652 examples**, which are this project's primary oracle.
- **Scope:** Markdown → HTML only. cmark's XML, man, LaTeX and CommonMark renderers are out of scope, as are its extensions (footnotes, tables and the like are not in cmark core and are not in this port). The CLI surface is the small subset the driver part defines in INTERFACES.md.
- **Compiler:** the public Nitpick compiler at `3a45b7c4` (the lab's pin), language reference its `meta/specs/`. The exchange's `lab/context/known-issues.md` lists the open faults to recognise and work around; check it before reporting anything as new.

## Why this shape

The lab tests one feature at a time in small programs. This port is the opposite bet: several parts handing values to each other, so the seams get exercised — ownership across a module's calls, errors carried up through layers to one `failsafe`, declarations shared across files. The design choices in INTERFACES.md (one owner for the node tree, borrowed text views with a stated convention, a total parse with failures only from allocation and IO) are made to put those seams where we can test them.

## The parts

One folder per part under `src/`. cmark sources named are the porting reference for each part, not a line-by-line obligation: the contract in INTERFACES.md is what a part must satisfy.

| # | Part | Job | cmark reference | Writer | Reviewer | Seam tests by |
|---|---|---|---|---|---|---|
| 1 | `buffer` | Growable byte buffer and the borrowed-view type every parser part reads through | `buffer.c/h`, `chunk.h` | Sol (OpenAI) | Neon (Google) | Astra |
| 2 | `utf8` | UTF-8 iterate / encode / validate-and-repair, character classes, case folding; generated data tables | `utf8.c/h`, `case_fold.inc` | Neon (Google) | Sol (OpenAI) | Carbon |
| 3 | `node` | The document tree: node store, node fields, tree surgery, the enter/exit iterator, text consolidation | `node.c/h`, `iterator.c/h` | Sol (OpenAI) | Astra (OpenAI) | Neon |
| 4 | `references` | Link reference definitions: label normalisation, store, lookup | `references.c/h` | Neon (Google) | Sol (OpenAI) | Carbon |
| 5 | `blocks` | Block structure: line feeding, open/close matching, leaf content, reference-definition extraction | `blocks.c`, `parser.h`, the block scanners in `scanners.re` | Astra (OpenAI) | Neon (Google) | Neon |
| 6 | `inlines` | Inline structure within block content: text, code spans, emphasis, links and images, autolinks, raw HTML, entities, smart punctuation | `inlines.c`, the inline scanners in `scanners.re` | Carbon (Google) | Sol (OpenAI) | Neon |
| 7 | `html` | The HTML renderer, including the escaping rules | `html.c`, `render.c/h`, `houdini_html_e.c`, `houdini_href_e.c`, `houdini_html_u.c`, `entities.inc` | Neon (Google) | Astra (OpenAI) | Muse (manager) |
| 8 | `driver` | The program: options, input, parse → render, output, the one `failsafe` | `main.c`, `cmark.c` | Muse (manager) | Neon (Google) | — (the spec runner) |
| — | `tests/` | The spec runner and the per-section score keeping | cmark's `test/spec.txt` | Muse (manager) | management | — |

Rules that apply to every part (from the guide):

- The writer works in `src/<part>/`, codes to INTERFACES.md, builds and runs everything at -O0 and -O2, and records the compiler commit and npkc's sha256 in each test log.
- **The team that uses a part writes the tests for it**, in `tests/seams/<part>/`, from the contract alone — never from the part's source. The table's last column names who; nobody tests their own part.
- The reviewer is from a different company than the writer where the table allows, re-runs the part's tests, and reads the code against the contract and the cmark reference.
- Expected output is always the spec's expected HTML or cmark's own output on the same input — never the port's output.

## Order and milestones

1. **This plan and the contract** — pull request with only `PLAN.md` and `INTERFACES.md`; management reviews before any part is written. Once merged, the contract is frozen; a change goes through the manager as its own pull request naming the parts it affects.
2. **Foundations:** `buffer` and `utf8` in parallel (no dependencies between them).
3. **Tree:** `node` (depends on `buffer`), then `references` (depends on `buffer`, `utf8`).
4. **Parsers:** `blocks` (depends on `node`, `references`, `utf8`), then `inlines` (depends on `node`, `references`, `utf8`, `buffer`).
5. **Output:** `html` (depends on `node`, `utf8`), then `driver` (depends on all).
6. **The whole:** the spec runner over all 652 examples, pass counts recorded per spec section in `tests/RESULTS.md`; inputs beyond the spec compared against cmark 0.31.2's own output.
7. **Final pull request** to `main` from `work/commonmark`, per `WORKFLOW.md`, with a "Compiler notes" section (see NOTES.md below). A half-done converter is acceptable if the pull request says exactly what passes and what does not.

Each step ends in a commit with its tests, so a pause at any point loses nothing. The project runs on the plans' spare capacity and pauses whenever the compiler work needs those plans.

## Data tables

Two cmark data files are too large to port by hand and are not code: `case_fold.inc` (UTF-8 case folding, ~52 KB) and `entities.inc` (HTML entities, ~147 KB). Each owning part (`utf8`, `html`) generates a Nitpick data module from the tagged file with a small generator script kept beside it in the part's folder, naming the source file and tag in its header. The generated module is committed; the generator is how it is remade. Generated tables are data, credited to cmark under its licence like the rest of the port.

## Compiler faults

When something looks like a compiler fault: check `lab/context/known-issues.md` first and say whether it matches a known one. Cut it to the smallest program that shows it and record that program, the compiler commit, and expected-versus-actual in `NOTES.md` under "Compiler notes", and again in the pull request. Work around it in the port and keep going; management passes it to the compiler project from there.

## Licences and credit

- cmark is BSD-2-Clause (John MacFarlane and contributors). Every notice in cmark's `COPYING` is copied whole into `LICENSES/` before the first part lands.
- The CommonMark spec text (`spec/spec.txt`, copied from the tag's `test/spec.txt`) is CC-BY-SA 4.0, per its own header; its licence is kept with it.
- `commonmark/README.md` states that this is a port of cmark and credits its authors, and carries the per-part credits from the table above (writer and reviewer, by name and company), kept current as parts land. This repo is a personal side project that has not been through AILP's vetting, and the README stays in line with that.
