"""Hand-computed lengths from the tagged patterns; never sampled from the port.

Every scanner has positives, negatives and shared-prefix near misses. Offset,
empty, boundary, NUL and non-UTF-8 cases are added by check.py to every scanner.
"""
VECTORS = {
'atx_heading_start': [
    (b'# ',2), (b'######\t \ttext',9), (b'##\r\n',3), (b'###\n',4),
    (b'#',0), (b'####### ',0), (b'#x',0), (b'#\v',0), (b' # ',0)],
'setext_heading_line': [
    (b'=\n',2), (b'=== \t\r\n',6), (b'---\t\n',5), (b'-\r',2),
    (b'===',0), (b'-=\n',0), (b'-- x\n',0), (b'--\v\n',0)],
'open_code_fence': [
    (b'```\n',3), (b'```` lang\r\n',4), (b'~~~a`b\n',3), (b'~~~~~~\n',6),
    (b'```a`b\n',0), (b'```',0), (b'``\n',0), (b'```\x00\n',0), (b'~~~x',0)],
'close_code_fence': [
    (b'```\n',3), (b'~~~~ \t\r\n',4), (b'````\t\n',4),
    (b'~~~a\n',0), (b'```\v\n',0), (b'~~~',0), (b'~~\n',0), (b'```~\n',0)],
'html_block_start': [
    (b'<script>',8), (b'<PRE ',5), (b'<textarea\n',10), (b'<STYLE\t',7),
    (b'<!--',4), (b'<?',2), (b'<!D',3), (b'<![CDATA[',9), (b'<div>',5),
    (b'</DIV/>',7), (b'<search ',8), (b'<h1\r',4), (b'<title/>',8),
    (b'<script/>',0), (b'</script>',0), (b'<span>',0), (b'<division>',0),
    (b'<div',0), (b'<!1',0), (b'<![cdata[',0), (b'<stylex>',0)],
'html_block_start_7': [
    (b'<widget>\n',9), (b'</WIDGET> \t\r\n',12), (b'<x a="b">\n',10),
    (b'<x>\n \n!',6), (b'<x>\n x',4), (b'<x>\f\r',5),
    (b'<x>',0), (b'<x>text\n',0), (b'<x>\v\n',0), (b'<x a=>\n',0)],
'html_block_end_1': [
    (b'</pre>',6), (b'xx</SCRIPT>tail',11), (b'</pre>!</style>',15),
    (b'\r</textarea>',12), (b'\n</pre>',0), (b'</pre >',0),
    (b'</scripture>',0), (b'\x00</style>',0)],
'html_block_end_2': [
    (b'-->',3), (b'a-->x-->tail',8), (b'\r-->',4),
    (b'\n-->',0), (b'-- >',0), (b'--',0), (b'\x00-->',0)],
'html_block_end_3': [
    (b'?>',2), (b'a?>b?>tail',6), (b'\r?>',3),
    (b'\n?>',0), (b'? >',0), (b'?',0)],
'html_block_end_4': [
    (b'>',1), (b'a>b>tail',4), (b'\r>',2), (b'>\n>',1),
    (b'\n>',0), (b'\x00>',0), (b'abc',0)],
'html_block_end_5': [
    (b']]>',3), (b'a]]>b]]>tail',8), (b'\r]]>',4),
    (b'\n]]>',0), (b']] >',0), (b']]',0)],
'spacechars': [
    (b' \t\v\f\r\nx',6), (b'\r\n',2), (b' ',1),
    (b'x ',0), (b'\xc2\xa0',0), (b'\x00 ',0)],
'scheme': [
    (b'http:',5), (b'a+:x',3), (b'A.-0:',5), (b'a'*32+b':',33),
    (b'a'*33+b':',0), (b'a:',0), (b'1a:',0), (b'ab_:',0), (b'http',0)],
'autolink_uri': [
    (b'http:>',6), (b'HTTP:a/b?c>',11), (b'ab:\xff>',5),
    (b'ab:>tail',4), (b'a:>',0), (b'http:a b>',0), (b'http:<x>',0),
    (b'http:x',0), (b'ab:\x00>',0)],
'autolink_email': [
    (b'a@b>',4), (b'A.x+z@a-b.example>',18), (b'.!@0>',5), (b'a@'+b'b'*63+b'>',66),
    (b'a@'+b'b'*64+b'>',0), (b'@b>',0), (b'a@-b>',0), (b'a@b->',0),
    (b'a@b..c>',0), (b'a@b.>',0), (b'a@b',0), (b'a(b)@c>',0)],
'html_tag': [
    (b'a>',2), (b'a/>',3), (b'/Tag \n>',7), (b'X-y0 a b:c ="v" _x=one/>',24),
    (b'a x=\'\'>',7), (b'a x=foo/>tail',9), (b'a x="a\nb">',10),
    (b'<a>',0), (b'1a>',0), (b'a',0), (b'a x=>',0), (b'a x="x>',0),
    (b'a x=`bad`>',0), (b'/a/>',0), (b'a / >',0), (b'a x\x00>',0)],
'html_comment': [
    (b'---->',5), (b'--hello-->',10), (b'--a-b-->',8), (b'--a--b-->',9),
    (b'--a\nb-->',8), (b'--->',0), (b'--x',0), (b'--a\x00-->',0),
    (b'<!--x-->',0), (b'--x-->tail',6)],
'html_pi': [
    (b'x?>',1), (b'?>',0), (b'abc',3), (b'>',1), (b'??>',3),
    (b'???',2), (b'a?',1), (b'?a?>',2), (b'\n?>',1), (b'\x00x',0)],
'html_declaration': [
    (b'DOCTYPE html>',12), (b'A',1), (b'a1!',3), (b'Z\n>',2),
    (b'a\x00x',1), (b'!A>',0), (b'1A>',0), (b'>',0)],
'html_cdata': [
    (b'CDATA[',6), (b'CDATA[x]]>',7), (b'CDATA[x]y]]>',9),
    (b'CDATA[]]]>',10), (b'CDATA[x]',7), (b'CDATA[x]]',7),
    (b'CDATA[x\x00z',7), (b'cdata[x',0), (b'CDATA',0), (b'![CDATA[',0)],
'link_title': [
    (b'""',2), (b"'title'",7), (b'(title)',7), (b'"a\nb"tail',5),
    (b'"a\\"b"',6), (b'"a\\"',4), (b'"a\\\\"b"',7), (b'(a\\(b)',6),
    (b'(a\\)b)',6), (b'(a(b))',0), (b'(a\x00)',0), (b'"title',0),
    (b'"a"b"',3), (b'"a\\"b',4), (b'()',2)],
'dangerous_url': [
    (b'javascript:x',11), (b'VbScRiPt:',9), (b'FILE:',5), (b'DATA:',5),
    (b'data:image/png',0), (b'DATA:IMAGE/JPEG;base64',0), (b'data:image/webp-extra',0),
    (b'data:image/gif',0), (b'data:image/svg+xml',5), (b'data:image/jpg',5),
    (b'data:image/pn',5), (b'javascript',0), (b' javascript:',0), (b'https:',0)],
}
