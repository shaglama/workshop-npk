"""Generates scan_seam.npk from the case tables below (run: python3 gen.py).

Written by Sonnet (Claude Sonnet 5.5, Anthropic) from INTERFACES.md Part 4, cmark's
scanners.re patterns as the contract names them, and the CommonMark 0.31.2 spec.
The part's source was not read. Every case is run twice by the harness: at offset 0,
and at offset 3 of the same text behind a "xyz" prefix (scanners must not look back).
"""
from pathlib import Path

ID = {"atx": 1, "setext": 2, "open": 3, "close": 4, "hbs": 5, "hbs7": 6,
      "end1": 7, "end2": 8, "end3": 9, "end4": 10, "end5": 11, "space": 12,
      "scheme": 13, "uri": 14, "email": 15, "tag": 16, "comment": 17, "pi": 18,
      "decl": 19, "cdata": 20, "title": 21, "danger": 22}
FUNC = {"atx": "scan_atx_heading_start", "setext": "scan_setext_heading_line",
        "open": "scan_open_code_fence", "close": "scan_close_code_fence",
        "hbs": "scan_html_block_start", "hbs7": "scan_html_block_start_7",
        "end1": "scan_html_block_end_1", "end2": "scan_html_block_end_2",
        "end3": "scan_html_block_end_3", "end4": "scan_html_block_end_4",
        "end5": "scan_html_block_end_5", "space": "scan_spacechars",
        "scheme": "scan_scheme", "uri": "scan_autolink_uri",
        "email": "scan_autolink_email", "tag": "scan_html_tag",
        "comment": "scan_html_comment", "pi": "scan_html_pi",
        "decl": "scan_html_declaration", "cdata": "scan_html_cdata",
        "title": "scan_link_title", "danger": "scan_dangerous_url"}

A63, A64 = "a" * 63, "a" * 64
FULL = None  # want = the whole string's byte length

BLOCK_TAGS = """address article aside base basefont blockquote body caption center col
colgroup dd details dialog dir div dl dt fieldset figcaption figure footer form frame
frameset h1 h2 h3 h4 h5 h6 head header hr html iframe legend li link main menu menuitem
nav noframes ol optgroup option p param search section summary table tbody td tfoot th
thead title tr track ul""".split()

G = {}  # group name -> (exit code, description, [(scanner, text, want)])

def group(code, desc, cases):
    G[code] = (desc, cases)

group(11, "atx heading start: 1-6 hashes then space/tab run or one line end", [
    ("atx", s, w) for s, w in [
        ("# a", 2), ("## a", 3), ("### a", 4), ("#### a", 5), ("##### a", 6), ("###### a", 7),
        ("####### a", 0), ("#", 0), ("#a", 0), ("#\n", 2), ("#\r", 2), ("#\r\n", 2),
        ("#\t a", 3), ("#  \t x", 5), ("## \n", 3), (" # a", 0), ("\\# a", 0), ("", 0),
        ("# ", 2), ("#   ", 4), ("#\u000ba", 0), ("#\u00a0a", 0), ("#hashtag", 0),
        ("##\nx", 3), ("###### \n", 7)]])

group(12, "setext heading line: a run of = or - , spaces/tabs, one line end; length includes the line end", [
    ("setext", s, w) for s, w in [
        ("=\n", 2), ("===\n", 4), ("=== \n", 5), ("=\t\n", 3), ("==", 0), ("== x\n", 0),
        ("=-\n", 0), ("-\n", 2), ("---\n", 4), ("--- \n", 5), ("-\r", 2), ("-\r\n", 2),
        ("==\r\n", 3), ("\n", 0), (" ===\n", 0), ("= =\n", 0), ("---", 0), ("- - -\n", 0),
        ("-=\n", 0), ("", 0), ("=====  \t \nnext", 10)]])

group(13, "open code fence: 3+ backticks or tildes; length is the fence only; line end required after the info", [
    ("open", s, w) for s, w in [
        ("```\n", 3), ("~~~\n", 3), ("````\n", 4), ("~~~~~~~\n", 7), ("``\n", 0), ("~~\n", 0),
        ("```js\n", 3), ("``` js x\n", 3), ("```a`b\n", 0), ("```a~b\n", 3), ("~~~a`b\n", 3),
        ("~~~a~b\n", 3), ("``` \n", 3), ("```", 0), ("```x", 0), ("``` `\n", 0), ("~~~ ~\n", 3),
        ("```\r\n", 3), ("```\r", 3), ("``~\n", 0), (" ```\n", 0), ("`~`\n", 0), ("~`~\n", 0),
        ("```~~~\n", 3), ("", 0)]])

