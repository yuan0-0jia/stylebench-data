# CodeHilite Extension for Python-Markdown
# ========================================

# Adds code/syntax highlighting to standard Python-Markdown code blocks.

# See https://Python-Markdown.github.io/extensions/code_hilite
# for documentation.

# Original code Copyright 2006-2008 [Waylan Limberg](https://github.com/waylan).

# All changes Copyright 2008-2014 The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""
Adds code/syntax highlighting to standard Python-Markdown code blocks.

See the [documentation](https://Python-Markdown.github.io/extensions/code_hilite)
for details.
"""

from __future__ import annotations

from . import Extension
from ..treeprocessors import Treeprocessor
from ..util import parseBoolValue
from typing import TYPE_CHECKING, Callable, Any

if TYPE_CHECKING:  # pragma: no cover
    import xml.etree.ElementTree as etree

try:  # pragma: no cover
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import get_formatter_by_name
    from pygments.util import ClassNotFound
    pygments = True
except ImportError:  # pragma: no cover
    pygments = False


def parse_hl_lines(expr: str) -> list[int]:
    """Support our syntax for emphasizing certain lines of code.

    `expr` should be like '1 2' to emphasize lines 1 and 2 of a code block.
    Returns a list of integers, the line numbers to emphasize.
    """
    if not expr:
        return []

    try:
        return list(map(int, expr.split()))
    except ValueError:  # pragma: no cover
        return []


# ------------------ The Main CodeHilite Class ----------------------
class CodeHilite:
    """
    Determine language of source code, and pass it on to the Pygments highlighter.

    Usage:

    ```python
    code = CodeHilite(src=some_code, lang='python')
    html = code.hilite()
    ```

    Arguments:
        src: Source string or any object with a `.readline` attribute.

    Keyword arguments:
        lang (str): String name of Pygments lexer to use for highlighting. Default: `None`.
        guess_lang (bool): Auto-detect which lexer to use.
            Ignored if `lang` is set to a valid value. Default: `True`.
        use_pygments (bool): Pass code to Pygments for code highlighting. If `False`, the code is
            instead wrapped for highlighting by a JavaScript library. Default: `True`.
        pygments_formatter (str): The name of a Pygments formatter or a formatter class used for
            highlighting the code blocks. Default: `html`.
        linenums (bool): An alias to Pygments `linenos` formatter option. Default: `None`.
        css_class (str): An alias to Pygments `cssclass` formatter option. Default: 'codehilite'.
        lang_prefix (str): Prefix prepended to the language. Default: "language-".

    Other Options:

    Any other options are accepted and passed on to the lexer and formatter. Therefore,
    valid options include any options which are accepted by the `html` formatter or
    whichever lexer the code's language uses. Note that most lexers do not have any
    options. However, a few have very useful options, such as PHP's `startinline` option.
    Any invalid options are ignored without error.

    * **Formatter options**: <https://pygments.org/docs/formatters/#HtmlFormatter>
    * **Lexer Options**: <https://pygments.org/docs/lexers/>

    Additionally, when Pygments is enabled, the code's language is passed to the
    formatter as an extra option `lang_str`, whose value being `{lang_prefix}{lang}`.
    This option has no effect to the Pygments' builtin formatters.

    Advanced Usage:

    ```python
    code = CodeHilite(
        src = some_code,
        lang = 'php',
        startinline = True,      # Lexer option. Snippet does not start with `<?php`.
        linenostart = 42,        # Formatter option. Snippet starts on line 42.
        hl_lines = [45, 49, 50], # Formatter option. Highlight lines 45, 49, and 50.
        linenos = 'inline'       # Formatter option. Avoid alignment problems.
    )
    html = code.hilite()
    ```

    """

    def __init__(self, src: str, **options):
        self.src = src
        self.lang: str | None = options.pop('lang', None)
        self.guess_lang: bool = options.pop('guess_lang', True)
        self.use_pygments: bool = options.pop('use_pygments', True)
        self.lang_prefix: str = options.pop('lang_prefix', 'language-')
        self.pygments_formatter: str | Callable = options.pop('pygments_formatter', 'html')

        if 'linenos' not in options:
            options['linenos'] = options.pop('linenums', None)
        if 'cssclass' not in options:
            options['cssclass'] = options.pop('css_class', 'codehilite')
        if 'wrapcode' not in options:
            # Override Pygments default
            options['wrapcode'] = True
        # Disallow use of `full` option
        options['full'] = False

        self.options = options

    def hilite(self, shebang: bool = True) -> str:
        """
        Pass code to the [Pygments](https://pygments.org/) highlighter with
        optional line numbers. The output should then be styled with CSS to
        your liking. No styles are applied by default - only styling hooks
        (i.e.: `<span class="k">`).

        returns : A string of html.

        """

        self.src = self.src.strip('\n')

        if self.lang is None and shebang:
            self._parseHeader()

        if pygments and self.use_pygments:
            try:
                f = get_lexer_by_name(self.lang, **self.options)
            except ValueError:
                try:
                    if self.guess_lang:
                        f = guess_lexer(self.src, **self.options)
                    else:
                        f = get_lexer_by_name('text', **self.options)
                except ValueError:  # pragma: no cover
                    f = get_lexer_by_name('text', **self.options)
            if not self.lang:
                # Use the guessed lexer's language instead
                self.lang = f.aliases[0]
            e = f'{self.lang_prefix}{self.lang}'
            if isinstance(self.pygments_formatter, str):
                try:
                    d = get_formatter_by_name(self.pygments_formatter, **self.options)
                except ClassNotFound:
                    d = get_formatter_by_name('html', **self.options)
            else:
                d = self.pygments_formatter(lang_str=e, **self.options)
            return highlight(self.src, f, d)
        else:
            # just escape and build markup usable by JavaScript highlighting libraries
            g = self.src.replace('&', '&amp;')
            g = g.replace('<', '&lt;')
            g = g.replace('>', '&gt;')
            g = g.replace('"', '&quot;')
            b = []
            if self.lang:
                b.append('{}{}'.format(self.lang_prefix, self.lang))
            if self.options['linenos']:
                b.append('linenums')
            a = ''
            if b:
                a = ' class="{}"'.format(' '.join(b))
            return '<pre class="{}"><code{}>{}\n</code></pre>\n'.format(
                self.options['cssclass'],
                a,
                g
            )

    def _parseHeader(self) -> None:
        """
        Determines language of a code block from shebang line and whether the
        said line should be removed or left in place. If the shebang line
        contains a path (even a single /) then it is assumed to be a real
        shebang line and left alone. However, if no path is given
        (e.i.: `#!python` or `:::python`) then it is assumed to be a mock shebang
        for language identification of a code fragment and removed from the
        code block prior to processing for code highlighting. When a mock
        shebang (e.i: `#!python`) is found, line numbering is turned on. When
        colons are found in place of a shebang (e.i.: `:::python`), line
        numbering is left in the current state - off by default.

        Also parses optional list of highlight lines, like:

            :::python hl_lines="1 3"
        """

        import re

        # split text into lines
        b = self.src.split("\n")
        # pull first line to examine
        a = b.pop(0)

        c = re.compile(r'''
            (?:(?:^::+)|(?P<shebang>^[#]!)) # Shebang or 2 or more colons
            (?P<path>(?:/\w+)*[/ ])?        # Zero or 1 path
            (?P<lang>[\w#.+-]*)             # The language
            \s*                             # Arbitrary whitespace
            # Optional highlight lines, single- or double-quote-delimited
            (hl_lines=(?P<quot>"|')(?P<hl_lines>.*?)(?P=quot))?
            ''',  re.VERBOSE)
        # search first line for shebang
        m = c.search(a)
        if m:
            # we have a match
            try:
                self.lang = m.group('lang').lower()
            except IndexError:  # pragma: no cover
                self.lang = None
            if m.group('path'):
                # path exists - restore first line
                b.insert(0, a)
            if self.options['linenos'] is None and m.group('shebang'):
                # Overridable and Shebang exists - use line numbers
                self.options['linenos'] = True

            self.options['hl_lines'] = parse_hl_lines(m.group('hl_lines'))
        else:
            # No match
            b.insert(0, a)

        self.src = "\n".join(b).strip("\n")


# ------------------ The Markdown Extension -------------------------------


class HiliteTreeprocessor(Treeprocessor):
    """ Highlight source code in code blocks. """

    config: dict[str, Any]

    def code_unescape(self, text: str) -> str:
        """Unescape code."""
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        # Escaped '&' should be replaced at the end to avoid
        # conflicting with < and >.
        text = text.replace("&amp;", "&")
        return text

    def run(self, root: etree.Element) -> None:
        """ Find code blocks and store in `htmlStash`. """
        b = root.iter('pre')
        for a in b:
            if len(a) == 1 and a[0].tag == 'code':
                e = self.config.copy()
                g = a[0].text
                if g is None:
                    continue
                d = CodeHilite(
                    self.code_unescape(g),
                    tab_length=self.md.tab_length,
                    style=e.pop('pygments_style', 'default'),
                    **e
                )
                f = self.md.htmlStash.store(d.hilite())
                # Clear code block in `etree` instance
                a.clear()
                # Change to `p` element which will later
                # be removed when inserting raw html
                a.tag = 'p'
                a.text = f


class CodeHiliteExtension(Extension):
    """ Add source code highlighting to markdown code blocks. """

    def __init__(self, **kwargs):
        # define default configs
        self.config = {
            'linenums': [
                None, "Use lines numbers. True|table|inline=yes, False=no, None=auto. Default: `None`."
            ],
            'guess_lang': [
                True, "Automatic language detection - Default: `True`."
            ],
            'css_class': [
                "codehilite", "Set class name for wrapper <div> - Default: `codehilite`."
            ],
            'pygments_style': [
                'default', 'Pygments HTML Formatter Style (Colorscheme). Default: `default`.'
            ],
            'noclasses': [
                False, 'Use inline styles instead of CSS classes - Default `False`.'
            ],
            'use_pygments': [
                True, 'Highlight code blocks with pygments. Disable if using a JavaScript library. Default: `True`.'
            ],
            'lang_prefix': [
                'language-', 'Prefix prepended to the language when `use_pygments` is false. Default: `language-`.'
            ],
            'pygments_formatter': [
                'html', 'Use a specific formatter for Pygments highlighting. Default: `html`.'
            ],
        }
        """ Default configuration options. """

        for key, a in kwargs.items():
            if key in self.config:
                self.setConfig(key, a)
            else:
                # manually set unknown keywords.
                if isinstance(a, str):
                    try:
                        # Attempt to parse `str` as a boolean value
                        a = parseBoolValue(a, preserve_none=True)
                    except ValueError:
                        pass  # Assume it's not a boolean value. Use as-is.
                self.config[key] = [a, '']

    def extendMarkdown(self, md):
        """ Add `HilitePostprocessor` to Markdown instance. """
        a = HiliteTreeprocessor(md)
        a.config = self.getConfigs()
        md.treeprocessors.register(a, 'hilite', 30)

        md.registerExtension(self)


def makeExtension(**kwargs):  # pragma: no cover
    return CodeHiliteExtension(**kwargs)
