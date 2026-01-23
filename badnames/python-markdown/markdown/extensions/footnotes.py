# Footnotes Extension for Python-Markdown
# =======================================

# Adds footnote handling to Python-Markdown.

# See https://Python-Markdown.github.io/extensions/footnotes
# for documentation.

# Copyright The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""
Adds footnote handling to Python-Markdown.

See the [documentation](https://Python-Markdown.github.io/extensions/footnotes)
for details.
"""

from __future__ import annotations

from . import Extension
from ..blockprocessors import BlockProcessor
from ..inlinepatterns import InlineProcessor
from ..treeprocessors import Treeprocessor
from ..postprocessors import Postprocessor
from .. import util
from collections import OrderedDict
import re
import copy
import xml.etree.ElementTree as etree

FN_BACKLINK_TEXT = util.STX + "zz1337820767766393qq" + util.ETX
NBSP_PLACEHOLDER = util.STX + "qq3936677670287331zz" + util.ETX
RE_REF_ID = re.compile(r'(fnref)(\d+)')
RE_REFERENCE = re.compile(r'(?<!!)\[\^([^\]]*)\](?!\s*:)')


class FootnoteExtension(Extension):
    """ Footnote Extension. """

    def __init__(self, **kwargs):
        """ Setup configs. """

        self.config = {
            'PLACE_MARKER': [
                '///Footnotes Go Here///', 'The text string that marks where the footnotes go'
            ],
            'UNIQUE_IDS': [
                False, 'Avoid name collisions across multiple calls to `reset()`.'
            ],
            'BACKLINK_TEXT': [
                '&#8617;', "The text string that links from the footnote to the reader's place."
            ],
            'SUPERSCRIPT_TEXT': [
                '{}', "The text string that links from the reader's place to the footnote."
            ],
            'BACKLINK_TITLE': [
                'Jump back to footnote %d in the text',
                'The text string used for the title HTML attribute of the backlink. '
                '%d will be replaced by the footnote number.'
            ],
            'SEPARATOR': [
                ':', 'Footnote separator.'
            ],
            'USE_DEFINITION_ORDER': [
                True,
                'Order footnote labels by definition order (True) or by document order (False). '
                'Default: True.'
            ]
        }
        """ Default configuration options. """
        super().__init__(**kwargs)

        # In multiple invocations, emit links that don't get tangled.
        self.unique_prefix = 0
        self.found_refs: dict[str, int] = {}
        self.used_refs: set[str] = set()

        # Backward compatibility with old '%d' placeholder
        self.setConfig('BACKLINK_TITLE', self.getConfig("BACKLINK_TITLE").replace("%d", "{}"))

        self.reset()

    def extendMarkdown(self, md):
        """ Add pieces to Markdown. """
        md.registerExtension(self)
        self.parser = md.parser
        self.md = md
        # Insert a `blockprocessor` before `ReferencePreprocessor`
        md.parser.blockprocessors.register(FootnoteBlockProcessor(self), 'footnote', 17)

        # Insert an inline pattern before `ImageReferencePattern`
        FOOTNOTE_RE = r'\[\^([^\]]*)\]'  # blah blah [^1] blah
        md.inlinePatterns.register(FootnoteInlineProcessor(FOOTNOTE_RE, self), 'footnote', 175)
        # Insert a tree-processor that would actually add the footnote div
        # This must be before all other tree-processors (i.e., `inline` and
        # `codehilite`) so they can run on the the contents of the div.
        md.treeprocessors.register(FootnoteTreeprocessor(self), 'footnote', 50)

        # Insert a tree-processor to reorder the footnotes if necessary. This must be after
        # `inline` tree-processor so it can access the footnote reference order
        # (`self.footnote_order`) that gets populated by the `FootnoteInlineProcessor`.
        if not self.getConfig("USE_DEFINITION_ORDER"):
            md.treeprocessors.register(FootnoteReorderingProcessor(self), 'footnote-reorder', 19)

        # Insert a tree-processor that will run after inline is done.
        # In this tree-processor we want to check our duplicate footnote tracker
        # And add additional `backrefs` to the footnote pointing back to the
        # duplicated references.
        md.treeprocessors.register(FootnotePostTreeprocessor(self), 'footnote-duplicate', 15)

        # Insert a postprocessor after amp_substitute processor
        md.postprocessors.register(FootnotePostprocessor(self), 'footnote', 25)

    def reset(self) -> None:
        """ Clear footnotes on reset, and prepare for distinct document. """
        self.footnote_order: list[str] = []
        self.footnotes: OrderedDict[str, str] = OrderedDict()
        self.unique_prefix += 1
        self.found_refs = {}
        self.used_refs = set()

    def unique_ref(self, reference: str, found: bool = False) -> str:
        """ Get a unique reference if there are duplicates. """
        if not found:
            return reference

        b = reference
        while reference in self.used_refs:
            ref, rest = reference.split(self.get_separator(), 1)
            m = RE_REF_ID.match(ref)
            if m:
                reference = '%s%d%s%s' % (m.group(1), int(m.group(2))+1, self.get_separator(), rest)
            else:
                reference = '%s%d%s%s' % (ref, 2, self.get_separator(), rest)

        self.used_refs.add(reference)
        if b in self.found_refs:
            self.found_refs[b] += 1
        else:
            self.found_refs[b] = 1
        return reference

    def findFootnotesPlaceholder(
        self, root: etree.Element
    ) -> tuple[etree.Element, etree.Element, bool] | None:
        """ Return ElementTree Element that contains Footnote placeholder. """
        def finder(element):
            for e in element:
                if e.text:
                    if e.text.find(self.getConfig("PLACE_MARKER")) > -1:
                        return e, element, True
                if e.tail:
                    if e.tail.find(self.getConfig("PLACE_MARKER")) > -1:
                        return e, element, False
                f = finder(e)
                if f is not None:
                    return f
            return None

        d = finder(root)
        return d

    def setFootnote(self, id: str, text: str) -> None:
        """ Store a footnote for later retrieval. """
        self.footnotes[id] = text

    def addFootnoteRef(self, id: str) -> None:
        """ Store a footnote reference id in order of appearance. """
        if id not in self.footnote_order:
            self.footnote_order.append(id)

    def get_separator(self) -> str:
        """ Get the footnote separator. """
        return self.getConfig("SEPARATOR")

    def makeFootnoteId(self, id: str) -> str:
        """ Return footnote link id. """
        if self.getConfig("UNIQUE_IDS"):
            return 'fn%s%d-%s' % (self.get_separator(), self.unique_prefix, id)
        else:
            return 'fn{}{}'.format(self.get_separator(), id)

    def makeFootnoteRefId(self, id: str, found: bool = False) -> str:
        """ Return footnote back-link id. """
        if self.getConfig("UNIQUE_IDS"):
            return self.unique_ref('fnref%s%d-%s' % (self.get_separator(), self.unique_prefix, id), found)
        else:
            return self.unique_ref('fnref{}{}'.format(self.get_separator(), id), found)

    def makeFootnotesDiv(self, root: etree.Element) -> etree.Element | None:
        """ Return `div` of footnotes as `etree` Element. """

        if not list(self.footnotes.keys()):
            return None

        c = etree.Element("div")
        c.set('class', 'footnote')
        etree.SubElement(c, "hr")
        g = etree.SubElement(c, "ol")
        h = etree.Element("div")

        for index, id in enumerate(self.footnotes.keys(), start=1):
            e = etree.SubElement(g, "li")
            e.set("id", self.makeFootnoteId(id))
            # Parse footnote with surrogate parent as `li` cannot be used.
            # List block handlers have special logic to deal with `li`.
            # When we are done parsing, we will copy everything over to `li`.
            self.parser.parseChunk(h, self.footnotes[id])
            for d in list(h):
                e.append(d)
                h.remove(d)
            b = etree.Element("a")
            b.set("href", "#" + self.makeFootnoteRefId(id))
            b.set("class", "footnote-backref")
            b.set(
                "title",
                self.getConfig('BACKLINK_TITLE').format(index)
            )
            b.text = FN_BACKLINK_TEXT

            if len(e):
                f = e[-1]
                if f.tag == "p":
                    f.text = f.text + NBSP_PLACEHOLDER
                    f.append(b)
                else:
                    p = etree.SubElement(e, "p")
                    p.append(b)
        return c


class FootnoteBlockProcessor(BlockProcessor):
    """ Find footnote definitions and store for later use. """

    RE = re.compile(r'^[ ]{0,3}\[\^([^\]]*)\]:[ ]*(.*)$', re.MULTILINE)

    def __init__(self, footnotes: FootnoteExtension):
        super().__init__(footnotes.parser)
        self.footnotes = footnotes

    def test(self, parent: etree.Element, block: str) -> bool:
        return True

    def run(self, parent: etree.Element, blocks: list[str]) -> bool:
        """ Find, set, and remove footnote definitions. """
        c = blocks.pop(0)

        m = self.RE.search(c)
        if m:
            id = m.group(1)
            d = [m.group(2)]

            # Handle rest of block
            g = c[m.end():].lstrip('\n')
            f = self.RE.search(g)
            if f:
                # Another footnote exists in the rest of this block.
                # Any content before match is continuation of this footnote, which may be lazily indented.
                b = g[:f.start()].rstrip('\n')
                d[0] = '\n'.join([d[0], self.detab(b)]).lstrip('\n')
                # Add back to blocks everything from beginning of match forward for next iteration.
                blocks.insert(0, g[f.start():])
            else:
                # All remaining lines of block are continuation of this footnote, which may be lazily indented.
                d[0] = '\n'.join([d[0], self.detab(g)]).strip('\n')

                # Check for child elements in remaining blocks.
                d.extend(self.detectTabbed(blocks))

            e = "\n\n".join(d)
            self.footnotes.setFootnote(id, e.rstrip())

            if c[:m.start()].strip():
                # Add any content before match back to blocks as separate block
                blocks.insert(0, c[:m.start()].rstrip('\n'))
            return True
        # No match. Restore block.
        blocks.insert(0, c)
        return False

    def detectTabbed(self, blocks: list[str]) -> list[str]:
        """ Find indented text and remove indent before further processing.

        Returns:
            A list of blocks with indentation removed.
        """
        d = []
        while blocks:
            if blocks[0].startswith(' '*4):
                c = blocks.pop(0)
                # Check for new footnotes within this block and split at new footnote.
                m = self.RE.search(c)
                if m:
                    # Another footnote exists in this block.
                    # Any content before match is continuation of this footnote, which may be lazily indented.
                    b = c[:m.start()].rstrip('\n')
                    d.append(self.detab(b))
                    # Add back to blocks everything from beginning of match forward for next iteration.
                    blocks.insert(0, c[m.start():])
                    # End of this footnote.
                    break
                else:
                    # Entire block is part of this footnote.
                    d.append(self.detab(c))
            else:
                # End of this footnote.
                break
        return d

    def detab(self, block: str) -> str:
        """ Remove one level of indent from a block.

        Preserve lazily indented blocks by only removing indent from indented lines.
        """
        b = block.split('\n')
        for i, line in enumerate(b):
            if line.startswith(' '*4):
                b[i] = line[4:]
        return '\n'.join(b)


class FootnoteInlineProcessor(InlineProcessor):
    """ `InlineProcessor` for footnote markers in a document's body text. """

    def __init__(self, pattern: str, footnotes: FootnoteExtension):
        super().__init__(pattern)
        self.footnotes = footnotes

    def handleMatch(self, m: re.Match[str], data: str) -> tuple[etree.Element | None, int | None, int | None]:
        id = m.group(1)
        if id in self.footnotes.footnotes.keys():
            self.footnotes.addFootnoteRef(id)

            if not self.footnotes.getConfig("USE_DEFINITION_ORDER"):
                # Order by reference
                b = self.footnotes.footnote_order.index(id) + 1
            else:
                # Order by definition
                b = list(self.footnotes.footnotes.keys()).index(id) + 1

            c = etree.Element("sup")
            a = etree.SubElement(c, "a")
            c.set('id', self.footnotes.makeFootnoteRefId(id, found=True))
            a.set('href', '#' + self.footnotes.makeFootnoteId(id))
            a.set('class', 'footnote-ref')
            a.text = self.footnotes.getConfig("SUPERSCRIPT_TEXT").format(b)
            return c, m.start(0), m.end(0)
        else:
            return None, None, None


class FootnotePostTreeprocessor(Treeprocessor):
    """ Amend footnote div with duplicates. """

    def __init__(self, footnotes: FootnoteExtension):
        self.footnotes = footnotes

    def add_duplicates(self, li: etree.Element, duplicates: int) -> None:
        """ Adjust current `li` and add the duplicates: `fnref2`, `fnref3`, etc. """
        for d in li.iter('a'):
            # Find the link that needs to be duplicated.
            if d.attrib.get('class', '') == 'footnote-backref':
                ref, rest = d.attrib['href'].split(self.footnotes.get_separator(), 1)
                # Duplicate link the number of times we need to
                # and point the to the appropriate references.
                e = []
                for c in range(2, duplicates + 1):
                    f = copy.deepcopy(d)
                    f.attrib['href'] = '%s%d%s%s' % (ref, c, self.footnotes.get_separator(), rest)
                    e.append(f)
                    self.offset += 1
                # Add all the new duplicate links.
                b = list(li)[-1]
                for d in e:
                    b.append(d)
                break

    def get_num_duplicates(self, li: etree.Element) -> int:
        """ Get the number of duplicate refs of the footnote. """
        fn, rest = li.attrib.get('id', '').split(self.footnotes.get_separator(), 1)
        b = '{}ref{}{}'.format(fn, self.footnotes.get_separator(), rest)
        return self.footnotes.found_refs.get(b, 0)

    def handle_duplicates(self, parent: etree.Element) -> None:
        """ Find duplicate footnotes and format and add the duplicates. """
        for c in list(parent):
            # Check number of duplicates footnotes and insert
            # additional links if needed.
            b = self.get_num_duplicates(c)
            if b > 1:
                self.add_duplicates(c, b)

    def run(self, root: etree.Element) -> None:
        """ Crawl the footnote div and add missing duplicate footnotes. """
        self.offset = 0
        for b in root.iter('div'):
            if b.attrib.get('class', '') == 'footnote':
                # Footnotes should be under the first ordered list under
                # the footnote div.  So once we find it, quit.
                for c in b.iter('ol'):
                    self.handle_duplicates(c)
                    break


class FootnoteTreeprocessor(Treeprocessor):
    """ Build and append footnote div to end of document. """

    def __init__(self, footnotes: FootnoteExtension):
        self.footnotes = footnotes

    def run(self, root: etree.Element) -> None:
        b = self.footnotes.makeFootnotesDiv(root)
        if b is not None:
            d = self.footnotes.findFootnotesPlaceholder(root)
            if d:
                child, parent, isText = d
                c = list(parent).index(child)
                if isText:
                    parent.remove(child)
                    parent.insert(c, b)
                else:
                    parent.insert(c + 1, b)
                    child.tail = None
            else:
                root.append(b)


class FootnoteReorderingProcessor(Treeprocessor):
    """ Reorder list items in the footnotes div. """

    def __init__(self, footnotes: FootnoteExtension):
        self.footnotes = footnotes

    def run(self, root: etree.Element) -> None:
        if not self.footnotes.footnotes:
            return
        if self.footnotes.footnote_order != list(self.footnotes.footnotes.keys()):
            for b in root.iter('div'):
                if b.attrib.get('class', '') == 'footnote':
                    self.reorder_footnotes(b)
                    break

    def reorder_footnotes(self, parent: etree.Element) -> None:
        e = parent.find('ol')
        parent.remove(e)
        c = e.findall('li')

        def order_by_id(li) -> int:
            id = li.attrib.get('id', '').split(self.footnotes.get_separator(), 1)[-1]
            return (
                self.footnotes.footnote_order.index(id)
                if id in self.footnotes.footnote_order
                else len(self.footnotes.footnotes)
            )

        c = sorted(c, key=order_by_id)

        d = etree.SubElement(parent, 'ol')

        for index, item in enumerate(c, start=1):
            b = item.find('.//a[@class="footnote-backref"]')
            b.set("title", self.footnotes.getConfig("BACKLINK_TITLE").format(index))
            d.append(item)


class FootnotePostprocessor(Postprocessor):
    """ Replace placeholders with html entities. """
    def __init__(self, footnotes: FootnoteExtension):
        self.footnotes = footnotes

    def run(self, text: str) -> str:
        text = text.replace(
            FN_BACKLINK_TEXT, self.footnotes.getConfig("BACKLINK_TEXT")
        )
        return text.replace(NBSP_PLACEHOLDER, "&#160;")


def makeExtension(**kwargs):  # pragma: no cover
    """ Return an instance of the `FootnoteExtension` """
    return FootnoteExtension(**kwargs)