group(14, "close code fence: 3+ backticks or tildes, then only spaces/tabs up to a line end", [
    ("close", s, w) for s, w in [
        ("```\n", 3), ("```  \t\n", 3), ("``` x\n", 0), ("~~~~\n", 4), ("~~\n", 0), ("```", 0),
        ("``` \r\n", 3), ("``` ~\n", 0), ("```` \n", 4), ("```a\n", 0), ("~~~\r", 3),
        ("``\n", 0), ("", 0)]])

hbs_cases = [
    ("<script>", 8), ("<SCRIPT\n", 8), ("<pre ", 5), ("<Textarea>", 10), ("<style\t", 7),
    ("<script", 0), ("<scripts>", 0), ("<!--", 4), ("<!-- x", 4), ("<?", 2), ("<?php", 2),
    ("<!A", 3), ("<!1", 0), ("<![CDATA[", 9), ("<![CDATA", 0), ("<!-", 0), ("<!>", 0),
    ("<div>", 5), ("<div ", 5), ("<div/>", 6), ("<div/", 0), ("<div\n", 5), ("</div>", 6),
    ("</DIV>", 6), ("<divx>", 0), ("<p>", 3), ("<p/>", 4), ("<hr />", 4), ("<hr/>", 5),
    ("<h7>", 0), ("<a>", 0), ("<span>", 0), ("<", 0), ("", 0), (" <div>", 0), ("<table\t", 7),
    ("<prefix>", 0), ("</script>", 0), ("</pre>", 0), ("<!DOCTYPE html>", 3), ("</", 0),
    ("<//>", 0), ("</ div>", 0), ("<div\u000cx", 5), ("<pre>", 5), ("<p\r", 3),
]
for t in BLOCK_TAGS:
    hbs_cases += [("<%s>" % t, len(t) + 2), ("<%s " % t, len(t) + 2), ("</%s>" % t, len(t) + 3),
                  ("<%s/>" % t, len(t) + 3), ("<%s>" % t.upper(), len(t) + 2),
                  ("<%szz>" % t, 0), ("</%szz>" % t, 0)]
group(15, "html block start (types 1-6): the length matched, not a type code; every spec tag name", [("hbs", s, w) for s, w in hbs_cases])

group(16, "html block start 7: a complete open/close tag then spaces and a line end; length includes the line end", [
    ("hbs7", s, w) for s, w in [
        ("<a>\n", 4), ("<a>  \n", 6), ("</a>\n", 5), ("<a/>\r\n", 5), ("<a>", 0), ("<a> x\n", 0),
        ("<a href=\"x\">\n", FULL), ("<a b='c'>\n", FULL), ("<a b>\n", FULL), ("<1>\n", 0),
        ("<a b=>\n", 0), ("</a b>\n", 0), ("<a\n b>\n", FULL), ("<!-- x -->\n", 0), ("<a>\t\u000c \n", 7),
        ("<a/>\n", 5), ("< a>\n", 0), ("<a", 0), ("", 0), ("<span class=\"x\">\n", FULL),
        ("<custom-tag>\n", FULL), ("<a>  x\n", 0)]])

group(17, "html block end 1-5: greedy to the last terminator on the line; never past a newline", [
    ("end1", s, w) for s, w in [
        ("</script>", 9), ("x</pre>y", 7), ("</STYLE>", 8), ("</textarea>", 11),
        ("abc</pre></style>z", 17), ("</scripts>", 0), ("</script", 0), ("\n</script>", 0),
        ("a\n</script>", 0), ("<script>", 0), ("</ script>", 0), ("", 0), ("</pre> </pre> x", 13)]
] + [
    ("end2", s, w) for s, w in [
        ("-->", 3), ("a-->", 4), ("a--> b -->", 10), ("-- >", 0), ("--\n-->", 0), ("->", 0),
        ("", 0), ("x\n-->", 0), ("<!-- c -->", 10)]
] + [
    ("end3", s, w) for s, w in [
        ("?>", 2), ("<?php ?>x", 8), (">", 0), ("?", 0), ("? >", 0), ("", 0), ("a?>b?>", 6), ("a\n?>", 0)]
] + [
    ("end4", s, w) for s, w in [
        (">", 1), ("a>", 2), ("a>b>", 4), ("abc", 0), ("\n>", 0), ("ab\n>", 0), ("", 0), ("<!DOCTYPE x>", 12)]
] + [
    ("end5", s, w) for s, w in [
        ("]]>", 3), ("a]]>", 4), ("]]", 0), ("]>", 0), ("a]]>b]]>c", 8), ("", 0), ("a\n]]>", 0)]])

