"""Independent byte-regex oracle transcribed from cmark 0.31.2 scanners.re.

Source: https://github.com/commonmark/cmark/blob/0.31.2/src/scanners.re
BSD-2-Clause notices: ../../../LICENSES/COPYING.
Returns lengths per INTERFACES.md, including for cmark's classification scans.
This imports no implementation and never derives expectations from port output.
"""
import re

NAMES = '''atx_heading_start setext_heading_line open_code_fence close_code_fence
html_block_start html_block_start_7 html_block_end_1 html_block_end_2
html_block_end_3 html_block_end_4 html_block_end_5 spacechars scheme autolink_uri
autolink_email html_tag html_comment html_pi html_declaration html_cdata
link_title dangerous_url'''.split()

SPACE = rb'[ \t\v\f\r\n]'
TAGNAME = rb'[A-Za-z][A-Za-z0-9-]*'
BLOCK = (b'address|article|aside|base|basefont|blockquote|body|caption|center|col|'
         b'colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|'
         b'footer|form|frame|frameset|h1|h2|h3|h4|h5|h6|head|header|hr|html|'
         b'iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|'
         b'option|p|param|section|search|title|summary|table|tbody|td|tfoot|'
         b'th|thead|title|tr|track|ul')
ATTRNAME = rb'[a-zA-Z_:][a-zA-Z0-9:._-]*'
VALUE = rb'''(?:[^ \t\r\n\v\f"'=<>`\x00]+|'[^'\x00]*'|"[^"\x00]*")'''
ATTR = SPACE + rb'+' + ATTRNAME + rb'(?:' + SPACE + rb'*=' + SPACE + rb'*' + VALUE + rb')?'
OPEN = TAGNAME + rb'(?:' + ATTR + rb')*' + SPACE + rb'*/?>'
CLOSE = rb'/' + TAGNAME + SPACE + rb'*>'
TAG = rb'(?:' + OPEN + rb'|' + CLOSE + rb')'
SCHEME = rb'[A-Za-z][A-Za-z0-9.+-]{1,31}:'
ESCAPED = rb'''\\[!"#$%&'()*+,./:;<=>?@\[\\\]^_`{|}~\-]'''
PATTERNS = {
    'atx_heading_start': rb'#{1,6}(?:[ \t]+|[\r\n])',
    'setext_heading_line': rb'(?:=+|-+)[ \t]*[\r\n]',
    'html_block_start': (rb'(?:<(?i:script|pre|textarea|style)(?:' + SPACE + rb'|>)|'
                         rb'<!--|<\?|<![A-Za-z]|<!\[CDATA\[|</?(?i:' + BLOCK + rb')(?:' + SPACE + rb'|/?>))'),
    'html_block_start_7': rb'<' + TAG + rb'[\t\n\f ]*[\r\n]',
    'html_block_end_1': rb'[^\n\x00]*</(?i:script|pre|textarea|style)>',
    'html_block_end_2': rb'[^\n\x00]*-->',
    'html_block_end_3': rb'[^\n\x00]*\?>',
    'html_block_end_4': rb'[^\n\x00]*>',
    'html_block_end_5': rb'[^\n\x00]*\]\]>',
    'spacechars': SPACE + rb'+',
    'scheme': SCHEME,
    'autolink_uri': SCHEME + rb'[^\x00-\x20<>]*>',
    'autolink_email': (rb"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~\-]+@"
                       rb'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
                       rb'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*>'),
    'html_tag': TAG,
    'html_comment': rb'--(?:[^\x00-]|-[^\x00-]|--[^\x00>])*-->',
    'html_pi': rb'(?:[^?>\x00]|\?[^>\x00]|>)+',
    'html_declaration': rb'[A-Za-z]+[^>\x00]*',
    'html_cdata': rb'CDATA\[(?:[^\]\x00]|\][^\]\x00]|\]\][^>\x00])*',
    'link_title': (rb'(?:"(?:' + ESCAPED + rb'|[^"\x00])*"|'
                   rb"'(?:" + ESCAPED + rb"|[^'\x00])*'|"
                   rb'\((?:' + ESCAPED + rb'|[^()\x00])*\))'),
    'dangerous_url': rb'(?i:javascript:|vbscript:|file:|data:)',
}
# Flatten (class+|other)* to (class|other)* (and the +/+ form)
# without changing the language, avoiding exponential Python backtracking.
COMPILED = {name: re.compile(pat) for name, pat in PATTERNS.items()}
SAFE_DATA = re.compile(rb'(?i:data:image/(?:png|gif|jpeg|webp))')


def expected(name, base, at):
    if at < 0 or at > len(base):
        return 0
    data = base[at:]
    if name in ('open_code_fence', 'close_code_fence'):
        # Trailing context is checked but not included in the returned length.
        for n in range(len(data), 2, -1):
            if data[:n] not in (b'`' * n, b'~' * n):
                continue
            tail = (rb'[ \t]*[\r\n]' if name == 'close_code_fence' else
                    rb'[^`\r\n\x00]*[\r\n]' if data[0] == 96 else
                    rb'[^\r\n\x00]*[\r\n]')
            if re.match(tail, data[n:]):
                return n
        return 0
    if name == 'dangerous_url' and SAFE_DATA.match(data):
        return 0
    pat = COMPILED[name]
    # Explicit longest-prefix search implements re2c maximal munch independently
    # of the Nitpick scanners, including ambiguous escaped title delimiters.
    for n in range(len(data), 0, -1):
        if pat.fullmatch(data[:n]):
            return n
    return 0
