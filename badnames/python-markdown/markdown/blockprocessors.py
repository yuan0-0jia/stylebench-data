# Python Markdown

# A Python implementation of John Gruber's Markdown.

# Documentation: https://python-markdown.github.io/
# GitHub: https://github.com/Python-Markdown/markdown/
# PyPI: https://pypi.org/project/Markdown/

# Started by Manfred Stienstra (http://www.dwerg.net/).
# Maintained for a few years by Yuri Takhteyev (http://www.freewisdom.org).
# Currently maintained by Waylan Limberg (https://github.com/waylan),
# Dmitry Shachnev (https://github.com/mitya57) and Isaac Muse (https://github.com/facelessuser).

# Copyright 2007-2023 The Python Markdown Project (v. 1.7 and later)
# Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
# Copyright 2004 Manfred Stienstra (the original version)

# License: BSD (see LICENSE.md for details).

"""
A block processor parses blocks of text and adds new elements to the ElementTree. Blocks of text,
separated from other text by blank lines, may have a different syntax and produce a differently
structured tree than other Markdown. Block processors excel at handling code formatting, equation
layouts, tables, etc.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as etree
from typing import TYPE_CHECKING, Any
from . import util
from .blockparser import BlockParser

if TYPE_CHECKING:  # pragma: no cover
    from markdown import Markdown

logger = logging.getLogger('MARKDOWN')


def build_block_parser(md: Markdown, **kwargs: Any) -> BlockParser:
    """ Build the default block parser used by Markdown. """
    a = BlockParser(md)
    a.blockprocessors.register(EmptyBlockProcessor(a), 'empty', 100)
    a.blockprocessors.register(ListIndentProcessor(a), 'indent', 90)
    a.blockprocessors.register(CodeBlockProcessor(a), 'code', 80)
    a.blockprocessors.register(HashHeaderProcessor(a), 'hashheader', 70)
    a.blockprocessors.register(SetextHeaderProcessor(a), 'setextheader', 60)
    a.blockprocessors.register(HRProcessor(a), 'hr', 50)
    a.blockprocessors.register(OListProcessor(a), 'olist', 40)
    a.blockprocessors.register(UListProcessor(a), 'ulist', 30)
    a.blockprocessors.register(BlockQuoteProcessor(a), 'quote', 20)
    a.blockprocessors.register(ReferenceProcessor(a), 'reference', 15)
    a.blockprocessors.register(ParagraphProcessor(a), 'paragraph', 10)
    return a


class BlockProcessor:
    """ Base class for block processors.

    Each subclass will provide the methods below to work with the source and
    tree. Each processor will need to define it's own `test` and `run`
    methods. The `test` method should return True or False, to indicate
    whether the current block should be processed by this processor. If the
    test passes, the parser will call the processors `run` method.

    Attributes:
        BlockProcessor.parser (BlockParser): The `BlockParser` instance this is attached to.
        BlockProcessor.tab_length (int): The tab length set on the `Markdown` instance.

    """

    def __init__(self, parser: BlockParser):
        self.parser = parser
        self.tab_length = parser.md.tab_length

    def lastChild(self, parent: etree.Element) -> etree.Element | None:
        """ Return the last child of an `etree` element. """
        if len(parent):
            return parent[-1]
        else:
            return None

    def detab(self, text: str, length: int | None = None) -> tuple[str, str]:
        """ Remove a tab from the front of each line of the given text. """
        if length is None:
            length = self.tab_length
        c = []
        b = text.split('\n')
        for a in b:
            if a.startswith(' ' * length):
                c.append(a[length:])
            elif not a.strip():
                c.append('')
            else:
                break
        return '\n'.join(c), '\n'.join(b[len(c):])

    def looseDetab(self, text: str, level: int = 1) -> str:
        """ Remove a tab from front of lines but allowing dedented lines. """
        a = text.split('\n')
        for i in range(len(a)):
            if a[i].startswith(' '*self.tab_length*level):
                a[i] = a[i][self.tab_length*level:]
        return '\n'.join(a)

    def test(self, parent: etree.Element, block: str) -> bool:
        """ Test for block type. Must be overridden by subclasses.

        As the parser loops through processors, it will call the `test`
        method on each to determine if the given block of text is of that
        type. This method must return a boolean `True` or `False`. The
        actual method of testing is left to the needs of that particular
        block type. It could be as simple as `block.startswith(some_string)`
        or a complex regular expression. As the block type may be different
        depending on the parent of the block (i.e. inside a list), the parent
        `etree` element is also provided and may be used as part of the test.

        Keyword arguments:
            parent: An `etree` element which will be the parent of the block.
            block: A block of text from the source which has been split at blank lines.
        """
        pass  # pragma: no cover

    def run(self, parent: etree.Element, blocks: list[str]) -> bool | None:
        """ Run processor. Must be overridden by subclasses.

        When the parser determines the appropriate type of a block, the parser
        will call the corresponding processor's `run` method. This method
        should parse the individual lines of the block and append them to
        the `etree`.

        Note that both the `parent` and `etree` keywords are pointers
        to instances of the objects which should be edited in place. Each
        processor must make changes to the existing objects as there is no
        mechanism to return new/different objects to replace them.

        This means that this method should be adding `SubElements` or adding text
        to the parent, and should remove (`pop`) or add (`insert`) items to
        the list of blocks.

        If `False` is returned, this will have the same effect as returning `False`
        from the `test` method.

        Keyword arguments:
            parent: An `etree` element which is the parent of the current block.
            blocks: A list of all remaining blocks of the document.
        """
        pass  # pragma: no cover


class ListIndentProcessor(BlockProcessor):
    """ Process children of list items.

    Example

        * a list item
            process this part

            or this part

    """

    ITEM_TYPES = ['li']
    """ List of tags used for list items. """
    LIST_TYPES = ['ul', 'ol']
    """ Types of lists this processor can operate on. """

    def __init__(self, *args):
        super().__init__(*args)
        self.INDENT_RE = re.compile(r'^(([ ]{%s})+)' % self.tab_length)

    def test(self, parent: etree.Element, block: str) -> bool:
        return block.startswith(' '*self.tab_length) and \
            not self.parser.state.isstate('detabbed') and \
            (parent.tag in self.ITEM_TYPES or
                (len(parent) and parent[-1] is not None and
                    (parent[-1].tag in self.LIST_TYPES)))

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        a = blocks.pop(0)
        level, sibling = self.get_level(parent, a)
        a = self.looseDetab(a, level)

        self.parser.state.set('detabbed')
        if parent.tag in self.ITEM_TYPES:
            # It's possible that this parent has a `ul` or `ol` child list
            # with a member.  If that is the case, then that should be the
            # parent.  This is intended to catch the edge case of an indented
            # list whose first member was parsed previous to this point
            # see `OListProcessor`
            if len(parent) and parent[-1].tag in self.LIST_TYPES:
                self.parser.parseBlocks(parent[-1], [a])
            else:
                # The parent is already a `li`. Just parse the child block.
                self.parser.parseBlocks(parent, [a])
        elif sibling.tag in self.ITEM_TYPES:
            # The sibling is a `li`. Use it as parent.
            self.parser.parseBlocks(sibling, [a])
        elif len(sibling) and sibling[-1].tag in self.ITEM_TYPES:
            # The parent is a list (`ol` or `ul`) which has children.
            # Assume the last child `li` is the parent of this block.
            if sibling[-1].text:
                # If the parent `li` has text, that text needs to be moved to a `p`
                # The `p` must be 'inserted' at beginning of list in the event
                # that other children already exist i.e.; a nested sub-list.
                p = etree.Element('p')
                p.text = sibling[-1].text
                sibling[-1].text = ''
                sibling[-1].insert(0, p)
            self.parser.parseChunk(sibling[-1], a)
        else:
            self.create_item(sibling, a)
        self.parser.state.reset()

    def create_item(self, parent: etree.Element, block: str) -> None:
        """ Create a new `li` and parse the block with it as the parent. """
        a = etree.SubElement(parent, 'li')
        self.parser.parseBlocks(a, [block])

    def get_level(self, parent: etree.Element, block: str) -> tuple[int, etree.Element]:
        """ Get level of indentation based on list level. """
        # Get indent level
        m = self.INDENT_RE.match(block)
        if m:
            b = len(m.group(1))/self.tab_length
        else:
            b = 0
        if self.parser.state.isstate('list'):
            # We're in a tight-list - so we already are at correct parent.
            c = 1
        else:
            # We're in a loose-list - so we need to find parent.
            c = 0
        # Step through children of tree to find matching indent level.
        while b > c:
            a = self.lastChild(parent)
            if (a is not None and
               (a.tag in self.LIST_TYPES or a.tag in self.ITEM_TYPES)):
                if a.tag in self.LIST_TYPES:
                    c += 1
                parent = a
            else:
                # No more child levels. If we're short of `indent_level`,
                # we have a code block. So we stop here.
                break
        return c, parent


class CodeBlockProcessor(BlockProcessor):
    """ Process code blocks. """

    def test(self, parent: etree.Element, block: str) -> bool:
        return block.startswith(' '*self.tab_length)

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        d = self.lastChild(parent)
        a = blocks.pop(0)
        e = ''
        if (d is not None and d.tag == "pre" and
           len(d) and d[0].tag == "code"):
            # The previous block was a code block. As blank lines do not start
            # new code blocks, append this block to the previous, adding back
            # line breaks removed from the split into a list.
            b = d[0]
            a, e = self.detab(a)
            b.text = util.AtomicString(
                '{}\n{}\n'.format(b.text, util.code_escape(a.rstrip()))
            )
        else:
            # This is a new code block. Create the elements and insert text.
            c = etree.SubElement(parent, 'pre')
            b = etree.SubElement(c, 'code')
            a, e = self.detab(a)
            b.text = util.AtomicString('%s\n' % util.code_escape(a.rstrip()))
        if e:
            # This block contained unindented line(s) after the first indented
            # line. Insert these lines as the first block of the master blocks
            # list for future processing.
            blocks.insert(0, e)


class BlockQuoteProcessor(BlockProcessor):
    """ Process blockquotes. """

    RE = re.compile(r'(^|\n)[ ]{0,3}>[ ]?(.*)')

    def test(self, parent: etree.Element, block: str) -> bool:
        return bool(self.RE.search(block)) and not util.nearing_recursion_limit()

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        b = blocks.pop(0)
        m = self.RE.search(b)
        if m:
            a = b[:m.start()]  # Lines before blockquote
            # Pass lines before blockquote in recursively for parsing first.
            self.parser.parseBlocks(parent, [a])
            # Remove `> ` from beginning of each line.
            b = '\n'.join(
                [self.clean(line) for line in b[m.start():].split('\n')]
            )
        d = self.lastChild(parent)
        if d is not None and d.tag == "blockquote":
            # Previous block was a blockquote so set that as this blocks parent
            c = d
        else:
            # This is a new blockquote. Create a new parent element.
            c = etree.SubElement(parent, 'blockquote')
        # Recursively parse block with blockquote as parent.
        # change parser state so blockquotes embedded in lists use `p` tags
        self.parser.state.set('blockquote')
        self.parser.parseChunk(c, b)
        self.parser.state.reset()

    def clean(self, line: str) -> str:
        """ Remove `>` from beginning of a line. """
        m = self.RE.match(line)
        if line.strip() == ">":
            return ""
        elif m:
            return m.group(2)
        else:
            return line


class OListProcessor(BlockProcessor):
    """ Process ordered list blocks. """

    TAG: str = 'ol'
    """ The tag used for the the wrapping element. """
    STARTSWITH: str = '1'
    """
    The integer (as a string ) with which the list starts. For example, if a list is initialized as
    `3. Item`, then the `ol` tag will be assigned an HTML attribute of `starts="3"`. Default: `"1"`.
    """
    LAZY_OL: bool = True
    """ Ignore `STARTSWITH` if `True`. """
    SIBLING_TAGS: list[str] = ['ol', 'ul']
    """
    Markdown does not require the type of a new list item match the previous list item type.
    This is the list of types which can be mixed.
    """

    def __init__(self, parser: BlockParser):
        super().__init__(parser)
        # Detect an item (`1. item`). `group(1)` contains contents of item.
        self.RE = re.compile(r'^[ ]{0,%d}\d+\.[ ]+(.*)' % (self.tab_length - 1))
        # Detect items on secondary lines. they can be of either list type.
        self.CHILD_RE = re.compile(r'^[ ]{0,%d}((\d+\.)|[*+-])[ ]+(.*)' %
                                   (self.tab_length - 1))
        # Detect indented (nested) items of either type
        self.INDENT_RE = re.compile(r'^[ ]{%d,%d}((\d+\.)|[*+-])[ ]+.*' %
                                    (self.tab_length, self.tab_length * 2 - 1))

    def test(self, parent: etree.Element, block: str) -> bool:
        return bool(self.RE.match(block))

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        # Check for multiple items in one block.
        c = self.get_items(blocks.pop(0))
        g = self.lastChild(parent)

        if g is not None and g.tag in self.SIBLING_TAGS:
            # Previous block was a list item, so set that as parent
            f = g
            # make sure previous item is in a `p` - if the item has text,
            # then it isn't in a `p`
            if f[-1].text:
                # since it's possible there are other children for this
                # sibling, we can't just `SubElement` the `p`, we need to
                # insert it as the first item.
                p = etree.Element('p')
                p.text = f[-1].text
                f[-1].text = ''
                f[-1].insert(0, p)
            # if the last item has a tail, then the tail needs to be put in a `p`
            # likely only when a header is not followed by a blank line
            d = self.lastChild(f[-1])
            if d is not None and d.tail:
                p = etree.SubElement(f[-1], 'p')
                p.text = d.tail.lstrip()
                d.tail = ''

            # parse first block differently as it gets wrapped in a `p`.
            e = etree.SubElement(f, 'li')
            self.parser.state.set('looselist')
            a = c.pop(0)
            self.parser.parseBlocks(e, [a])
            self.parser.state.reset()
        elif parent.tag in ['ol', 'ul']:
            # this catches the edge case of a multi-item indented list whose
            # first item is in a blank parent-list item:
            #     * * subitem1
            #         * subitem2
            # see also `ListIndentProcessor`
            f = parent
        else:
            # This is a new list so create parent with appropriate tag.
            f = etree.SubElement(parent, self.TAG)
            # Check if a custom start integer is set
            if not self.LAZY_OL and self.STARTSWITH != '1':
                f.attrib['start'] = self.STARTSWITH

        self.parser.state.set('list')
        # Loop through items in block, recursively parsing each with the
        # appropriate parent.
        for b in c:
            if b.startswith(' '*self.tab_length):
                # Item is indented. Parse with last item as parent
                self.parser.parseBlocks(f[-1], [b])
            else:
                # New item. Create `li` and parse with it as parent
                e = etree.SubElement(f, 'li')
                self.parser.parseBlocks(e, [b])
        self.parser.state.reset()

    def get_items(self, block: str) -> list[str]:
        """ Break a block into list items. """
        a = []
        for b in block.split('\n'):
            m = self.CHILD_RE.match(b)
            if m:
                # This is a new list item
                # Check first item for the start index
                if not a and self.TAG == 'ol':
                    # Detect the integer value of first list item
                    INTEGER_RE = re.compile(r'(\d+)')
                    self.STARTSWITH = INTEGER_RE.match(m.group(1)).group()
                # Append to the list
                a.append(m.group(3))
            elif self.INDENT_RE.match(b):
                # This is an indented (possibly nested) item.
                if a[-1].startswith(' '*self.tab_length):
                    # Previous item was indented. Append to that item.
                    a[-1] = '{}\n{}'.format(a[-1], b)
                else:
                    a.append(b)
            else:
                # This is another line of previous item. Append to that item.
                a[-1] = '{}\n{}'.format(a[-1], b)
        return a


class UListProcessor(OListProcessor):
    """ Process unordered list blocks. """

    TAG: str = 'ul'
    """ The tag used for the the wrapping element. """

    def __init__(self, parser: BlockParser):
        super().__init__(parser)
        # Detect an item (`1. item`). `group(1)` contains contents of item.
        self.RE = re.compile(r'^[ ]{0,%d}[*+-][ ]+(.*)' % (self.tab_length - 1))


class HashHeaderProcessor(BlockProcessor):
    """ Process Hash Headers. """

    # Detect a header at start of any line in block
    RE = re.compile(r'(?:^|\n)(?P<level>#{1,6})(?P<header>(?:\\.|[^\\])*?)#*(?:\n|$)')

    def test(self, parent: etree.Element, block: str) -> bool:
        return bool(self.RE.search(block))

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        c = blocks.pop(0)
        m = self.RE.search(c)
        if m:
            b = c[:m.start()]  # All lines before header
            a = c[m.end():]     # All lines after header
            if b:
                # As the header was not the first line of the block and the
                # lines before the header must be parsed first,
                # recursively parse this lines as a block.
                self.parser.parseBlocks(parent, [b])
            # Create header using named groups from RE
            h = etree.SubElement(parent, 'h%d' % len(m.group('level')))
            h.text = m.group('header').strip()
            if a:
                # Insert remaining lines as first block for future parsing.
                if self.parser.state.isstate('looselist'):
                    # This is a weird edge case where a header is a child of a loose list
                    # and there is no blank line after the header. To ensure proper
                    # parsing, the line(s) after need to be detabbed. See #1443.
                    a = self.looseDetab(a)
                blocks.insert(0, a)
        else:  # pragma: no cover
            # This should never happen, but just in case...
            logger.warn("We've got a problem header: %r" % c)


class SetextHeaderProcessor(BlockProcessor):
    """ Process Setext-style Headers. """

    # Detect Setext-style header. Must be first 2 lines of block.
    RE = re.compile(r'^.*?\n[=-]+[ ]*(\n|$)', re.MULTILINE)

    def test(self, parent: etree.Element, block: str) -> bool:
        return bool(self.RE.match(block))

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        b = blocks.pop(0).split('\n')
        # Determine level. `=` is 1 and `-` is 2.
        if b[1].startswith('='):
            a = 1
        else:
            a = 2
        h = etree.SubElement(parent, 'h%d' % a)
        h.text = b[0].strip()
        if len(b) > 2:
            # Block contains additional lines. Add to  master blocks for later.
            blocks.insert(0, '\n'.join(b[2:]))


class HRProcessor(BlockProcessor):
    """ Process Horizontal Rules. """

    # Python's `re` module doesn't officially support atomic grouping. However you can fake it.
    # See https://stackoverflow.com/a/13577411/866026
    RE = r'^[ ]{0,3}(?=(?P<atomicgroup>(-+[ ]{0,2}){3,}|(_+[ ]{0,2}){3,}|(\*+[ ]{0,2}){3,}))(?P=atomicgroup)[ ]*$'
    # Detect hr on any line of a block.
    SEARCH_RE = re.compile(RE, re.MULTILINE)

    def test(self, parent: etree.Element, block: str) -> bool:
        m = self.SEARCH_RE.search(block)
        if m:
            # Save match object on class instance so we can use it later.
            self.match = m
            return True
        return False

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        a = blocks.pop(0)
        b = self.match
        # Check for lines in block before `hr`.
        d = a[:b.start()].rstrip('\n')
        if d:
            # Recursively parse lines before `hr` so they get parsed first.
            self.parser.parseBlocks(parent, [d])
        # create hr
        etree.SubElement(parent, 'hr')
        # check for lines in block after `hr`.
        c = a[b.end():].lstrip('\n')
        if c:
            # Add lines after `hr` to master blocks for later parsing.
            blocks.insert(0, c)


class EmptyBlockProcessor(BlockProcessor):
    """ Process blocks that are empty or start with an empty line. """

    def test(self, parent: etree.Element, block: str) -> bool:
        return not block or block.startswith('\n')

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        a = blocks.pop(0)
        b = '\n\n'
        if a:
            # Starts with empty line
            # Only replace a single line.
            b = '\n'
            # Save the rest for later.
            d = a[1:]
            if d:
                # Add remaining lines to master blocks for later.
                blocks.insert(0, d)
        c = self.lastChild(parent)
        if (c is not None and c.tag == 'pre' and
           len(c) and c[0].tag == 'code'):
            # Last block is a code block. Append to preserve whitespace.
            c[0].text = util.AtomicString(
                '{}{}'.format(c[0].text, b)
            )


class ReferenceProcessor(BlockProcessor):
    """ Process link references. """
    RE = re.compile(
        r'^[ ]{0,3}\[([^\[\]]*)\]:[ ]*\n?[ ]*([^\s]+)[ ]*(?:\n[ ]*)?((["\'])(.*)\4[ ]*|\((.*)\)[ ]*)?$', re.MULTILINE
    )

    def test(self, parent: etree.Element, block: str) -> bool:
        return True

    def run(self, parent: etree.Element, blocks: list[str]) -> bool:
        a = blocks.pop(0)
        m = self.RE.search(a)
        if m:
            id = m.group(1).strip().lower()
            b = m.group(2).lstrip('<').rstrip('>')
            c = m.group(5) or m.group(6)
            self.parser.md.references[id] = (b, c)
            if a[m.end():].strip():
                # Add any content after match back to blocks as separate block
                blocks.insert(0, a[m.end():].lstrip('\n'))
            if a[:m.start()].strip():
                # Add any content before match back to blocks as separate block
                blocks.insert(0, a[:m.start()].rstrip('\n'))
            return True
        # No match. Restore block.
        blocks.insert(0, a)
        return False


class ParagraphProcessor(BlockProcessor):
    """ Process Paragraph blocks. """

    def test(self, parent: etree.Element, block: str) -> bool:
        return True

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        a = blocks.pop(0)
        if a.strip():
            # Not a blank block. Add to parent, otherwise throw it away.
            if self.parser.state.isstate('list'):
                # The parent is a tight-list.
                #
                # Check for any children. This will likely only happen in a
                # tight-list when a header isn't followed by a blank line.
                # For example:
                #
                #     * # Header
                #     Line 2 of list item - not part of header.
                b = self.lastChild(parent)
                if b is not None:
                    # Insert after sibling.
                    if b.tail:
                        b.tail = '{}\n{}'.format(b.tail, a)
                    else:
                        b.tail = '\n%s' % a
                else:
                    # Append to parent.text
                    if parent.text:
                        parent.text = '{}\n{}'.format(parent.text, a)
                    else:
                        parent.text = a.lstrip()
            else:
                # Create a regular paragraph
                p = etree.SubElement(parent, 'p')
                p.text = a.lstrip()
