# Interfaces: the contract between the parts

Manager: Muse Wonder (Meta). This contract is frozen once the plan pull request merges; a change goes through the manager as its own pull request naming the parts it affects. Every part codes to this document, and every seam test is written from this document alone.

Signatures are written `name(param: Type, …) -> Return`. The notation:

- A plain parameter of an owning type is **lent**: the callee reads it, the caller keeps it, nothing is freed by the callee. (Nitpick's own rule for plain parameters.)
- `Type*` means **passed by address** (`@value` at the call, as the prelude's `list_push(@l, …)` does): the callee may mutate through it for the duration of the call and keeps nothing afterwards.
- `move Type` means the callee **takes ownership**; the caller writes `move(...)` and cannot use the value afterwards.
- A returned owning value is owned by the caller. **Nothing is ever returned lent** — a borrow that leaves the call is exactly what the Chunk convention below rules out.
- The language has no tuple types and no anonymous struct types: every multi-field value in this contract is a **named struct**, and every payload struct is named.
- Lengths, offsets and columns are `int64`, counted in **bytes**, everywhere. (cmark uses `int32_t` byte counts; the port widens them rather than juggling two widths.)

## Failure: which signatures can fail, and the one caller rule

Every Nitpick call returns a `Result` unless the callee is declared `never fails`, so every signature in this contract is marked one way or the other:

- `-> T never fails` — the function returns `T` directly; callers take it with `raw` where the language requires a spelling. Such a function may still *trap* (an overflow, a limit, an allocation failure on the trap route), as any code may; it never returns an error.
- `-> Result<T>` — the function can return an error. Anything that builds an owned value through a fallible call is here: `.clone()` returns a `Result` because allocation can fail (TRAITS §2.5), so every getter that clones a string out of the store returns a `Result`, and so does every builder that assembles strings through such calls.

**The one caller rule: relay the failure unchanged.** A function that calls a fallible function either handles the error itself (only the driver does, at the top) or relays it to its own caller unchanged — no renaming, no wrapping, no converting to a default. The error seam is the thing this project exists to exercise; a failure that arrives at the driver's `failsafe` should be the failure that occurred, with its identity intact.

**The parse itself is total.** Every byte string parses to some document, and every document renders; cmark has no parse errors and neither does the port. Failures reach the program only as returned errors on the routes above (allocation, through fallible library calls) or as traps, plus the driver's own IO error below.

No part contains a `main` or a `failsafe`, and no part defines error constants. The only error constant in the project is the driver's `InputError` (a file that cannot be read), which its `failsafe` maps to exit status 2.

**Strange failures are compiler notes first.** A crash, output that differs between -O0 and -O2, or output that changes from run to run is recorded under "Compiler notes" (NOTES.md and the pull request) as a possible compiler fault *before* anyone debugs the port around it. This design runs along the compiler's ownership roads on purpose; those notes are what the project is for.

## Shared conventions

**Text.** All text is bytes in Nitpick `string` values. Input is arbitrary bytes; nothing in the parse assumes valid UTF-8 except where the `utf8` part is asked. With the `validate_utf8` option, each fed line is passed through `utf8_check` (invalid sequences become U+FFFD) before parsing, as cmark does.

**Chunk — the borrowed view.** cmark passes `cmark_chunk` (a pointer and a length) everywhere. The port's equivalent is:

```
Chunk = { off: int64, len: int64 }
```

A `Chunk` is a byte range inside a `string` **base**. It is meaningless on its own: every function that takes a `Chunk` also takes its base as a lent `string` parameter, named `base` in this contract. A `Chunk` never outlives the call it is passed to, and no part stores one. Functions that need text beyond the call copy it into an owned `string` (see `chunk_to_string` in the `buffer` part). This convention is the port's answer to cmark's pointer views, and it is deliberate: it keeps every borrow inside one call, where the language checks it.

**Options.** One struct of plain data, passed by value:

```
Options = {
    sourcepos: bool,      // CMARK_OPT_SOURCEPOS — emit data-sourcepos attributes
    hardbreaks: bool,     // CMARK_OPT_HARDBREAKS — softbreak renders as <br />
    nobreaks: bool,       // CMARK_OPT_NOBREAKS — softbreak renders as a space
    unsafe: bool,         // CMARK_OPT_UNSAFE — render raw HTML and dangerous URLs
    validate_utf8: bool,  // CMARK_OPT_VALIDATE_UTF8
    smart: bool           // CMARK_OPT_SMART — smart punctuation in the inline parser
}
```

## The import graph (acyclic — it must stay that way)

```
cm_buffer   → (nothing)
cm_scan     → (nothing)
cm_utf8     → cm_buffer
cm_escape   → cm_buffer, cm_utf8
cm_refs     → cm_buffer, cm_utf8, cm_scan, cm_escape
cm_node     → cm_buffer, cm_refs
cm_blocks   → cm_buffer, cm_utf8, cm_scan, cm_node, cm_refs, cm_escape
cm_html     → cm_buffer, cm_utf8, cm_node, cm_escape
cm_inlines  → cm_buffer, cm_utf8, cm_scan, cm_node, cm_refs, cm_escape
cm_main     → every part
```

No part imports a part that imports it back. In particular, `cm_blocks` and `cm_inlines` never import each other: the scanners they share live in `cm_scan`, and reference-definition parsing lives in `cm_refs`, so the two parsers meet only through `cm_node`, `cm_refs`, `cm_scan` and `cm_escape`. The escaping and unescaping services live in `cm_escape`, low in the graph, because almost everyone needs them: `cm_refs` cleans each definition's URL and title through it (cmark's `cmark_reference_create` calls `cmark_clean_url` / `cmark_clean_title`), `cm_blocks` unescapes fenced code info strings through it, and `cm_inlines` cleans inline link destinations through it. (Cycles across files are near a known open fault — see `lab/context/known-issues.md` — apart from being poor structure.)

## Part 1 — `buffer` (module `cm_buffer`)

The growable byte buffer (cmark's `cmark_strbuf`) and the chunk helpers.

```
Buffer                                  // owning, move-only; starts empty
buffer_new() -> Result<Buffer>
buffer_put(buf: Buffer*, base: string, c: Chunk) -> Result<NIL>   // append the chunk's bytes
buffer_puts(buf: Buffer*, s: string) -> Result<NIL>               // append a whole string
buffer_putc(buf: Buffer*, b: int64) -> Result<NIL>                // append one byte (0–255)
buffer_len(buf: Buffer) -> int64 never fails
buffer_clear(buf: Buffer*) never fails                            // keep the buffer, drop the contents
buffer_detach(move buf: Buffer) -> string never fails             // hand out the contents; the buffer is consumed
chunk_of(base: string, off: int64, len: int64) -> Chunk never fails  // no copy; caller guarantees the range is inside base
chunk_all(base: string) -> Chunk never fails
chunk_to_string(base: string, c: Chunk) -> Result<string>         // an owned copy of the range
chunk_trim(base: string, c: Chunk) -> Chunk never fails           // narrow past spaces/tabs at both ends
chunk_eq(base: string, c: Chunk, other: string) -> bool never fails  // byte equality with an owned string
```

Ownership: a `Buffer` has exactly one owner at all times; `buffer_detach` is the only way text leaves it, and it consumes the buffer (cmark's detach leaves an empty buffer behind; consuming is the port's stricter spelling of the same hand-over, and callers that need another buffer make one).

## Part 2 — `utf8` (module `cm_utf8`)

Character-level services over bytes. All functions read a chunk of a lent base.

```
Utf8Char = { cp: int64, width: int64 }  // plain data: a decoded character and its byte width

utf8_iterate(base: string, c: Chunk, pos: int64) -> Utf8Char never fails
    // the character at byte offset pos inside the chunk; an invalid byte gives { 0xFFFD, 1 };
    // pos at or past the end of the chunk gives { 0, 0 }
utf8_encode(cp: int64, buf: Buffer*) -> Result<NIL>   // append cp as UTF-8; cp is a valid scalar or 0xFFFD
utf8_check(base: string, c: Chunk, buf: Buffer*) -> Result<NIL>
    // append the chunk with every invalid sequence replaced by U+FFFD
utf8_is_space(cp: int64) -> bool never fails          // cmark_utf8proc_is_space
utf8_is_punct(cp: int64) -> bool never fails          // cmark_utf8proc_is_punctuation_or_symbol
utf8_case_fold(base: string, c: Chunk, buf: Buffer*) -> Result<NIL>  // append the case-folded form
```

The case-fold and character-class tables are generated data (see PLAN.md, "Data tables"); the functions above are the only way other parts reach them.

## Part 3 — `escape` (module `cm_escape`)

Escaping, unescaping and cleaning (cmark's houdini files, `cmark_strbuf_unescape`, and the `clean_url` / `clean_title` pair from `inlines.c`). Low in the graph on purpose: the reference store, both parsers and the renderer all use it. The generated entity table lives here (see PLAN.md, "Data tables").

```
escape_html_into(buf: Buffer*, base: string, c: Chunk, secure: bool) -> Result<NIL>
    // append the chunk with & < > " escaped; secure also neutralises the
    // insecure characters cmark's houdini lists
escape_href_into(buf: Buffer*, base: string, c: Chunk) -> Result<NIL>
    // append the chunk percent-escaped as an href, per houdini_escape_href
unescape_entities_into(buf: Buffer*, base: string, c: Chunk) -> Result<NIL>
    // append the chunk with entity and numeric character references replaced
    // by their characters (houdini_unescape_html_f)
unescape_backslashes_into(buf: Buffer*, base: string, c: Chunk) -> Result<NIL>
    // append the chunk with backslash escapes resolved (cmark_strbuf_unescape):
    // a backslash before an ASCII punctuation character is dropped, any other
    // backslash is kept
clean_url(base: string, c: Chunk) -> Result<string>
    // cmark_clean_url: entity-unescape, backslash-unescape, trim — in cmark's order
clean_title(base: string, c: Chunk) -> Result<string>
    // cmark_clean_title: the same cleaning, for titles
```

## Part 4 — `scan` (module `cm_scan`)

The pattern scanners cmark generates from `scanners.re`, written by hand from the same patterns. Each scans a lent base from a byte position and returns the length matched, or 0 for no match. All are `never fails`. (cmark's take a chunk and an offset; the chunk convention makes the base explicit.)

```
scan_atx_heading_start(base: string, at: int64) -> int64 never fails
scan_setext_heading_line(base: string, at: int64) -> int64 never fails
scan_open_code_fence(base: string, at: int64) -> int64 never fails
scan_close_code_fence(base: string, at: int64) -> int64 never fails
scan_html_block_start(base: string, at: int64) -> int64 never fails
scan_html_block_start_7(base: string, at: int64) -> int64 never fails
scan_html_block_end_1 … scan_html_block_end_5(base: string, at: int64) -> int64 never fails
scan_spacechars(base: string, at: int64) -> int64 never fails
scan_scheme(base: string, at: int64) -> int64 never fails
scan_autolink_uri(base: string, at: int64) -> int64 never fails
scan_autolink_email(base: string, at: int64) -> int64 never fails
scan_html_tag(base: string, at: int64) -> int64 never fails
scan_html_comment(base: string, at: int64) -> int64 never fails
scan_html_pi(base: string, at: int64) -> int64 never fails
scan_html_declaration(base: string, at: int64) -> int64 never fails
scan_html_cdata(base: string, at: int64) -> int64 never fails
scan_link_title(base: string, at: int64) -> int64 never fails
scan_dangerous_url(base: string, at: int64) -> int64 never fails
```

## Part 5 — `node` (module `cm_node`)

The document tree. cmark links heap nodes with pointers; the port keeps every node in one store owned by the `Document`, and refers to nodes by index.

```
NodeRef = int64            // an index into the Document's store; NO_NODE = -1
Document = { … }           // owning; holds the node store, the root, and the RefMap (below)

NodeKind = enum {
    None, DocumentNode, BlockQuote, List, Item, CodeBlock, HtmlBlock, CustomBlock,
    Paragraph, Heading, ThematicBreak,
    Text, Softbreak, Linebreak, Code, HtmlInline, CustomInline,
    Emph, Strong, Link, Image
}
ListType = enum { Bullet, Ordered }

// The per-kind payloads, all named. The plain ones travel inside NodeInfo;
// the ones holding strings (LinkData, CustomData, and CodeData's info) are
// shapes only — their string fields cross this contract one at a time,
// through the getters and setters below, never inside a returned struct.
ListData    = { start: int64, list_type: ListType, delimiter: int64, bullet: int64,
                marker_offset: int64, padding: int64, tight: bool }        // plain
CodeData    = { info: string, fence_length: int64, fence_offset: int64,
                fence_char: int64, fenced: bool }                          // info is a string
HeadingData = { level: int64, setext: bool }                               // plain
LinkData    = { url: string, title: string }                               // strings
CustomData  = { on_enter: string, on_exit: string }                        // strings

// Everything about a node that is plain data, copyable, and cheap to hand out:
NodeInfo = {
    kind: NodeKind,
    parent, first_child, last_child, next, prev: NodeRef,
    start_line, start_column, end_line, end_column: int64,
    list: ListData,
    fence_length: int64, fence_offset: int64, fence_char: int64, fenced: bool,  // CodeData's plain fields
    heading: HeadingData,
    html_block_type: int64,
    open: bool, last_line_blank: bool, last_line_checked: bool   // block-parser working flags
}
```

Nodes are never removed from the store, so a `NodeRef` stays valid for the Document's whole life. Unlinking a node (consolidation does this) detaches it from its parent and siblings; the detached node remains in the store, unreachable from the root.

Reading a node is split the way the language requires: `node_info` hands out the plain data by copy, and each string a node holds is reached through its own getter (which clones, and so returns a `Result`) and setter (which takes the new string by `move`). There is no call that returns a whole node.

```
doc_new() -> Result<Document>              // an empty document: empty store, no root, empty RefMap
doc_set_refs(doc: Document*, move m: RefMap) never fails
    // install a filled map as the document's own, replacing the empty one.
    // parser_finish calls this (see cm_blocks) — the one step that moves the
    // parser's map into the document it hands over.
doc_root(doc: Document) -> NodeRef never fails
node_new(doc: Document*, kind: NodeKind) -> NodeRef never fails  // appended to the store, unattached, literal empty
node_info(doc: Document, n: NodeRef) -> NodeInfo never fails
node_literal(doc: Document, n: NodeRef) -> Result<string>        // a clone of the node's text ("" if none)
node_set_literal(doc: Document*, n: NodeRef, move s: string) never fails
node_code_info(doc: Document, n: NodeRef) -> Result<string>
node_set_code_info(doc: Document*, n: NodeRef, move s: string) never fails
node_link_url(doc: Document, n: NodeRef) -> Result<string>
node_link_title(doc: Document, n: NodeRef) -> Result<string>
node_set_link(doc: Document*, n: NodeRef, move url: string, move title: string) never fails
node_custom_on_enter(doc: Document, n: NodeRef) -> Result<string>
node_custom_on_exit(doc: Document, n: NodeRef) -> Result<string>
node_set_custom(doc: Document*, n: NodeRef, move on_enter: string, move on_exit: string) never fails
node_set_list(doc: Document*, n: NodeRef, d: ListData) never fails
node_set_code_fence(doc: Document*, n: NodeRef, fence_length: int64, fence_offset: int64,
                    fence_char: int64, fenced: bool) never fails
node_set_heading(doc: Document*, n: NodeRef, d: HeadingData) never fails
node_set_html_block_type(doc: Document*, n: NodeRef, t: int64) never fails
node_set_sourcepos(doc: Document*, n: NodeRef, start_line: int64, start_column: int64,
                   end_line: int64, end_column: int64) never fails
node_set_flags(doc: Document*, n: NodeRef, open: bool, last_line_blank: bool,
               last_line_checked: bool) never fails               // the blocks part's working flags
node_append_child(doc: Document*, parent: NodeRef, child: NodeRef) never fails  // detaches child from any siblings first
node_prepend_child(doc: Document*, parent: NodeRef, child: NodeRef) never fails
node_insert_before(doc: Document*, sibling: NodeRef, n: NodeRef) never fails
node_insert_after(doc: Document*, sibling: NodeRef, n: NodeRef) never fails
node_unlink(doc: Document*, n: NodeRef) never fails
node_replace(doc: Document*, target: NodeRef, replacement: NodeRef) never fails  // replacement takes target's place; target is unlinked
consolidate_text_nodes(doc: Document*, root: NodeRef) never fails  // merge adjacent Text siblings, as cmark_consolidate_text_nodes does
doc_ref_lookup(doc: Document, base: string, label: Chunk) -> Result<RefHit>   // see cm_refs for RefHit
```

The node's tree links change only through the surgery calls (`node_append_child` … `node_replace`); `NodeInfo`'s link fields are a read view, not a handle to write through. One exception to the walk rule below, by name: `consolidate_text_nodes` unlinks merged nodes, and it does not walk with the iterator — it traverses child lists directly, and it runs after `process_inlines` and before rendering, when no walk is in progress. The no-unlink rule binds walks, not it.

**Iterator.** The iterator is plain state — it holds no borrow. The document is passed to each step.

```
Iter = { root: NodeRef, current: NodeRef, … }   // plain state for one walk
Event = enum { Enter, Exit, Done }
Step = { event: Event, node: NodeRef }           // plain data

iter_new(root: NodeRef) -> Iter never fails
iter_next(doc: Document, it: Iter*) -> Step never fails
```

What a walk may do to the tree while it runs (cmark's rule): a walk may **add children to the node whose `Enter` event it has just been given, and edit that node's own fields** — `process_inlines` works exactly this way. It may not unlink, replace, or add siblings to any node, and it may not touch any other node's children. The renderer changes nothing.

Ownership: the `Document` owns every node and every string inside them. No other part frees, moves out of, or stores a node; parts hold `NodeRef` values freely (they are plain integers) and reach node contents only through the calls above, for as long as the `Document` lives. The driver owns the `Document` from `parser_finish` to the end of rendering.

## Part 6 — `references` (module `cm_refs`)

Link reference definitions, keyed by normalised label: case-folded (via `utf8_case_fold`), whitespace-collapsed, at most 1000 bytes of label (longer labels are not definitions and never match, per the spec).

```
RefMap                                   // owning
RefHit = { found: bool, url: string, title: string }   // owning, move-only (it holds strings)

refmap_new() -> Result<RefMap>
refmap_add(m: RefMap*, base: string, label: Chunk, raw_url_base: string, url: Chunk,
           raw_title_base: string, title: Chunk) -> Result<NIL>
    // cleans the URL through cm_escape's clean_url and the title through
    // clean_title before storing — cmark's cmark_reference_create does the same
    // cleaning at store time. The first definition of a label wins; a later one
    // is cleaned and dropped.
refmap_lookup(m: RefMap, base: string, label: Chunk) -> Result<RefHit>
    // url and title are owned clones — the map keeps its own copies, so what a
    // caller does with the results cannot reach them
RefParse = { consumed: int64 }           // plain data; consumed = 0 means "no definition here"
parse_ref_definition(m: RefMap*, base: string, c: Chunk) -> Result<RefParse>
    // cmark's parse_reference_inline, homed here so the block parser never imports
    // the inline parser: if the chunk begins with one or more reference definitions,
    // add each to the map and report the total bytes consumed; otherwise consume 0.
    // Uses cm_scan's scan_link_title and cm_utf8's case folding through this part.
```

## Part 7 — `blocks` (module `cm_blocks`)

The block parser. It owns the half-built `Document` — created empty by `parser_new` — and, to one side, the `RefMap` it is filling, until `parser_finish` hands the `Document` over.

```
Parser = { … }                            // owning
parser_new(opts: Options) -> Result<Parser>
parser_feed(p: Parser*, bytes: string) -> Result<NIL>
    // any byte count, any split; line endings (\n, \r\n, lone \r) are the parser's business.
    // While feeding, the parser adds reference definitions to its own map by calling
    // cm_refs' parse_ref_definition on the block content it assembles — field access
    // inside the owning part, not a borrow that leaves a call. When a fenced code
    // block closes, its info string is unescaped through cm_escape (entity and
    // backslash unescaping, as cmark's finalize step does) before it is stored
    // with node_set_code_info.
parser_finish(move p: Parser) -> Result<Document>
    // closes all open blocks, installs the parser's RefMap into the document
    // with doc_set_refs, and returns the document
```

Turning each leaf block's raw content into inline nodes is part 8, called by the driver between finish and render (below). The block's raw content reaches the inline part through `node_literal` (a clone, so a `Result` the inline part relays).

## Part 8 — `inlines` (module `cm_inlines`)

```
process_inlines(doc: Document*, opts: Options) -> Result<NIL>
    // walks the tree under the iterator's mutation rule; for every Paragraph and
    // Heading node, parses its stored content into inline child nodes (Text, Code,
    // Emph, Strong, Link, Image, breaks, HtmlInline, CustomInline), looking link
    // references up through doc_ref_lookup, cleaning inline link destinations and
    // titles through cm_escape, and using the buffer/utf8/scan services as the
    // import graph assigns them.
```

Emphasis, link and image construction follow cmark's `inlines.c`, including its delimiter-stack treatment of `*`/`_` and bracket stack for links.

## Part 9 — `html` (module `cm_html`)

The renderer. Escaping itself lives in `cm_escape` (part 3); the renderer calls it.

```
render_html(doc: Document, root: NodeRef, opts: Options) -> Result<string>
    // the whole document as HTML, owned by the caller
```

`render_html` walks with part 5's iterator and follows cmark's `html.c`, including: raw HTML is escaped unless `opts.unsafe`; dangerous URLs (`javascript:`, `vbscript:`, `file:`, and `data:` except image media types — `cm_scan`'s `scan_dangerous_url`) are replaced by the empty string unless `opts.unsafe`; `sourcepos` adds `data-sourcepos="l:c-l:c"` to block elements.

## Part 10 — `driver` (module `cm_main`)

The only executable part; the only `main` and `failsafe` in the project.

```
main: read all of stdin, or each named file in turn; convert; write HTML to stdout.
flags: --sourcepos --hardbreaks --nobreaks --unsafe --validate-utf8 --smart
```

The driver's pipeline per input, in the contract's own forms — also the project's definition of the whole conversion:

```
parser = parser_new(opts)?!
parser_feed(@parser, input)?!
document = parser_finish(move parser)?!
process_inlines(@document, opts)?!
consolidate_text_nodes(@document, doc_root(document))
html = render_html(document, doc_root(document), opts)?!
write html to stdout
```

Errors: a file that cannot be read fails with the driver's `InputError`, exit status 2, and a message on stderr naming the file. Every other failure arrives by relay from the parts and reaches the same `failsafe` unchanged. The driver states its full failsafe census in its own source, as every Nitpick program must.

## What this contract does not decide

Internal data structures inside a part (how `references` indexes its map, how `blocks` keeps its open-block stack, how `inlines` keeps its delimiter stack), the generated tables' internal layout, and each part's file layout under `src/<part>/` are the writer's, reviewed against cmark's behaviour. If a writer finds this contract cannot be implemented as written, they stop and raise it with the manager rather than deviating silently; the contract changes by pull request, not by drift.