group(18, "spacechars: the run of space, tab, VT, FF, CR, LF; 0 when none", [
    ("space", s, w) for s, w in [
        ("", 0), (" ", 1), ("  \t\n x", 5), ("\u000b\u000c\r", 3), ("x", 0), ("\u00a0", 0), ("a  b", 0),
        ("   ", 3), ("\n\n\nx", 3), ("\t", 1), (" x ", 1)]])

group(19, "scheme: a letter then 1-31 of letters, digits, + . - and a colon; length includes the colon", [
    ("scheme", s, w) for s, w in [
        ("http:", 5), ("HTTP:", 5), ("a:", 0), ("ab:", 3), ("a1:", 3), ("a+.-:", 5), ("a+b.c-d:", 8),
        ("1a:", 0), ("+a:", 0), ("ab", 0), ("ab c:", 0), ("http", 0), ("a" * 32 + ":", 33),
        ("a" * 33 + ":", 0), ("mailto:x", 7), ("a_b:", 0), (":", 0), ("", 0), ("http://x", 5),
        ("a" * 31 + ":", 32)]])

group(20, "autolink uri (scanned after the '<'): scheme, no space/control/</>, then '>'; length includes '>'", [
    ("uri", s, w) for s, w in [
        ("http://a.b>", 11), ("http:>", 6), ("a:b>", 0), ("ab:>", 4), ("http://a b>", 0),
        ("http://a<b>", 0), ("http://a>b>", 9), ("http://x\n>", 0), ("http://\u00fc>", 10),
        ("http://a\t>", 0), ("http://a", 0), ("mailto:a@b.c>", 13), ("irc://foo.bar:2233/baz>", FULL),
        ("foo@bar.example.com>", 0), ("x:y>", 0), ("", 0), (">", 0), ("http://a\u007fb>", 11),
        ("a" * 32 + ":x>", 35), ("a" * 33 + ":x>", 0)]])

group(21, "autolink email (scanned after the '<'): local part, @, hostname labels, '>'", [
    ("email", s, w) for s, w in [
        ("foo@bar.com>", 12), ("a@b>", 4), ("foo@bar>", 8), ("foo.bar+baz@ex-ample.org>", FULL),
        ("foo@-bar.com>", 0), ("foo@bar-.com>", 0), ("foo@bar..com>", 0), ("foo@.com>", 0),
        ("foo@bar.>", 0), ("@bar>", 0), ("foo@>", 0), ("foo\\@bar>", 0), ("foo@bar_baz>", 0),
        ("foo@bar.com", 0), ("foo@bar com>", 0), ("x@" + A63 + ">", FULL), ("x@" + A64 + ">", 0),
        ("x@a." + A63 + ">", FULL), ("x@a." + A64 + ">", 0), ("a!#$%&'*+/=?^_`{|}~-@b>", FULL),
        ("a,b@c>", 0), ("a b@c>", 0), ("a(b@c>", 0), ("a:b@c>", 0), ("a@b-c>", 6), ("a@b--c>", 7),
        ("a@b.c.d.e>", 10), ("", 0), ("a@b>c@d>", 4)]])

group(22, "html tag, open and close tags (scanned after the '<')", [
    ("tag", s, w) for s, w in [
        ("a>", 2), ("a b='c' d>", FULL), ("a/>", 3), ("a href=x>", FULL), ("a b = \"c\">", FULL),
        ("a b='c'd>", 0), ("a 1b>", 0), ("a b=>", 0), ("a b=c`d>", 0), ("a b=\"c>", 0),
        ("/a>", 3), ("/a >", 4), ("/a b>", 0), ("/>", 0), ("a-b>", 4), ("1a>", 0), ("a1-2>", 5),
        ("a\n b='c'\n>", FULL), ("A HREF=x>", FULL), ("a _b:c.d-e>", FULL), ("a b=c d=e>", FULL),
        ("a b='c' d=\"e\">", FULL), ("a b=\"c\"d=\"e\">", 0), ("a b=c'd>", 0), ("a b='c'>", FULL),
        ("a\tb\n=\nc>", FULL), ("a b=<>", 0), ("a b==c>", 0), ("a/ >", 0), ("a />", 4),
        ("a  / >", 0), ("a//>", 0), ("a>>", 2), ("a", 0), (">", 0), ("", 0), ("/a\n>", 4),
        ("/a/>", 0), ("/ a>", 0), ("//a>", 0), ("a b='c\nd'>", FULL), ("a b=\"c'd\">", FULL),
        ("a b='c\"d'>", FULL), ("a\u000bb>", 4), ("a b='c' >", FULL), ("a b='c'/>", FULL),
        ("a b=\"\">", FULL), ("a b=''>", FULL), ("a b=c/>", FULL), ("a rest x>", FULL),
        ("a b c>", FULL)]])

