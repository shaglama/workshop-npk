# Interfaces: the contract between the parts

Manager: Muse Wonder (Meta). This contract is frozen once the plan pull request merges; a change goes through the manager as its own pull request naming the parts it affects. Every part codes to this document, and every seam test is written from this document alone.

Signatures are written `name(param: Type, …) -> Return`. The notation:

- A plain parameter of an owning type is **lent**: the callee reads it, the caller keeps it, nothing is freed by the callee. (Nitpick's own rule for plain parameters.)
- `Type*` means **passed by address** (`@value` at the call, as the prelude's `list_push(@l, …)` does): the callee may mutate through it for the duration of the call and keeps nothing afterwards.
- `move Type` means the callee **takes ownership**; the caller writes `move(...)` and cannot use the value afterwards.
- A returned owning value is owned by the caller.
- Lengths, offsets and columns are `int64`, counted in **bytes**, everywhere. (cmark uses `int32_t` byte counts; the port widens them rather than juggling two widths.)

## Shared conventions

**Text.** All text is bytes in Nitpick `string` values. Input is arbitrary bytes; nothing in the parse assumes valid UTF-8 except where the `utf8` part is asked. With the `validate_utf8` option, each fed line is passed through `utf8_check` (invalid sequences become U+FFFD) before parsing, as cmark does.

**Chunk — the borrowed view.** cmark passes `cmark_chunk` (a pointer and a length) everywhere. The port's equivalent is:

```
Chunk = { off: int64, len: int64 }
```

A `Chunk` is a byte range inside a `string` **base**. It is meaningless on its own: every function that takes a `Chunk` also takes its base as a lent `string` parameter, named `base` in this contract. A `Chunk` never outlives the call it is passed to, and no part stores one. Functions that need text beyond the call copy it into an owned `string` (see `chunk_to_string` in the `buffer` part). This convention is the port's answer to cmark's pointer views, and it is deliberate: it keeps every borrow inside one call, where the language checks it.

**Errors.** Parsing and rendering are **total**: every byte string parses to some document, and every document renders. No part returns a parse error, because cmark has none. Failures reach the program only through the language's own routes:

- allocation failure (`HeapOom` and its census companions) — traps to the driver's `failsafe`, as in any Nitpick program;
- file IO failure — the driver's own error, below.

No part contains a `main` or a `failsafe`, and no part defines error constants. A part's functions either cannot fail, or relay a failure upward unchanged; no part renames another part's error. The only error constant in the project is the driver's `InputError` (a file that cannot be read), which its `failsafe` maps to exit status 2.

**Options.** One struct, passed by value (it is plain data):

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

## Part 1 — `buffer` (module `cm_buffer`)

The growable byte buffer (cmark's `cmark_strbuf`) and the chunk helpers.

```
Buffer                                  // owning, move-only; starts empty
buffer_new() -> Buffer
buffer_put(buf: Buffer*, base: string, c: Chunk)        // append the chunk's bytes
buffer_puts(buf: Buffer*, s: string)                    // append a whole string
buffer_putc(buf: Buffer*, b: int64)                     // append one byte (0–255)
buffer_len(buf: Buffer) -> int64
buffer_clear(buf: Buffer*)                              // keep the buffer, drop the contents
buffer_detach(move buf: Buffer) -> string               // hand out the contents; the buffer is consumed
chunk_of(base: string, off: int64, len: int64) -> Chunk // no copy; the caller guarantees the range is inside base
chunk_all(base: string) -> Chunk
chunk_to_string(base: string, c: Chunk) -> string       // an owned copy of the range
chunk_trim(base: string, c: Chunk) -> Chunk             // narrow past spaces/tabs at both ends (cmark_isspace set)
chunk_eq(base: string, c: Chunk, other: string) -> bool // byte equality with an owned string
```

Ownership: a `Buffer` has exactly one owner at all times; `buffer_detach` is the only way text leaves it, and it consumes the buffer (cmark's detach leaves an empty buffer behind; consuming is the port's stricter spelling of the same hand-over, and callers that need another buffer make one).

## Part 2 — `utf8` (module `cm_utf8`)

Character-level services over bytes. All functions read a chunk of a lent base.

```
utf8_iterate(base: string, c: Chunk, pos: int64) -> (int64, int64)
    // decode the character at byte offset pos inside the chunk:
    // returns (codepoint, width in bytes). An invalid byte gives (0xFFFD, 1).
utf8_encode(cp: int64, buf: Buffer*)                    // append cp as UTF-8; cp is a valid scalar or 0xFFFD
utf8_check(base: string, c: Chunk, buf: Buffer*)        // append the chunk with every invalid sequence replaced by U+FFFD
utf8_is_space(cp: int64) -> bool                        // cmark_utf8proc_is_space
utf8_is_punct(cp: int64) -> bool                        // cmark_utf8proc_is_punctuation_or_symbol
utf8_case_fold(base: string, c: Chunk, buf: Buffer*)    // append the case-folded form (for reference labels)
```

The case-fold and character-class tables are generated data (see PLAN.md, "Data tables"); the functions above are the only way other parts reach them.

## Part 3 — `node` (module `cm_node`)

The document tree. cmark links heap nodes with pointers; the port keeps every node in one store owned by the `Document`, and refers to nodes by index.

```
NodeRef = int64            // an index into the Document's store; NO_NODE = -1
Document = { … }           // owning; holds the node store and the root

NodeKind = enum {
    None, Document, BlockQuote, List, Item, CodeBlock, HtmlBlock, CustomBlock,
    Paragraph, Heading, ThematicBreak,
    Text, Softbreak, Linebreak, Code, HtmlInline, CustomInline,
    Emph, Strong, Link, Image
}

Node = {
    kind: NodeKind,
    literal: string,                 // text content (Text, Code, Html*, CodeBlock body); empty otherwise
    parent, first_child, last_child, next, prev: NodeRef,
    start_line, start_column, end_line, end_column: int64,
    // per-kind payload, exactly one meaningful per kind:
    list:    { start: int64, list_type: ListType, delimiter: int64, bullet: int64,
               marker_offset: int64, padding: int64, tight: bool },
    code:    { info: string, fence_length: int64, fence_offset: int64, fence_char: int64, fenced: bool },
    heading: { level: int64, setext: bool },
    link:    { url: string, title: string },
    custom:  { on_enter: string, on_exit: string },
    html_block_type: int64,
    // block-parser working flags (blocks part only; other parts do not read them):
    open: bool, last_line_blank: bool, last_line_checked: bool
}
ListType = enum { Bullet, Ordered }
```

Nodes are never removed from the store, so a `NodeRef` stays valid for the Document's whole life. Unlinking a node (consolidation does this) detaches it from its parent and siblings; the detached node remains in the store, unreachable from the root.

```
doc_new() -> Document
doc_root(doc: Document) -> NodeRef
node_new(doc: Document*, kind: NodeKind) -> NodeRef     // appended to the store, unattached, literal empty
node_get(doc: Document, n: NodeRef) -> Node             // a copy of the node's plain fields;
                                                        // string fields are NOT copied out by this call —
                                                        // see node_literal / node_set_literal
node_kind(doc: Document, n: NodeRef) -> NodeKind
node_literal(doc: Document, n: NodeRef) -> string       // an owned clone of the literal ("" if none)
node_set_literal(doc: Document*, n: NodeRef, move s: string)
node_parent / node_first_child / node_last_child / node_next / node_prev
    (doc: Document, n: NodeRef) -> NodeRef
node_append_child(doc: Document*, parent: NodeRef, child: NodeRef)   // detach child from any siblings first
node_prepend_child(doc: Document*, parent: NodeRef, child: NodeRef)
node_insert_before(doc: Document*, sibling: NodeRef, n: NodeRef)
node_insert_after(doc: Document*, sibling: NodeRef, n: NodeRef)
node_unlink(doc: Document*, n: NodeRef)
node_replace(doc: Document*, old: NodeRef, new: NodeRef)             // new takes old's place; old is unlinked
node_set_link(doc: Document*, n: NodeRef, move url: string, move title: string)
    // …and the matching field setters for the list/code/heading/custom payloads,
    //    one per payload, same shape: plain fields by value, strings by move.
consolidate_text_nodes(doc: Document*, root: NodeRef)
    // merge adjacent Text siblings, as cmark_consolidate_text_nodes does
```

**Iterator** (the renderer's and inline part's way of walking):

```
Iter = { … }                       // a walk in progress over a lent Document
iter_new(doc: Document, root: NodeRef) -> Iter
iter_next(it: Iter*) -> (Event, NodeRef)   // Event = enum { Enter, Exit, Done }
```

Ownership: the `Document` owns every node and every string inside them. No other part frees, moves out of, or stores a node; parts hold `NodeRef` values freely (they are plain integers) and reach node contents only through the calls above, for as long as the `Document` lives. The driver owns the `Document` from `parser_finish` to the end of rendering.

## Part 4 — `references` (module `cm_refs`)

Link reference definitions, keyed by normalised label: case-folded (via `utf8_case_fold`), whitespace-collapsed, at most 1000 bytes of label (longer labels are not definitions and never match, per the spec).

```
RefMap                                   // owning
refmap_new() -> RefMap
refmap_add(m: RefMap*, base: string, label: Chunk, move url: string, move title: string)
    // the first definition of a label wins; a later one is dropped (the strings are consumed either way)
refmap_lookup(m: RefMap, base: string, label: Chunk) -> (bool, string, string)
    // (found, url, title); url and title are owned clones ("" when not found) —
    // the map keeps its own copies, so what a caller does with the results cannot reach them
```

## Part 5 — `blocks` (module `cm_blocks`)

The block parser. It owns the half-built `Document` and the `RefMap` until `parser_finish` hands the `Document` over.

```
Parser = { … }                            // owning
parser_new(opts: Options) -> Parser
parser_feed(p: Parser*, bytes: string)    // any byte count, any split; line endings
                                          // (\n, \r\n, lone \r) are the parser's business
parser_finish(move p: Parser) -> Document // closes all open blocks, extracts nothing
                                          // further; the RefMap is finished with
parser_refmap(p: Parser) -> RefMap        // lent read of the map being built, for the
                                          // inline part after finish — see below
```

The lifecycle seam, stated once: `parser_finish` consumes the `Parser`. The `Document` it returns carries the `RefMap` with it (the `Document` struct holds it), because the inline part needs the map after the block structure is final. So part 3's `Document` has one more field than the tree alone needs:

```
Document = { nodes: …, root: NodeRef, refs: RefMap }
```

and the inline part reads the map through `doc_refs(doc: Document) -> RefMap` (lent), in `cm_node`'s module. cmark keeps parser, tree and map as separate objects with one owner (the parser, then the caller); the port keeps the same single-owner shape by moving the map into the `Document` at finish.

Block parsing also finalises each leaf block's raw content; turning that content into inline nodes is part 6, called by the driver between finish and render (below).

## Part 6 — `inlines` (module `cm_inlines`)

```
process_inlines(doc: Document*, opts: Options)
    // walks the tree; for every Paragraph and Heading node, parses its stored
    // content into inline child nodes (Text, Code, Emph, Strong, Link, Image,
    // breaks, HtmlInline, CustomInline), using doc's RefMap for link references
    // and the buffer/utf8/html-escape services as INTERFACES assigns them.
```

The block's raw content reaches this part through `node_literal` (an owned clone); the inline children are built with part 3's calls. Emphasis, link and image construction follow cmark's `inlines.c`, including its delimiter-stack treatment of `*`/`_` and bracket stack for links.

## Scanners (owned by the parser parts, exported to each other)

cmark generates these from `scanners.re`; the port writes them by hand from the same patterns, one home each, callable by both parser parts. Each takes a base and a chunk-position and returns the length matched, or 0:

```
scan_atx_heading_start, scan_setext_heading_line, scan_open_code_fence,
scan_close_code_fence, scan_html_block_start, scan_html_block_start_7,
scan_html_block_end_1 … scan_html_block_end_5, scan_spacechars     // cm_blocks
scan_scheme, scan_autolink_uri, scan_autolink_email, scan_html_tag,
scan_html_comment, scan_html_pi, scan_html_declaration, scan_html_cdata,
scan_link_title, scan_dangerous_url                               // cm_inlines
```

Shape: `scan_x(base: string, at: int64) -> int64` — bytes matched starting at `at`, 0 for no match. (cmark's take a chunk and an offset; the port's chunk convention makes the base explicit.)

## Part 7 — `html` (module `cm_html`)

The renderer, and the escaping services (cmark's houdini files), which the inline part also uses.

```
render_html(doc: Document, root: NodeRef, opts: Options) -> string
    // the whole document as HTML, owned by the caller
escape_html_into(buf: Buffer*, base: string, c: Chunk, secure: bool)
    // append the chunk with & < > " (and ' handling per houdini) escaped;
    // secure also neutralises the insecure characters cmark lists
escape_href_into(buf: Buffer*, base: string, c: Chunk)
    // append the chunk percent-escaped as an href, per houdini_escape_href
unescape_entities_into(buf: Buffer*, base: string, c: Chunk)
    // append the chunk with entity and numeric character references replaced
    // by their characters (the entities.inc table, generated — see PLAN.md)
```

`render_html` walks with part 3's iterator and follows cmark's `html.c`, including: raw HTML is escaped unless `opts.unsafe`; dangerous URLs (`javascript:`, `vbscript:`, `file:`, and `data:` except image media types) are replaced by the empty string unless `opts.unsafe`; `sourcepos` adds `data-sourcepos="l:c-l:c"` to block elements.

## Part 8 — `driver` (module `cm_main`)

The only executable part; the only `main` and `failsafe` in the project.

```
main: read all of stdin, or each named file in turn; convert; write HTML to stdout.
flags: --sourcepos --hardbreaks --nobreaks --unsafe --validate-utf8 --smart
```

The driver's pipeline per input, which is also the project's definition of the whole conversion:

```
Parser = parser_new(opts)
parser_feed(parser, input)            // once, with the whole input
Document = parser_finish(parser)      // the Document owns the RefMap now
process_inlines(document, opts)
consolidate_text_nodes(document, root)   // cmark calls this in finish; the port calls it here, after inlines
html = render_html(document, root, opts)
write html to stdout
```

Errors: a file that cannot be read fails with the driver's `InputError`, exit status 2, and a message on stderr naming the file. Allocation failures trap to the same `failsafe` with the language's own exit scheme for those errors. The driver states its full failsafe census in its own source, as every Nitpick program must.

## What this contract does not decide

Internal data structures inside a part (how `references` indexes its map, how `blocks` keeps its open-block stack, how `inlines` keeps its delimiter stack), the generated tables' internal layout, and each part's file layout under `src/<part>/` are the writer's, reviewed against cmark's behaviour. If a writer finds this contract cannot be implemented as written, they stop and raise it with the manager rather than deviating silently; the contract changes by pull request, not by drift.
