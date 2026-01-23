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
from .codehilite import CodeHilite, CodeHiliteExtension, parseHlLines
from .attr_list import getAttrsAndRemainder, AttrListExtension
from ..util import parseBoolValue
from ..serializers import _escapeAttribHtml
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
        self.checkedForDeps = False
        self.codehiliteConf: dict[str, Any] = {}
        self.useAttrList = False
        # List of options to convert to boolean values
        self.boolOptions = [
            'linenums',
            'guess_lang',
            'noclasses',
            'use_pygments'
        ]

    def run(self, lines: list[str]) -> list[str]:
        """ Match and store Fenced Code Blocks in the `HtmlStash`. """

        # Check for dependent extensions
        if not self.checkedForDeps:
            for ext in self.md.registeredExtensions:
                if isinstance(ext, CodeHiliteExtension):
                    self.codehiliteConf = ext.getConfigs()
                if isinstance(ext, AttrListExtension):
                    self.useAttrList = True

            self.checkedForDeps = True

        text = "\n".join(lines)
        index = 0
        while 1:
            m = self.FENCED_BLOCK_RE.search(text, index)
            if m:
                lang, id, classes, config = None, '', [], {}
                if m.group('attrs'):
                    attrs, remainder = getAttrsAndRemainder(m.group('attrs'))
                    if remainder:  # Does not have correctly matching curly braces, so the syntax is invalid.
                        index = m.end('attrs')  # Explicitly skip over this, to prevent an infinite loop.
                        continue
                    id, classes, config = self.handleAttrs(attrs)
                    if len(classes):
                        lang = classes.pop(0)
                else:
                    if m.group('lang'):
                        lang = m.group('lang')
                    if m.group('hl_lines'):
                        # Support `hl_lines` outside of `attrs` for backward-compatibility
                        config['hl_lines'] = parseHlLines(m.group('hl_lines'))

                # If `config` is not empty, then the `codehighlite` extension
                # is enabled, so we call it to highlight the code
                if self.codehiliteConf and self.codehiliteConf['use_pygments'] and config.get('use_pygments', True):
                    localConfig = self.codehiliteConf.copy()
                    localConfig.update(config)
                    # Combine classes with `cssclass`. Ensure `cssclass` is at end
                    # as Pygments appends a suffix under certain circumstances.
                    # Ignore ID as Pygments does not offer an option to set it.
                    if classes:
                        localConfig['css_class'] = '{} {}'.format(
                            ' '.join(classes),
                            localConfig['css_class']
                        )
                    highliter = CodeHilite(
                        m.group('code'),
                        lang=lang,
                        style=localConfig.pop('pygments_style', 'default'),
                        **localConfig
                    )

                    code = highliter.hilite(shebang=False)
                else:
                    idAttr = langAttr = classAttr = kvPairs = ''
                    if lang:
                        prefix = self.config.get('lang_prefix', 'language-')
                        langAttr = f' class="{prefix}{_escapeAttribHtml(lang)}"'
                    if classes:
                        classAttr = f' class="{_escapeAttribHtml(" ".join(classes))}"'
                    if id:
                        idAttr = f' id="{_escapeAttribHtml(id)}"'
                    if self.useAttrList and config and not config.get('use_pygments', False):
                        # Only assign key/value pairs to code element if `attr_list` extension is enabled, key/value
                        # pairs were defined on the code block, and the `use_pygments` key was not set to `True`. The
                        # `use_pygments` key could be either set to `False` or not defined. It is omitted from output.
                        kvPairs = ''.join(
                            f' {k}="{_escapeAttribHtml(v)}"' for k, v in config.items() if k != 'use_pygments'
                        )
                    code = self._escape(m.group('code'))
                    code = f'<pre{idAttr}{classAttr}><code{langAttr}{kvPairs}>{code}</code></pre>'

                placeholder = self.md.htmlStash.store(code)
                text = f'{text[:m.start()]}\n{placeholder}\n{text[m.end():]}'
                # Continue from after the replaced text in the next iteration.
                index = m.start() + 1 + len(placeholder)
            else:
                break
        return text.split("\n")

    def handleAttrs(self, attrs: Iterable[tuple[str, str]]) -> tuple[str, list[str], dict[str, Any]]:
        """ Return tuple: `(id, [list, of, classes], {configs})` """
        id = ''
        classes = []
        configs = {}
        for k, v in attrs:
            if k == 'id':
                id = v
            elif k == '.':
                classes.append(v)
            elif k == 'hl_lines':
                configs[k] = parseHlLines(v)
            elif k in self.boolOptions:
                configs[k] = parseBoolValue(v, failOnErrors=False, preserveNone=True)
            else:
                configs[k] = v
        return id, classes, configs

    def _escape(self, txt: str) -> str:
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt


def makeExtension(**kwargs):  # pragma: no cover
    return FencedCodeExtension(**kwargs)