group(23, "html comment, processing instruction, declaration, cdata (scanned after the '<')", [
    ("comment", s, w) for s, w in [
        ("!---->", 6), ("!-->", 4), ("!--->", 5), ("!-- a -->", 9), ("!-- a --> b -->", 9),
        ("!--a", 0), ("!-- a --", 0), ("!--", 0), ("!-- a -- b -->", FULL), ("!-- \n multi\nline -->", FULL),
        ("!- x -->", 0), ("! -- x -->", 0), ("!--x-->", 7), ("", 0), ("!-- x --!>", 0)]
] + [
    ("pi", s, w) for s, w in [
        ("?php?>", 6), ("??>", 3), ("?>", 2), ("?a>b?>", 6), ("?x", 0), ("?x?", 0),
        ("? a ?> b ?>", 6), ("?a?b?>", 6), ("", 0), ("?a\n b ?>", FULL)]
] + [
    ("decl", s, w) for s, w in [
        ("!DOCTYPE html>", 14), ("!A b>", 5), ("!1 b>", 0), ("!DOCTYPE html", 0), ("!>", 0), ("", 0),
        ("!DOCTYPE html PUBLIC \"x\" \"y\">", FULL)]
] + [
    ("cdata", s, w) for s, w in [
        ("![CDATA[x]]>", 12), ("![CDATA[]]>", 11), ("![CDATA[a]]b]]>", FULL), ("![CDATA[x]]", 0),
        ("![CDATA[x", 0), ("![CDATA[a]]>b]]>", 12), ("![CDATA]]>", 0), ("", 0),
        ("![CDATA[ <b> & ] ]> ]]>", FULL), ("![CDATA[\nx\n]]>", FULL)]])

group(24, "link title: quoted by \" ' or ( ), escapes, ambiguous closers; length includes the delimiters", [
    ("title", s, w) for s, w in [
        ('"abc"', 5), ("'abc'", 5), ("(abc)", 5), ('""', 2), ("''", 2), ("()", 2),
        ('"a\\"b"', 6), ('"a\\"', 4), ("(a\\)b)", 6), ("(a\\)", 4), ("(a(b)", 0), ("(a)b)", 3),
        ('"a\nb"', 5), ('"abc', 0), ("abc", 0), ("'a\"b'", 5), ("\"a'b\"", 5), ('(a"b)', 5),
        ('"a"b"', 3), ("'it's'", 4), ('"\\\\"', 4), ('"x" trailing', 3), ('"a" "b"', 3),
        ('"a\\qb"', 6), ("", 0), ("'abc", 0), ("(abc", 0), ("(a\\(b)", 6), ('"\\""', 4), (" 'a'", 0),
        ("(a\n\nb)", FULL)]])

group(25, "dangerous url: javascript: vbscript: file: data: (not data:image/png|gif|jpeg|webp); length of the scheme and colon", [
    ("danger", s, w) for s, w in [
        ("javascript:alert(1)", 11), ("JAVASCRIPT:", 11), ("JaVaScRiPt:x", 11), ("vbscript:x", 9),
        ("file:///x", 5), ("data:text/html;base64,xx", 5), ("data:image/png;base64,x", 0),
        ("data:image/gif,", 0), ("data:image/jpeg,", 0), ("data:image/webp,", 0),
        ("DATA:IMAGE/PNG;x", 0), ("data:image/svg+xml,x", 5), ("data:image/bmp", 5), ("data:", 5),
        ("javascript", 0), ("javascript :x", 0), (" javascript:x", 0), ("http://x", 0),
        ("xjavascript:", 0), ("java\tscript:", 0), ("js:", 0), ("https://javascript:", 0), ("FILE:x", 5),
        ("mailto:x", 0), ("", 0), ("data:image/", 5), ("data:application/x", 5), ("data:image/jpg", 5),
        ("VBScript:", 9)]])

