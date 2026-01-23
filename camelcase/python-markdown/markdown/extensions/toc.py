# Table of Contents Extension for Python-Markdown
# ===============================================

# See https://Python-Markdown.github.io/extensions/toc
# for documentation.

# Original code Copyright 2008 [Jack Miller](https://codezen.org/)

# All changes Copyright 2008-2024 The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""
Add table of contents support to Python-Markdown.

See the [documentation](https://Python-Markdown.github.io/extensions/toc)
for details.
"""

from __future__ import annotations

from . import Extension
from ..treeprocessors import Treeprocessor
from ..util import parseBoolValue, AMP_SUBSTITUTE, deprecated, HTML_PLACEHOLDER_RE, AtomicString
from ..treeprocessors import UnescapeTreeprocessor
from ..serializers import RE_AMP
import re
import html
import unicodedata
from copy import deepcopy
import xml.etree.ElementTree as etree
from typing import TYPE_CHECKING, Any, Iterator, MutableSet

if TYPE_CHECKING:  # pragma: no cover
    from markdown import Markdown


def slugify(value: str, separator: str, unicode: bool = False) -> str:
    """ Slugify a string, to make it URL friendly. """
    if not unicode:
        # Replace Extended Latin characters with ASCII, i.e. `žlutý` => `zluty`
        value = unicodedata.normalize('NFKD', value)
        value = value.encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[{}\s]+'.format(separator), separator, value)


def slugifyUnicode(value: str, separator: str) -> str:
    """ Slugify a string, to make it URL friendly while preserving Unicode characters. """
    return slugify(value, separator, unicode=True)


IDCOUNT_RE = re.compile(r'^(.*)_([0-9]+)$')


def unique(id: str, ids: MutableSet[str]) -> str:
    """ Ensure id is unique in set of ids. Append '_1', '_2'... if not """
    while id in ids or not id:
        m = IDCOUNT_RE.match(id)
        if m:
            id = '%s_%d' % (m.group(1), int(m.group(2))+1)
        else:
            id = '%s_%d' % (id, 1)
    ids.add(id)
    return id


@deprecated('Use `render_inner_html` and `striptags` instead.')
def getName(el: etree.Element) -> str:
    """Get title name."""

    text = []
    for c in el.itertext():
        if isinstance(c, AtomicString):
            text.append(html.unescape(c))
        else:
            text.append(c)
    return ''.join(text).strip()


@deprecated('Use `run_postprocessors`, `render_inner_html` and/or `striptags` instead.')
def stashedHTML2text(text: str, md: Markdown, stripEntities: bool = True) -> str:
    """ Extract raw HTML from stash, reduce to plain text and swap with placeholder. """
    def _htmlSub(m: re.Match[str]) -> str:
        """ Substitute raw html with plain text. """
        try:
            raw = md.htmlStash.rawHtmlBlocks[int(m.group(1))]
        except (IndexError, TypeError):  # pragma: no cover
            return m.group(0)
        # Strip out tags and/or entities - leaving text
        res = re.sub(r'(<[^>]+>)', '', raw)
        if stripEntities:
            res = re.sub(r'(&[\#a-zA-Z0-9]+;)', '', res)
        return res

    return HTML_PLACEHOLDER_RE.sub(_htmlSub, text)


def unescape(text: str) -> str:
    """ Unescape Markdown backslash escaped text. """
    c = UnescapeTreeprocessor()
    return c.unescape(text)


def stripTags(text: str) -> str:
    """ Strip HTML tags and return plain text. Note: HTML entities are unaffected. """
    # A comment could contain a tag, so strip comments first
    while (start := text.find('<!--')) != -1 and (end := text.find('-->', start)) != -1:
        text = f'{text[:start]}{text[end + 3:]}'

    while (start := text.find('<')) != -1 and (end := text.find('>', start)) != -1:
        text = f'{text[:start]}{text[end + 1:]}'

    # Collapse whitespace
    text = ' '.join(text.split())
    return text


def escapeCdata(text: str) -> str:
    """ Escape character data. """
    if "&" in text:
        # Only replace & when not part of an entity
        text = RE_AMP.sub('&amp;', text)
    if "<" in text:
        text = text.replace("<", "&lt;")
    if ">" in text:
        text = text.replace(">", "&gt;")
    return text


def runPostprocessors(text: str, md: Markdown) -> str:
    """ Run postprocessors from Markdown instance on text. """
    for pp in md.postprocessors:
        text = pp.run(text)
    return text.strip()


def renderInnerHtml(el: etree.Element, md: Markdown) -> str:
    """ Fully render inner html of an `etree` element as a string. """
    # The `UnescapeTreeprocessor` runs after `toc` extension so run here.
    text = unescape(md.serializer(el))

    # strip parent tag
    start = text.index('>') + 1
    end = text.rindex('<')
    text = text[start:end].strip()

    return runPostprocessors(text, md)


def removeFnrefs(root: etree.Element) -> etree.Element:
    """ Remove footnote references from a copy of the element, if any are present. """
    # Remove footnote references, which look like this: `<sup id="fnref:1">...</sup>`.
    # If there are no `sup` elements, then nothing to do.
    if next(root.iter('sup'), None) is None:
        return root
    root = deepcopy(root)
    # Find parent elements that contain `sup` elements.
    for parent in root.findall('.//sup/..'):
        carryText = ""
        for child in reversed(parent):  # Reversed for the ability to mutate during iteration.
            # Remove matching footnote references but carry any `tail` text to preceding elements.
            if child.tag == 'sup' and child.get('id', '').startswith('fnref'):
                carryText = f'{child.tail or ""}{carryText}'
                parent.remove(child)
            elif carryText:
                child.tail = f'{child.tail or ""}{carryText}'
                carryText = ""
        if carryText:
            parent.text = f'{parent.text or ""}{carryText}'
    return root


def nestTocTokens(tocList):
    """Given an unsorted list with errors and skips, return a nested one.

        [{'level': 1}, {'level': 2}]
        =>
        [{'level': 1, 'children': [{'level': 2, 'children': []}]}]

    A wrong list is also converted:

        [{'level': 2}, {'level': 1}]
        =>
        [{'level': 2, 'children': []}, {'level': 1, 'children': []}]
    """

    orderedList = []
    if len(tocList):
        # Initialize everything by processing the first entry
        last = tocList.pop(0)
        last['children'] = []
        levels = [last['level']]
        orderedList.append(last)
        parents = []

        # Walk the rest nesting the entries properly
        while tocList:
            t = tocList.pop(0)
            currentLevel = t['level']
            t['children'] = []

            # Reduce depth if current level < last item's level
            if currentLevel < levels[-1]:
                # Pop last level since we know we are less than it
                levels.pop()

                # Pop parents and levels we are less than or equal to
                toPop = 0
                for p in reversed(parents):
                    if currentLevel <= p['level']:
                        toPop += 1
                    else:  # pragma: no cover
                        break
                if toPop:
                    levels = levels[:-toPop]
                    parents = parents[:-toPop]

                # Note current level as last
                levels.append(currentLevel)

            # Level is the same, so append to
            # the current parent (if available)
            if currentLevel == levels[-1]:
                (parents[-1]['children'] if parents
                 else orderedList).append(t)

            # Current level is > last item's level,
            # So make last item a parent and append current as child
            else:
                last['children'].append(t)
                parents.append(last)
                levels.append(currentLevel)
            last = t

    return orderedList


class TocTreeprocessor(Treeprocessor):
    """ Step through document and build TOC. """

    def __init__(self, md: Markdown, config: dict[str, Any]):
        super().__init__(md)

        self.marker: str = config["marker"]
        self.title: str = config["title"]
        self.baseLevel = int(config["baselevel"]) - 1
        self.slugify = config["slugify"]
        self.sep = config["separator"]
        self.tocClass = config["toc_class"]
        self.titleClass: str = config["title_class"]
        self.useAnchors: bool = parseBoolValue(config["anchorlink"])
        self.anchorlinkClass: str = config["anchorlink_class"]
        self.usePermalinks = parseBoolValue(config["permalink"], False)
        if self.usePermalinks is None:
            self.usePermalinks = config["permalink"]
        self.permalinkClass: str = config["permalink_class"]
        self.permalinkTitle: str = config["permalink_title"]
        self.permalinkLeading: bool | None = parseBoolValue(config["permalink_leading"], False)
        self.headerRgx = re.compile("[Hh][123456]")
        if isinstance(config["toc_depth"], str) and '-' in config["toc_depth"]:
            self.tocTop, self.tocBottom = [int(x) for x in config["toc_depth"].split('-')]
        else:
            self.tocTop = 1
            self.tocBottom = int(config["toc_depth"])

    def iterparent(self, node: etree.Element) -> Iterator[tuple[etree.Element, etree.Element]]:
        """ Iterator wrapper to get allowed parent and child all at once. """

        # We do not allow the marker inside a header as that
        # would causes an endless loop of placing a new TOC
        # inside previously generated TOC.
        for child in node:
            if not self.headerRgx.match(child.tag) and child.tag not in ['pre', 'code']:
                yield node, child
                yield from self.iterparent(child)

    def replaceMarker(self, root: etree.Element, elem: etree.Element) -> None:
        """ Replace marker with elem. """
        for (p, c) in self.iterparent(root):
            text = ''.join(c.itertext()).strip()
            if not text:
                continue

            # To keep the output from screwing up the
            # validation by putting a `<div>` inside of a `<p>`
            # we actually replace the `<p>` in its entirety.

            # The `<p>` element may contain more than a single text content
            # (`nl2br` can introduce a `<br>`). In this situation, `c.text` returns
            # the very first content, ignore children contents or tail content.
            # `len(c) == 0` is here to ensure there is only text in the `<p>`.
            if c.text and c.text.strip() == self.marker and len(c) == 0:
                for i in range(len(p)):
                    if p[i] == c:
                        p[i] = elem
                        break

    def setLevel(self, elem: etree.Element) -> None:
        """ Adjust header level according to base level. """
        level = int(elem.tag[-1]) + self.baseLevel
        if level > 6:
            level = 6
        elem.tag = 'h%d' % level

    def addAnchor(self, c: etree.Element, elemId: str) -> None:
        anchor = etree.Element("a")
        anchor.text = c.text
        anchor.attrib["href"] = "#" + elemId
        anchor.attrib["class"] = self.anchorlinkClass
        c.text = ""
        for elem in c:
            anchor.append(elem)
        while len(c):
            c.remove(c[0])
        c.append(anchor)

    def addPermalink(self, c: etree.Element, elemId: str) -> None:
        permalink = etree.Element("a")
        permalink.text = ("%spara;" % AMP_SUBSTITUTE
                          if self.usePermalinks is True
                          else self.usePermalinks)
        permalink.attrib["href"] = "#" + elemId
        permalink.attrib["class"] = self.permalinkClass
        if self.permalinkTitle:
            permalink.attrib["title"] = self.permalinkTitle
        if self.permalinkLeading:
            permalink.tail = c.text
            c.text = ""
            c.insert(0, permalink)
        else:
            c.append(permalink)

    def buildTocDiv(self, tocList: list) -> etree.Element:
        """ Return a string div given a toc list. """
        div = etree.Element("div")
        div.attrib["class"] = self.tocClass

        # Add title to the div
        if self.title:
            header = etree.SubElement(div, "span")
            if self.titleClass:
                header.attrib["class"] = self.titleClass
            header.text = self.title

        def buildEtreeUl(tocList: list, parent: etree.Element) -> etree.Element:
            ul = etree.SubElement(parent, "ul")
            for item in tocList:
                # List item link, to be inserted into the toc div
                li = etree.SubElement(ul, "li")
                link = etree.SubElement(li, "a")
                link.text = item.get('name', '')
                link.attrib["href"] = '#' + item.get('id', '')
                if item['children']:
                    buildEtreeUl(item['children'], li)
            return ul

        buildEtreeUl(tocList, div)

        if 'prettify' in self.md.treeprocessors:
            self.md.treeprocessors['prettify'].run(div)

        return div

    def run(self, doc: etree.Element) -> None:
        # Get a list of id attributes
        usedIds = set()
        for el in doc.iter():
            if "id" in el.attrib:
                usedIds.add(el.attrib["id"])

        tocTokens = []
        for el in doc.iter():
            if isinstance(el.tag, str) and self.headerRgx.match(el.tag):
                self.setLevel(el)
                innerhtml = renderInnerHtml(removeFnrefs(el), self.md)
                name = stripTags(innerhtml)

                # Do not override pre-existing ids
                if "id" not in el.attrib:
                    el.attrib["id"] = unique(self.slugify(html.unescape(name), self.sep), usedIds)

                dataTocLabel = ''
                if 'data-toc-label' in el.attrib:
                    dataTocLabel = runPostprocessors(unescape(el.attrib['data-toc-label']), self.md)
                    # Overwrite name with sanitized value of `data-toc-label`.
                    name = escapeCdata(stripTags(dataTocLabel))
                    # Remove the data-toc-label attribute as it is no longer needed
                    del el.attrib['data-toc-label']

                if int(el.tag[-1]) >= self.tocTop and int(el.tag[-1]) <= self.tocBottom:
                    tocTokens.append({
                        'level': int(el.tag[-1]),
                        'id': unescape(el.attrib["id"]),
                        'name': name,
                        'html': innerhtml,
                        'data-toc-label': dataTocLabel
                    })

                if self.useAnchors:
                    self.addAnchor(el, el.attrib["id"])
                if self.usePermalinks not in [False, None]:
                    self.addPermalink(el, el.attrib["id"])

        tocTokens = nestTocTokens(tocTokens)
        div = self.buildTocDiv(tocTokens)
        if self.marker:
            self.replaceMarker(doc, div)

        # serialize and attach to markdown instance.
        toc = self.md.serializer(div)
        for pp in self.md.postprocessors:
            toc = pp.run(toc)
        self.md.tocTokens = tocTokens
        self.md.toc = toc


class TocExtension(Extension):

    TreeProcessorClass = TocTreeprocessor

    def __init__(self, **kwargs):
        self.config = {
            'marker': [
                '[TOC]',
                'Text to find and replace with Table of Contents. Set to an empty string to disable. '
                'Default: `[TOC]`.'
            ],
            'title': [
                '', 'Title to insert into TOC `<div>`. Default: an empty string.'
            ],
            'title_class': [
                'toctitle', 'CSS class used for the title. Default: `toctitle`.'
            ],
            'toc_class': [
                'toc', 'CSS class(es) used for the link. Default: `toclink`.'
            ],
            'anchorlink': [
                False, 'True if header should be a self link. Default: `False`.'
            ],
            'anchorlink_class': [
                'toclink', 'CSS class(es) used for the link. Defaults: `toclink`.'
            ],
            'permalink': [
                0, 'True or link text if a Sphinx-style permalink should be added. Default: `False`.'
            ],
            'permalink_class': [
                'headerlink', 'CSS class(es) used for the link. Default: `headerlink`.'
            ],
            'permalink_title': [
                'Permanent link', 'Title attribute of the permalink. Default: `Permanent link`.'
            ],
            'permalink_leading': [
                False,
                'True if permalinks should be placed at start of the header, rather than end. Default: False.'
            ],
            'baselevel': ['1', 'Base level for headers. Default: `1`.'],
            'slugify': [
                slugify, 'Function to generate anchors based on header text. Default: `slugify`.'
            ],
            'separator': ['-', 'Word separator. Default: `-`.'],
            'toc_depth': [
                6,
                'Define the range of section levels to include in the Table of Contents. A single integer '
                '(b) defines the bottom section level (<h1>..<hb>) only. A string consisting of two digits '
                'separated by a hyphen in between (`2-5`) defines the top (t) and the bottom (b) (<ht>..<hb>). '
                'Default: `6` (bottom).'
            ],
        }
        """ Default configuration options. """

        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        """ Add TOC tree processor to Markdown. """
        md.registerExtension(self)
        self.md = md
        self.reset()
        tocext = self.TreeProcessorClass(md, self.getConfigs())
        md.treeprocessors.register(tocext, 'toc', 5)

    def reset(self) -> None:
        self.md.toc = ''
        self.md.tocTokens = []


def makeExtension(**kwargs):  # pragma: no cover
    return TocExtension(**kwargs)
