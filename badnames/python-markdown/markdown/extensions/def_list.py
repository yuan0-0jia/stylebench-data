# Definition List Extension for Python-Markdown
# =============================================

# Adds parsing of Definition Lists to Python-Markdown.

# See https://Python-Markdown.github.io/extensions/definition_lists
# for documentation.

# Original code Copyright 2008 [Waylan Limberg](https://github.com/waylan)

# All changes Copyright 2008-2014 The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""
Adds parsing of Definition Lists to Python-Markdown.

See the [documentation](https://Python-Markdown.github.io/extensions/definition_lists)
for details.
"""

from __future__ import annotations

from . import Extension
from ..blockprocessors import BlockProcessor, ListIndentProcessor
import xml.etree.ElementTree as etree
import re


class DefListProcessor(BlockProcessor):
    """ Process Definition Lists. """

    RE = re.compile(r'(^|\n)[ ]{0,3}:[ ]{1,3}(.*?)(\n|$)')
    NO_INDENT_RE = re.compile(r'^[ ]{0,3}[^ :]')

    def test(self, parent: etree.Element, block: str) -> bool:
        return bool(self.RE.search(block))

    def run(self, parent: etree.Element, blocks: list[str]) -> bool | None:

        g = blocks.pop(0)
        m = self.RE.search(g)
        k = [j.strip() for j in
                 g[:m.start()].split('\n') if j.strip()]
        a = g[m.end():]
        f = self.NO_INDENT_RE.match(a)
        if f:
            d, theRest = (a, None)
        else:
            d, theRest = self.detab(a)
        if d:
            d = '{}\n{}'.format(m.group(2), d)
        else:
            d = m.group(2)
        h = self.lastChild(parent)
        if not k and h is None:
            # This is not a definition item. Most likely a paragraph that
            # starts with a colon at the beginning of a document or list.
            blocks.insert(0, g)
            return False
        if not k and h.tag == 'p':
            # The previous paragraph contains the terms
            i = 'looselist'
            k = h.text.split('\n')
            parent.remove(h)
            # Acquire new sibling
            h = self.lastChild(parent)
        else:
            i = 'list'

        if h is not None and h.tag == 'dl':
            # This is another item on an existing list
            c = h
            if not k and len(c) and c[-1].tag == 'dd' and len(c[-1]):
                i = 'looselist'
        else:
            # This is a new list
            c = etree.SubElement(parent, 'dl')
        # Add terms
        for j in k:
            e = etree.SubElement(c, 'dt')
            e.text = j
        # Add definition
        self.parser.state.set(i)
        b = etree.SubElement(c, 'dd')
        self.parser.parseBlocks(b, [d])
        self.parser.state.reset()

        if theRest:
            blocks.insert(0, theRest)


class DefListIndentProcessor(ListIndentProcessor):
    """ Process indented children of definition list items. """

    # Definition lists need to be aware of all list types
    ITEM_TYPES = ['dd', 'li']
    """ Include `dd` in list item types. """
    LIST_TYPES = ['dl', 'ol', 'ul']
    """ Include `dl` is list types. """

    def create_item(self, parent: etree.Element, block: str) -> None:
        """ Create a new `dd` or `li` (depending on parent) and parse the block with it as the parent. """

        a = etree.SubElement(parent, 'dd')
        self.parser.parseBlocks(a, [block])


class DefListExtension(Extension):
    """ Add definition lists to Markdown. """

    def extendMarkdown(self, md):
        """ Add an instance of `DefListProcessor` to `BlockParser`. """
        md.parser.blockprocessors.register(DefListIndentProcessor(md.parser), 'defindent', 85)
        md.parser.blockprocessors.register(DefListProcessor(md.parser), 'deflist', 25)


def makeExtension(**kwargs):  # pragma: no cover
    return DefListExtension(**kwargs)
