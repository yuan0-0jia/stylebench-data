# Fenced Code Extension for Python Markdown
# =========================================

# This extension adds Fenced Code Blocks to Python-Markdown.

# See https://Python-Markdown.github.io/extensions/fenced_code_blocks
# for documentation.

# Original code Copyright 2007-2008 [Waylan Limberg](https://github.com/waylan).

# All changes Copyright 2008-2014 The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""
This extension adds Fenced Code Blocks to Python-Markdown.

See the [documentation](https://Python-Markdown.github.io/extensions/fenced_code_blocks)
for details.
"""

from __future__ import annotations

from textwrap import dedent
from . import Extension
from ..preprocessors import Preprocessor
from .codehilite import CodeHilite, CodeHiliteExtension, parse_hl_lines
from .attr_list import get_attrs_and_remainder, AttrListExtension
from ..util import parseBoolValue
from ..serializers import _escape_attrib_html
import re
from typing import TYPE_CHECKING, Any, Iterable

if TYPE_CHECKING:  # pragma: no cover
    from markdown import Markdown


class FencedCodeExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            'lang_prefix': ['language-', 'Prefix prepended to the language. Default: "language-"']
        }
        """ Default configuration options. """
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        """ Add `FencedBlockPreprocessor` to the Markdown instance. """
        md.registerExtension(self)

        md.preprocessors.register(FencedBlockPreprocessor(md, self.getConfigs()), 'fenced_code_block', 25)


class FencedBlockPreprocessor(Preprocessor):
    """ Find and extract fenced code blocks. """

    FENCED_BLOCK_RE = re.compile(
        dedent(r'''
            (?P<fence>^(?:~{3,}|`{3,}))[ ]*                          # opening fence
            ((\{(?P<attrs>[^\n]*)\})|                                # (optional {attrs} or
            (\.?(?P<lang>[\w#.+-]*)[ ]*)?                            # optional (.)lang
            (hl_lines=(?P<quot>"|')(?P<hl_lines>.*?)(?P=quot)[ ]*)?) # optional hl_lines)
            \n                                                       # newline (end of opening fence)
            (?P<code>.*?)(?<=\n)                                     # the code block
            (?P=fence)[ ]*$                                          # closing fence
        '''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )

    def __init__(self, md: Markdown, config: dict[str, Any]):
        super().__init__(md)
        self.config = config
        self.checked_for_deps = False
        self.codehilite_conf: dict[str, Any] = {}
        self.use_attr_list = False
        # List of options to convert to boolean values
        self.bool_options = [
            'linenums',
            'guess_lang',
            'noclasses',
            'use_pygments'
        ]

    def run(self, lines: list[str]) -> list[str]:
        """ Match and store Fenced Code Blocks in the `HtmlStash`. """

        # Check for dependent extensions
        if not self.checked_for_deps:
            for c in self.md.registeredExtensions:
                if isinstance(c, CodeHiliteExtension):
                    self.codehilite_conf = c.getConfigs()
                if isinstance(c, AttrListExtension):
                    self.use_attr_list = True

            self.checked_for_deps = True

        o = "\n".join(lines)
        f = 0
        while 1:
            m = self.FENCED_BLOCK_RE.search(o, f)
            if m:
                h, id, classes, config = None, '', [], {}
                if m.group('attrs'):
                    attrs, remainder = get_attrs_and_remainder(m.group('attrs'))
                    if remainder:  # Does not have correctly matching curly braces, so the syntax is invalid.
                        f = m.end('attrs')  # Explicitly skip over this, to prevent an infinite loop.
                        continue
                    id, classes, config = self.handle_attrs(attrs)
                    if len(classes):
                        h = classes.pop(0)
                else:
                    if m.group('lang'):
                        h = m.group('lang')
                    if m.group('hl_lines'):
                        # Support `hl_lines` outside of `attrs` for backward-compatibility
                        config['hl_lines'] = parse_hl_lines(m.group('hl_lines'))

                # If `config` is not empty, then the `codehighlite` extension
                # is enabled, so we call it to highlight the code
                if self.codehilite_conf and self.codehilite_conf['use_pygments'] and config.get('use_pygments', True):
                    j = self.codehilite_conf.copy()
                    j.update(config)
                    # Combine classes with `cssclass`. Ensure `cssclass` is at end
                    # as Pygments appends a suffix under certain circumstances.
                    # Ignore ID as Pygments does not offer an option to set it.
                    if classes:
                        j['css_class'] = '{} {}'.format(
                            ' '.join(classes),
                            j['css_class']
                        )
                    d = CodeHilite(
                        m.group('code'),
                        lang=h,
                        style=j.pop('pygments_style', 'default'),
                        **j
                    )

                    b = d.hilite(shebang=False)
                else:
                    e = i = a = g = ''
                    if h:
                        n = self.config.get('lang_prefix', 'language-')
                        i = f' class="{n}{_escape_attrib_html(h)}"'
                    if classes:
                        a = f' class="{_escape_attrib_html(" ".join(classes))}"'
                    if id:
                        e = f' id="{_escape_attrib_html(id)}"'
                    if self.use_attr_list and config and not config.get('use_pygments', False):
                        # Only assign key/value pairs to code element if `attr_list` extension is enabled, key/value
                        # pairs were defined on the code block, and the `use_pygments` key was not set to `True`. The
                        # `use_pygments` key could be either set to `False` or not defined. It is omitted from output.
                        g = ''.join(
                            f' {k}="{_escape_attrib_html(v)}"' for k, v in config.items() if k != 'use_pygments'
                        )
                    b = self._escape(m.group('code'))
                    b = f'<pre{e}{a}><code{i}{g}>{b}</code></pre>'

                l = self.md.htmlStash.store(b)
                o = f'{o[:m.start()]}\n{l}\n{o[m.end():]}'
                # Continue from after the replaced text in the next iteration.
                f = m.start() + 1 + len(l)
            else:
                break
        return o.split("\n")

    def handle_attrs(self, attrs: Iterable[tuple[str, str]]) -> tuple[str, list[str], dict[str, Any]]:
        """ Return tuple: `(id, [list, of, classes], {configs})` """
        id = ''
        a = []
        b = {}
        for k, v in attrs:
            if k == 'id':
                id = v
            elif k == '.':
                a.append(v)
            elif k == 'hl_lines':
                b[k] = parse_hl_lines(v)
            elif k in self.bool_options:
                b[k] = parseBoolValue(v, fail_on_errors=False, preserve_none=True)
            else:
                b[k] = v
        return id, a, b

    def _escape(self, txt: str) -> str:
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt


def makeExtension(**kwargs):  # pragma: no cover
    return FencedCodeExtension(**kwargs)