# group 26 is generated: every scanner at the end of its base and on an empty base
group(26, "every scanner: no match on an empty base and at the very end of a base", [
    (k, "", 0) for k in ID] + [(k, "abc", -1) for k in ID])

def lit(s):
    out = []
    for ch in s:
        o = ord(ch)
        if ch == '"': out.append('\\"')
        elif ch == "\\": out.append("\\\\")
        elif ch == "\n": out.append("\\n")
        elif ch == "\t": out.append("\\t")
        elif ch == "\r": out.append("\\r")
        elif 32 <= o < 127: out.append(ch)
        else: out.append("\\u{%x}" % o)
    return '"' + "".join(out) + '"'

def emit():
    L = []
    w = L.append
    w("// GENERATED by gen.py -- do not edit. Seam tests for cm_scan, by Sonnet (Anthropic),")
    w("// from INTERFACES.md Part 4 alone (plus scanners.re's patterns and the CommonMark spec).")
    w("// The part's source was not read.")
    w("mod:scan_seam;")
    w("")
    w('use "../../../src/buffer/cm_buffer.npk".*;')
    w('use "../../../src/scan/cm_scan.npk".*;')
    w("")
    w("func:run = int64(int64:id, string:s, int64:at) never fails {")
    for k, i in ID.items():
        w("    if (id == %di64) { pass raw %s(s, at); }" % (i, FUNC[k]))
    w("    pass -1i64;")
    w("};")
    w("")
    w("// one case at offset 0, and again at offset 3 behind a 'xyz' prefix (no look-behind)")
    w("func:chk = bool(int64:id, string:s, int64:want) {")
    w("    int64:a = raw run(id, s, 0i64);")
    w("    if (a != want) { pass false; }")
    w("    Buffer:buf = relay buffer_create();")
    w('    relay buffer_puts(@buf, "xyz");')
    w("    relay buffer_puts(@buf, s);")
    w("    string:p = raw buffer_detach(move(buf));")
    w("    int64:b = raw run(id, p, 3i64);")
    w("    pass b == want;")
    w("};")
    w("")
    for code, (desc, cases) in sorted(G.items()):
        w("// group %d: %s" % (code, desc))
        w("func:g%d = bool() {" % code)
        for k, s, want in cases:
            if code == 26 and want == -1:
                # end of base: scan at s.len must give 0
                w("    if (!(raw at_end(%di64, %s))) { pass false; }" % (ID[k], lit(s)))
                continue
            if want is None:
                want = len(s.encode())
            w("    if (!(relay chk(%di64, %s, %di64))) { pass false; }" % (ID[k], lit(s), want))
        w("    pass true;")
        w("};")
        w("")
    w("func:at_end = bool(int64:id, string:s) never fails {")
    w("    int64:r = raw run(id, s, s.len);")
    w("    pass r == 0i64;")
    w("};")
    w("")
    w("// CHECK_ALL_BEGIN")
    w("func:check_all = int32() {")
    for code in sorted(G):
        w("    if (!(relay g%d())) { pass %di32; }" % (code, code))
    w("    pass 0i32;")
    w("};")
    w("// CHECK_ALL_END")
    w("")
    w("func:main = int32(cstring[]:_~argv) {")
    w("    Result<int32>:outcome = check_all();")
    w("    if (outcome.is_error) { !!! outcome.err; }")
    w("    exit outcome.value;")
    w("};")
    w("")
    w("// Any returned error is forwarded here unchanged by main.")
    w("func:failsafe = int32(Error:err) {")
    w("    pick (err) {")
    w("        (Unreachable, HeapOom, HeapBadRequest, WildLeak, StackExhausted,")
    w("         MachineFault, DivByZero, DivOverflow, IntOverflow, OutOfBounds,")
    w("         DecreasesViolated) { exit 100i32; },")
    w("        (*) { exit 100i32; }")
    w("    }")
    w("};")
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    (here / "scan_seam.npk").write_text(emit())
    import json
    (here / "groups.json").write_text(json.dumps({str(c): d for c, (d, _) in sorted(G.items())}, indent=1))
    print("cases:", sum(len(c) for _, c in G.values()))
