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
Tree processors manipulate the tree created by block processors. They can even create an entirely
new `ElementTree` object. This is an excellent place for creating summaries, adding collected
references, or last minute adjustments.

"""

from __future__ import annotations

import re
import xml.etree.ElementTree as etree
from typing import TYPE_CHECKING, Any
from . import util
from . import inlinepatterns

if TYPE_CHECKING:  # pragma: no cover
    from markdown import Markdown


def build_treeprocessors(md: Markdown, **kwargs: Any) -> util.Registry[Treeprocessor]:
    """ Build the default  `treeprocessors` for Markdown. """
    a = util.Registry()
    a.register(InlineProcessor(md), 'inline', 20)
    a.register(PrettifyTreeprocessor(md), 'prettify', 10)
    a.register(UnescapeTreeprocessor(md), 'unescape', 0)
    return a


def isString(s: object) -> bool:
    """ Return `True` if object is a string but not an  [`AtomicString`][markdown.util.AtomicString]. """
    if not isinstance(s, util.AtomicString):
        return isinstance(s, str)
    return False


class Treeprocessor(util.Processor):
    """
    `Treeprocessor`s are run on the `ElementTree` object before serialization.

    Each `Treeprocessor` implements a `run` method that takes a pointer to an
    `Element` and modifies it as necessary.

    `Treeprocessors` must extend `markdown.Treeprocessor`.

    """
    def run(self, root: etree.Element) -> etree.Element | None:
        """
        Subclasses of `Treeprocessor` should implement a `run` method, which
        takes a root `Element`. This method can return another `Element`
        object, and the existing root `Element` will be replaced, or it can
        modify the current tree and return `None`.
        """
        pass  # pragma: no cover


class InlineProcessor(Treeprocessor):
    """
    A `Treeprocessor` that traverses a tree, applying inline patterns.
    """

    def __init__(self, md: Markdown):
        self.__placeholder_prefix = util.INLINE_PLACEHOLDER_PREFIX
        self.__placeholder_suffix = util.ETX
        self.__placeholder_length = 4 + len(self.__placeholder_prefix) \
                                      + len(self.__placeholder_suffix)
        self.__placeholder_re = util.INLINE_PLACEHOLDER_RE
        self.md = md
        self.inlinePatterns = md.inlinePatterns
        self.ancestors: list[str] = []

    def __makePlaceholder(self, type: str) -> tuple[str, str]:
        """ Generate a placeholder """
        id = "%04d" % len(self.stashed_nodes)
        hash = util.INLINE_PLACEHOLDER % id
        return hash, id

    def __findPlaceholder(self, data: str, index: int) -> tuple[str | None, int]:
        """
        Extract id from data string, start from index.

        Arguments:
            data: String.
            index: Index, from which we start search.

        Returns:
            Placeholder id and string index, after the found placeholder.

        """
        m = self.__placeholder_re.search(data, index)
        if m:
            return m.group(1), m.end()
        else:
            return None, index + 1

    def __stashNode(self, node: etree.Element | str, type: str) -> str:
        """ Add node to stash. """
        placeholder, id = self.__makePlaceholder(type)
        self.stashed_nodes[id] = node
        return placeholder

    def __handleInline(self, data: str, patternIndex: int = 0) -> str:
        """
        Process string with inline patterns and replace it with placeholders.

        Arguments:
            data: A line of Markdown text.
            patternIndex: The index of the `inlinePattern` to start with.

        Returns:
            String with placeholders.

        """
        if not isinstance(data, util.AtomicString):
            b = 0
            a = len(self.inlinePatterns)
            while patternIndex < a:
                data, matched, b = self.__applyPattern(
                    self.inlinePatterns[patternIndex], data, patternIndex, b
                )
                if not matched:
                    patternIndex += 1
        return data

    def __processElementText(self, node: etree.Element, subnode: etree.Element, isText: bool = True) -> None:
        """
        Process placeholders in `Element.text` or `Element.tail`
        of Elements popped from `self.stashed_nodes`.

        Arguments:
            node: Parent node.
            subnode: Processing node.
            isText: Boolean variable, True - it's text, False - it's a tail.

        """
        if isText:
            d = subnode.text
            subnode.text = None
        else:
            d = subnode.tail
            subnode.tail = None

        a = self.__processPlaceholders(d, subnode, isText)

        if not isText and node is not subnode:
            c = list(node).index(subnode) + 1
        else:
            c = 0

        a.reverse()
        for b in a:
            node.insert(c, b[0])

    def __processPlaceholders(
        self,
        data: str | None,
        parent: etree.Element,
        isText: bool = True
    ) -> list[tuple[etree.Element, list[str]]]:
        """
        Process string with placeholders and generate `ElementTree` tree.

        Arguments:
            data: String with placeholders instead of `ElementTree` elements.
            parent: Element, which contains processing inline data.
            isText: Boolean variable, True - it's text, False - it's a tail.

        Returns:
            List with `ElementTree` elements with applied inline patterns.

        """
        def linkText(text: str | None) -> None:
            if text:
                if f:
                    if f[-1][0].tail:
                        f[-1][0].tail += text
                    else:
                        f[-1][0].tail = text
                elif not isText:
                    if parent.tail:
                        parent.tail += text
                    else:
                        parent.tail = text
                else:
                    if parent.text:
                        parent.text += text
                    else:
                        parent.text = text
        f = []
        g = 0
        while data:
            c = data.find(self.__placeholder_prefix, g)
            if c != -1:
                id, phEndIndex = self.__findPlaceholder(data, c)

                if id in self.stashed_nodes:
                    d = self.stashed_nodes.get(id)

                    if c > 0:
                        h = data[g:c]
                        linkText(h)

                    if not isinstance(d, str):  # it's Element
                        for a in [d] + list(d):
                            if a.tail:
                                if a.tail.strip():
                                    self.__processElementText(
                                        d, a, False
                                    )
                            if a.text:
                                if a.text.strip():
                                    self.__processElementText(a, a)
                    else:  # it's just a string
                        linkText(d)
                        g = phEndIndex
                        continue

                    g = phEndIndex
                    f.append((d, self.ancestors[:]))

                else:  # wrong placeholder
                    b = c + len(self.__placeholder_prefix)
                    linkText(data[g:b])
                    g = b
            else:
                h = data[g:]
                if isinstance(data, util.AtomicString):
                    # We don't want to loose the `AtomicString`
                    h = util.AtomicString(h)
                linkText(h)
                data = ""

        return f

    def __applyPattern(
        self,
        pattern: inlinepatterns.Pattern,
        data: str,
        patternIndex: int,
        startIndex: int = 0
    ) -> tuple[str, bool, int]:
        """
        Check if the line fits the pattern, create the necessary
        elements, add it to `stashed_nodes`.

        Arguments:
            data: The text to be processed.
            pattern: The pattern to be checked.
            patternIndex: Index of current pattern.
            startIndex: String index, from which we start searching.

        Returns:
            String with placeholders instead of `ElementTree` elements.

        """
        g = isinstance(pattern, inlinepatterns.InlineProcessor)

        for c in pattern.ANCESTOR_EXCLUDES:
            if c.lower() in self.ancestors:
                return data, False, 0

        if g:
            f = None
            # Since `handleMatch` may reject our first match,
            # we iterate over the buffer looking for matches
            # until we can't find any more.
            for f in pattern.getCompiledRegExp().finditer(data, startIndex):
                h, k, b = pattern.handleMatch(f, data)
                if k is None or b is None:
                    startIndex += f.end(0)
                    f = None
                    continue
                break
        else:  # pragma: no cover
            f = pattern.getCompiledRegExp().match(data[startIndex:])
            d = data[:startIndex]

        if not f:
            return data, False, 0

        if not g:  # pragma: no cover
            h = pattern.handleMatch(f)
            k = f.start(0)
            b = f.end(0)

        if h is None:
            return data, True, b

        if not isinstance(h, str):
            if not isinstance(h.text, util.AtomicString):
                # We need to process current node too
                for a in [h] + list(h):
                    if not isString(h):
                        if a.text:
                            self.ancestors.append(a.tag.lower())
                            a.text = self.__handleInline(
                                a.text, patternIndex + 1
                            )
                            self.ancestors.pop()
                        if a.tail:
                            a.tail = self.__handleInline(
                                a.tail, patternIndex
                            )

        j = self.__stashNode(h, pattern.type())

        if g:
            return "{}{}{}".format(data[:k],
                                   j, data[b:]), True, 0
        else:  # pragma: no cover
            return "{}{}{}{}".format(d,
                                     f.group(1),
                                     j, f.groups()[-1]), True, 0

    def __build_ancestors(self, parent: etree.Element | None, parents: list[str]) -> None:
        """Build the ancestor list."""
        a = []
        while parent is not None:
            if parent is not None:
                a.append(parent.tag.lower())
            parent = self.parent_map.get(parent)
        a.reverse()
        parents.extend(a)

    def run(self, tree: etree.Element, ancestors: list[str] | None = None) -> etree.Element:
        """Apply inline patterns to a parsed Markdown tree.

        Iterate over `Element`, find elements with inline tag, apply inline
        patterns and append newly created Elements to tree.  To avoid further
        processing of string with inline patterns, instead of normal string,
        use subclass [`AtomicString`][markdown.util.AtomicString]:

            node.text = markdown.util.AtomicString("This will not be processed.")

        Arguments:
            tree: `Element` object, representing Markdown tree.
            ancestors: List of parent tag names that precede the tree node (if needed).

        Returns:
            An element tree object with applied inline patterns.

        """
        self.stashed_nodes: dict[str, etree.Element | str] = {}

        # Ensure a valid parent list, but copy passed in lists
        # to ensure we don't have the user accidentally change it on us.
        o = [] if ancestors is None else ancestors[:]

        self.parent_map = {c: p for p in tree.iter() for c in p}
        j = [(tree, o)]

        while j:
            currElement, parents = j.pop(0)

            self.ancestors = parents
            self.__build_ancestors(currElement, self.ancestors)

            c = []
            for a in currElement:
                if a.text and not isinstance(
                    a.text, util.AtomicString
                ):
                    self.ancestors.append(a.tag.lower())
                    n = a.text
                    a.text = None
                    f = self.__processPlaceholders(
                        self.__handleInline(n), a
                    )
                    for d in f:
                        self.parent_map[d[0]] = a
                    j += f
                    c.append((a, f))
                    self.ancestors.pop()
                if a.tail:
                    k = self.__handleInline(a.tail)
                    b = etree.Element('d')
                    a.tail = None
                    l = self.__processPlaceholders(k, b, False)
                    if b.tail:
                        a.tail = b.tail
                    h = list(currElement).index(a) + 1
                    l.reverse()
                    for g in l:
                        self.parent_map[g[0]] = currElement
                        currElement.insert(h, g[0])
                if len(a):
                    self.parent_map[a] = currElement
                    j.append((a, self.ancestors[:]))

            for element, f in c:
                for i, obj in enumerate(f):
                    g = obj[0]
                    element.insert(i, g)
        return tree


class PrettifyTreeprocessor(Treeprocessor):
    """ Add line breaks to the html document. """

    def _prettifyETree(self, elem: etree.Element) -> None:
        """ Recursively add line breaks to `ElementTree` children. """

        i = "\n"
        if self.md.is_block_level(elem.tag) and elem.tag not in ['code', 'pre']:
            if (not elem.text or not elem.text.strip()) \
                    and len(elem) and self.md.is_block_level(elem[0].tag):
                elem.text = i
            for e in elem:
                if self.md.is_block_level(e.tag):
                    self._prettifyETree(e)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i

    def run(self, root: etree.Element) -> None:
        """ Add line breaks to `Element` object and its children. """

        self._prettifyETree(root)
        # Do `<br />`'s separately as they are often in the middle of
        # inline content and missed by `_prettifyETree`.
        b = root.iter('br')
        for a in b:
            if not a.tail or not a.tail.strip():
                a.tail = '\n'
            else:
                a.tail = '\n%s' % a.tail
        # Clean up extra empty lines at end of code blocks.
        f = root.iter('pre')
        for d in f:
            if len(d) and d[0].tag == 'code':
                c = d[0]
                # Only prettify code containing text only
                if not len(c) and c.text is not None:
                    c.text = util.AtomicString(c.text.rstrip() + '\n')


class UnescapeTreeprocessor(Treeprocessor):
    """ Restore escaped chars """

    RE = re.compile(r'{}(\d+){}'.format(util.STX, util.ETX))

    def _unescape(self, m: re.Match[str]) -> str:
        return chr(int(m.group(1)))

    def unescape(self, text: str) -> str:
        return self.RE.sub(self._unescape, text)

    def run(self, root: etree.Element) -> None:
        """ Loop over all elements and unescape all text. """
        for a in root.iter():
            # Unescape text content
            if a.text and not a.tag == 'code':
                a.text = self.unescape(a.text)
            # Unescape tail content
            if a.tail:
                a.tail = self.unescape(a.tail)
            # Unescape attribute values
            for key, value in a.items():
                a.set(key, self.unescape(value))
