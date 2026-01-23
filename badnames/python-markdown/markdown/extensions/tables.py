# Tables Extension for Python-Markdown
# ====================================

# Adds parsing of tables to Python-Markdown.

# See https://Python-Markdown.github.io/extensions/tables
# for documentation.

# Original code Copyright 2009 [Waylan Limberg](https://github.com/waylan)

# All changes Copyright 2008-2014 The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""
Adds parsing of tables to Python-Markdown.

See the [documentation](https://Python-Markdown.github.io/extensions/tables)
for details.
"""

from __future__ import annotations

from . import Extension
from ..blockprocessors import BlockProcessor
import xml.etree.ElementTree as etree
import re
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:  # pragma: no cover
    from .. import blockparser

PIPE_NONE = 0
PIPE_LEFT = 1
PIPE_RIGHT = 2


class TableProcessor(BlockProcessor):
    """ Process Tables. """

    RE_CODE_PIPES = re.compile(r'(?:(\\\\)|(\\`+)|(`+)|(\\\|)|(\|))')
    RE_END_BORDER = re.compile(r'(?<!\\)(?:\\\\)*\|$')

    def __init__(self, parser: blockparser.BlockParser, config: dict[str, Any]):
        self.border: bool | int = False
        self.separator: Sequence[str] = ''
        self.config = config

        super().__init__(parser)

    def test(self, parent: etree.Element, block: str) -> bool:
        """
        Ensure first two rows (column header and separator row) are valid table rows.

        Keep border check and separator row do avoid repeating the work.
        """
        e = False
        h = [f.strip(' ') for f in block.split('\n')]
        if len(h) > 1:
            b = h[0]
            self.border = PIPE_NONE
            if b.startswith('|'):
                self.border |= PIPE_LEFT
            if self.RE_END_BORDER.search(b) is not None:
                self.border |= PIPE_RIGHT
            f = self._split_row(b)
            g = len(f)
            e = g > 1

            # Each row in a single column table needs at least one pipe.
            if not e and g == 1 and self.border:
                for d in range(1, len(h)):
                    e = h[d].startswith('|')
                    if not e:
                        e = self.RE_END_BORDER.search(h[d]) is not None
                    if not e:
                        break

            if e:
                f = self._split_row(h[1])
                e = (len(f) == g) and set(''.join(f)) <= set('|:- ')
                if e:
                    self.separator = f

        return e

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        """ Parse a table block and build table. """
        d = blocks.pop(0).split('\n')
        e = d[0].strip(' ')
        g = [] if len(d) < 3 else d[2:]

        # Get alignment of columns
        b: list[str | None] = []
        for c in self.separator:
            c = c.strip(' ')
            if c.startswith(':') and c.endswith(':'):
                b.append('center')
            elif c.startswith(':'):
                b.append('left')
            elif c.endswith(':'):
                b.append('right')
            else:
                b.append(None)

        # Build table
        h = etree.SubElement(parent, 'table')
        k = etree.SubElement(h, 'thead')
        self._build_row(e, k, b)
        j = etree.SubElement(h, 'tbody')
        if len(g) == 0:
            # Handle empty table
            self._build_empty_row(j, b)
        else:
            for f in g:
                self._build_row(f.strip(' '), j, b)

    def _build_empty_row(self, parent: etree.Element, align: Sequence[str | None]) -> None:
        """Build an empty row."""
        d = etree.SubElement(parent, 'tr')
        b = len(align)
        while b:
            etree.SubElement(d, 'td')
            b -= 1

    def _build_row(self, row: str, parent: etree.Element, align: Sequence[str | None]) -> None:
        """ Given a row of text, build table cells. """
        e = etree.SubElement(parent, 'tr')
        d = 'td'
        if parent.tag == 'thead':
            d = 'th'
        b = self._split_row(row)
        # We use align here rather than cells to ensure every row
        # contains the same number of columns.
        for i, a in enumerate(align):
            c = etree.SubElement(e, d)
            try:
                c.text = b[i].strip(' ')
            except IndexError:  # pragma: no cover
                c.text = ""
            if a:
                if self.config['use_align_attribute']:
                    c.set('align', a)
                else:
                    c.set('style', f'text-align: {a};')

    def _split_row(self, row: str) -> list[str]:
        """ split a row of text into list of cells. """
        if self.border:
            if row.startswith('|'):
                row = row[1:]
            row = self.RE_END_BORDER.sub('', row)
        return self._split(row)

    def _split(self, row: str) -> list[str]:
        """ split a row of text with some code into a list of cells. """
        b = []
        g = []
        q = []
        n = []
        o = []
        d = []

        # Parse row
        # Throw out \\, and \|
        for m in self.RE_CODE_PIPES.finditer(row):
            # Store ` data (len, start_pos, end_pos)
            if m.group(2):
                # \`+
                # Store length of each tic group: subtract \
                q.append(len(m.group(2)) - 1)
                # Store start of group, end of group, and escape length
                n.append((m.start(2), m.end(2) - 1, 1))
            elif m.group(3):
                # `+
                # Store length of each tic group
                q.append(len(m.group(3)))
                # Store start of group, end of group, and escape length
                n.append((m.start(3), m.end(3) - 1, 0))
            # Store pipe location
            elif m.group(5):
                g.append(m.start(5))

        # Pair up tics according to size if possible
        # Subtract the escape length *only* from the opening.
        # Walk through tic list and see if tic has a close.
        # Store the tic region (start of region, end of region).
        h = 0
        l = len(q)
        while h < l:
            try:
                p = q[h] - n[h][2]
                if p == 0:
                    raise ValueError
                e = q[h + 1:].index(p) + 1
                o.append((n[h][0], n[h + e][1]))
                h += e + 1
            except ValueError:
                h += 1

        # Resolve pipes.  Check if they are within a tic pair region.
        # Walk through pipes comparing them to each region.
        #     - If pipe position is less that a region, it isn't in a region
        #     - If it is within a region, we don't want it, so throw it out
        #     - If we didn't throw it out, it must be a table pipe
        for f in g:
            k = False
            for j in o:
                if f < j[0]:
                    # Pipe is not in a region
                    break
                elif j[0] <= f <= j[1]:
                    # Pipe is within a code region.  Throw it out.
                    k = True
                    break
            if not k:
                d.append(f)

        # Split row according to table delimiters.
        h = 0
        for f in d:
            b.append(row[h:f])
            h = f + 1
        b.append(row[h:])
        return b


class TableExtension(Extension):
    """ Add tables to Markdown. """

    def __init__(self, **kwargs):
        self.config = {
            'use_align_attribute': [False, 'True to use align attribute instead of style.'],
        }
        """ Default configuration options. """

        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        """ Add an instance of `TableProcessor` to `BlockParser`. """
        if '|' not in md.ESCAPED_CHARS:
            md.ESCAPED_CHARS.append('|')
        b = TableProcessor(md.parser, self.getConfigs())
        md.parser.blockprocessors.register(b, 'table', 75)


def makeExtension(**kwargs):  # pragma: no cover
    return TableExtension(**kwargs)
