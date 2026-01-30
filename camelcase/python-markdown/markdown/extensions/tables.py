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
        isTable = False
        rows = [row.strip(' ') for row in block.split('\n')]
        if len(rows) > 1:
            header0 = rows[0]
            self.border = PIPE_NONE
            if header0.startswith('|'):
                self.border |= PIPE_LEFT
            if self.RE_END_BORDER.search(header0) is not None:
                self.border |= PIPE_RIGHT
            row = self._split_row(header0)
            row0Len = len(row)
            isTable = row0Len > 1

            # Each row in a single column table needs at least one pipe.
            if not isTable and row0Len == 1 and self.border:
                for index in range(1, len(rows)):
                    isTable = rows[index].startswith('|')
                    if not isTable:
                        isTable = self.RE_END_BORDER.search(rows[index]) is not None
                    if not isTable:
                        break

            if isTable:
                row = self._split_row(rows[1])
                isTable = (len(row) == row0Len) and set(''.join(row)) <= set('|:- ')
                if isTable:
                    self.separator = row

        return isTable

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        """ Parse a table block and build table. """
        block = blocks.pop(0).split('\n')
        header = block[0].strip(' ')
        rows = [] if len(block) < 3 else block[2:]

        # Get alignment of columns
        align: list[str | None] = []
        for c in self.separator:
            c = c.strip(' ')
            if c.startswith(':') and c.endswith(':'):
                align.append('center')
            elif c.startswith(':'):
                align.append('left')
            elif c.endswith(':'):
                align.append('right')
            else:
                align.append(None)

        # Build table
        table = etree.SubElement(parent, 'table')
        thead = etree.SubElement(table, 'thead')
        self._build_row(header, thead, align)
        tbody = etree.SubElement(table, 'tbody')
        if len(rows) == 0:
            # Handle empty table
            self._build_empty_row(tbody, align)
        else:
            for row in rows:
                self._build_row(row.strip(' '), tbody, align)

    def _build_empty_row(self, parent: etree.Element, align: Sequence[str | None]) -> None:
        """Build an empty row."""
        tr = etree.SubElement(parent, 'tr')
        count = len(align)
        while count:
            etree.SubElement(tr, 'td')
            count -= 1

    def _build_row(self, row: str, parent: etree.Element, align: Sequence[str | None]) -> None:
        """ Given a row of text, build table cells. """
        tr = etree.SubElement(parent, 'tr')
        tag = 'td'
        if parent.tag == 'thead':
            tag = 'th'
        cells = self._split_row(row)
        # We use align here rather than cells to ensure every row
        # contains the same number of columns.
        for i, a in enumerate(align):
            c = etree.SubElement(tr, tag)
            try:
                c.text = cells[i].strip(' ')
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
        elements = []
        pipes = []
        tics = []
        ticPoints = []
        ticRegion = []
        goodPipes = []

        # Parse row
        # Throw out \\, and \|
        for m in self.RE_CODE_PIPES.finditer(row):
            # Store ` data (len, start_pos, end_pos)
            if m.group(2):
                # \`+
                # Store length of each tic group: subtract \
                tics.append(len(m.group(2)) - 1)
                # Store start of group, end of group, and escape length
                ticPoints.append((m.start(2), m.end(2) - 1, 1))
            elif m.group(3):
                # `+
                # Store length of each tic group
                tics.append(len(m.group(3)))
                # Store start of group, end of group, and escape length
                ticPoints.append((m.start(3), m.end(3) - 1, 0))
            # Store pipe location
            elif m.group(5):
                pipes.append(m.start(5))

        # Pair up tics according to size if possible
        # Subtract the escape length *only* from the opening.
        # Walk through tic list and see if tic has a close.
        # Store the tic region (start of region, end of region).
        pos = 0
        ticLen = len(tics)
        while pos < ticLen:
            try:
                ticSize = tics[pos] - ticPoints[pos][2]
                if ticSize == 0:
                    raise ValueError
                index = tics[pos + 1:].index(ticSize) + 1
                ticRegion.append((ticPoints[pos][0], ticPoints[pos + index][1]))
                pos += index + 1
            except ValueError:
                pos += 1

        # Resolve pipes.  Check if they are within a tic pair region.
        # Walk through pipes comparing them to each region.
        #     - If pipe position is less that a region, it isn't in a region
        #     - If it is within a region, we don't want it, so throw it out
        #     - If we didn't throw it out, it must be a table pipe
        for pipe in pipes:
            throwOut = False
            for region in ticRegion:
                if pipe < region[0]:
                    # Pipe is not in a region
                    break
                elif region[0] <= pipe <= region[1]:
                    # Pipe is within a code region.  Throw it out.
                    throwOut = True
                    break
            if not throwOut:
                goodPipes.append(pipe)

        # Split row according to table delimiters.
        pos = 0
        for pipe in goodPipes:
            elements.append(row[pos:pipe])
            pos = pipe + 1
        elements.append(row[pos:])
        return elements


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
        processor = TableProcessor(md.parser, self.getConfigs())
        md.parser.blockprocessors.register(processor, 'table', 75)


def makeExtension(**kwargs):  # pragma: no cover
    return TableExtension(**kwargs)
