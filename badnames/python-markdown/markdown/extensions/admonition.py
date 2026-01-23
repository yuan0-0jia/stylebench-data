# Admonition extension for Python-Markdown
# ========================================

# Adds rST-style admonitions. Inspired by [rST][] feature with the same name.

# [rST]: http://docutils.sourceforge.net/docs/ref/rst/directives.html#specific-admonitions

# See https://Python-Markdown.github.io/extensions/admonition
# for documentation.

# Original code Copyright [Tiago Serafim](https://www.tiagoserafim.com/).

# All changes Copyright The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)


"""
Adds rST-style admonitions to Python-Markdown.
Inspired by [rST][] feature with the same name.

[rST]: http://docutils.sourceforge.net/docs/ref/rst/directives.html#specific-admonitions

See the [documentation](https://Python-Markdown.github.io/extensions/admonition)
for details.
"""

from __future__ import annotations

from . import Extension
from ..blockprocessors import BlockProcessor
import xml.etree.ElementTree as etree
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from markdown import blockparser


class AdmonitionExtension(Extension):
    """ Admonition extension for Python-Markdown. """

    def extendMarkdown(self, md):
        """ Add Admonition to Markdown instance. """
        md.registerExtension(self)

        md.parser.blockprocessors.register(AdmonitionProcessor(md.parser), 'admonition', 105)


class AdmonitionProcessor(BlockProcessor):

    CLASSNAME = 'admonition'
    CLASSNAME_TITLE = 'admonition-title'
    RE = re.compile(r'(?:^|\n)!!! ?([\w\-]+(?: +[\w\-]+)*)(?: +"(.*?)")? *(?:\n|$)')
    RE_SPACES = re.compile('  +')

    def __init__(self, parser: blockparser.BlockParser):
        """Initialization."""

        super().__init__(parser)

        self.current_sibling: etree.Element | None = None
        self.content_indent = 0

    def parse_content(self, parent: etree.Element, block: str) -> tuple[etree.Element | None, str, str]:
        """Get sibling admonition.

        Retrieve the appropriate sibling element. This can get tricky when
        dealing with lists.

        """

        c = block
        e = ''

        # We already acquired the block via test
        if self.current_sibling is not None:
            d = self.current_sibling
            block, e = self.detab(block, self.content_indent)
            self.current_sibling = None
            self.content_indent = 0
            return d, block, e

        d = self.lastChild(parent)

        if d is None or d.tag != 'div' or d.get('class', '').find(self.CLASSNAME) == -1:
            d = None
        else:
            # If the last child is a list and the content is sufficiently indented
            # to be under it, then the content's sibling is in the list.
            b = self.lastChild(d)
            a = 0
            while b is not None:
                if (
                    d is not None and block.startswith(' ' * self.tab_length * 2) and
                    b is not None and b.tag in ('ul', 'ol', 'dl')
                ):

                    # The expectation is that we'll find an `<li>` or `<dt>`.
                    # We should get its last child as well.
                    d = self.lastChild(b)
                    b = self.lastChild(d) if d is not None else None

                    # Context has been lost at this point, so we must adjust the
                    # text's indentation level so it will be evaluated correctly
                    # under the list.
                    block = block[self.tab_length:]
                    a += self.tab_length
                else:
                    b = None

            if not block.startswith(' ' * self.tab_length):
                d = None

            if d is not None:
                a += self.tab_length
                block, e = self.detab(c, a)
                self.current_sibling = d
                self.content_indent = a

        return d, block, e

    def test(self, parent: etree.Element, block: str) -> bool:

        if self.RE.search(block):
            return True
        else:
            return self.parse_content(parent, block)[0] is not None

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        a = blocks.pop(0)
        m = self.RE.search(a)

        if m:
            if m.start() > 0:
                self.parser.parseBlocks(parent, [a[:m.start()]])
            a = a[m.end():]  # removes the first line
            a, theRest = self.detab(a)
        else:
            sibling, a, theRest = self.parse_content(parent, a)

        if m:
            klass, title = self.get_class_and_title(m)
            b = etree.SubElement(parent, 'div')
            b.set('class', '{} {}'.format(self.CLASSNAME, klass))
            if title:
                p = etree.SubElement(b, 'p')
                p.text = title
                p.set('class', self.CLASSNAME_TITLE)
        else:
            # Sibling is a list item, but we need to wrap it's content should be wrapped in <p>
            if sibling.tag in ('li', 'dd') and sibling.text:
                c = sibling.text
                sibling.text = ''
                p = etree.SubElement(sibling, 'p')
                p.text = c

            b = sibling

        self.parser.parseChunk(b, a)

        if theRest:
            # This block contained unindented line(s) after the first indented
            # line. Insert these lines as the first block of the master blocks
            # list for future processing.
            blocks.insert(0, theRest)

    def get_class_and_title(self, match: re.Match[str]) -> tuple[str, str | None]:
        a, b = match.group(1).lower(), match.group(2)
        a = self.RE_SPACES.sub(' ', a)
        if b is None:
            # no title was provided, use the capitalized class name as title
            # e.g.: `!!! note` will render
            # `<p class="admonition-title">Note</p>`
            b = a.split(' ', 1)[0].capitalize()
        elif b == '':
            # an explicit blank title should not be rendered
            # e.g.: `!!! warning ""` will *not* render `p` with a title
            b = None
        return a, b


def makeExtension(**kwargs):  # pragma: no cover
    return AdmonitionExtension(**kwargs)
