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


def buildTreeprocessors(md: Markdown, **kwargs: Any) -> util.Registry[Treeprocessor]:
    """ Build the default  `treeprocessors` for Markdown. """
    treeprocessors = util.Registry()
    treeprocessors.register(InlineProcessor(md), 'inline', 20)
    treeprocessors.register(PrettifyTreeprocessor(md), 'prettify', 10)
    treeprocessors.register(UnescapeTreeprocessor(md), 'unescape', 0)
    return treeprocessors


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
        self.__placeholderPrefix = util.INLINE_PLACEHOLDER_PREFIX
        self.__placeholderSuffix = util.ETX
        self.__placeholderLength = 4 + len(self.__placeholderPrefix) \
                                      + len(self.__placeholderSuffix)
        self.__placeholderRe = util.INLINE_PLACEHOLDER_RE
        self.md = md
        self.inlinePatterns = md.inlinePatterns
        self.ancestors: list[str] = []

    def __makeplaceholder(self, type: str) -> tuple[str, str]:
        """ Generate a placeholder """
        id = "%04d" % len(self.stashedNodes)
        hash = util.INLINE_PLACEHOLDER % id
        return hash, id

    def __findplaceholder(self, data: str, index: int) -> tuple[str | None, int]:
        """
        Extract id from data string, start from index.

        Arguments:
            data: String.
            index: Index, from which we start search.

        Returns:
            Placeholder id and string index, after the found placeholder.

        """
        m = self.__placeholderRe.search(data, index)
        if m:
            return m.group(1), m.end()
        else:
            return None, index + 1

    def __stashnode(self, node: etree.Element | str, type: str) -> str:
        """ Add node to stash. """
        placeholder, id = self.__makeplaceholder(type)
        self.stashedNodes[id] = node
        return placeholder

    def __handleinline(self, data: str, patternIndex: int = 0) -> str:
        """
        Process string with inline patterns and replace it with placeholders.

        Arguments:
            data: A line of Markdown text.
            patternIndex: The index of the `inlinePattern` to start with.

        Returns:
            String with placeholders.

        """
        if not isinstance(data, util.AtomicString):
            startIndex = 0
            count = len(self.inlinePatterns)
            while patternIndex < count:
                data, matched, startIndex = self.__applypattern(
                    self.inlinePatterns[patternIndex], data, patternIndex, startIndex
                )
                if not matched:
                    patternIndex += 1
        return data

    def __processelementtext(self, node: etree.Element, subnode: etree.Element, isText: bool = True) -> None:
        """
        Process placeholders in `Element.text` or `Element.tail`
        of Elements popped from `self.stashed_nodes`.

        Arguments:
            node: Parent node.
            subnode: Processing node.
            isText: Boolean variable, True - it's text, False - it's a tail.

        """
        if isText:
            text = subnode.text
            subnode.text = None
        else:
            text = subnode.tail
            subnode.tail = None

        childResult = self.__processplaceholders(text, subnode, isText)

        if not isText and node is not subnode:
            pos = list(node).index(subnode) + 1
        else:
            pos = 0

        childResult.reverse()
        for newChild in childResult:
            node.insert(pos, newChild[0])

    def __processplaceholders(
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
                if result:
                    if result[-1][0].tail:
                        result[-1][0].tail += text
                    else:
                        result[-1][0].tail = text
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
        result = []
        strartIndex = 0
        while data:
            index = data.find(self.__placeholderPrefix, strartIndex)
            if index != -1:
                id, phEndIndex = self.__findplaceholder(data, index)

                if id in self.stashedNodes:
                    node = self.stashedNodes.get(id)

                    if index > 0:
                        text = data[strartIndex:index]
                        linkText(text)

                    if not isinstance(node, str):  # it's Element
                        for child in [node] + list(node):
                            if child.tail:
                                if child.tail.strip():
                                    self.__processelementtext(
                                        node, child, False
                                    )
                            if child.text:
                                if child.text.strip():
                                    self.__processelementtext(child, child)
                    else:  # it's just a string
                        linkText(node)
                        strartIndex = phEndIndex
                        continue

                    strartIndex = phEndIndex
                    result.append((node, self.ancestors[:]))

                else:  # wrong placeholder
                    end = index + len(self.__placeholderPrefix)
                    linkText(data[strartIndex:end])
                    strartIndex = end
            else:
                text = data[strartIndex:]
                if isinstance(data, util.AtomicString):
                    # We don't want to loose the `AtomicString`
                    text = util.AtomicString(text)
                linkText(text)
                data = ""

        return result

    def __applypattern(
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
        newStyle = isinstance(pattern, inlinepatterns.InlineProcessor)

        for exclude in pattern.ANCESTOR_EXCLUDES:
            if exclude.lower() in self.ancestors:
                return data, False, 0

        if newStyle:
            match = None
            # Since `handleMatch` may reject our first match,
            # we iterate over the buffer looking for matches
            # until we can't find any more.
            for match in pattern.getCompiledRegExp().finditer(data, startIndex):
                node, start, end = pattern.handleMatch(match, data)
                if start is None or end is None:
                    startIndex += match.end(0)
                    match = None
                    continue
                break
        else:  # pragma: no cover
            match = pattern.getCompiledRegExp().match(data[startIndex:])
            leftData = data[:startIndex]

        if not match:
            return data, False, 0

        if not newStyle:  # pragma: no cover
            node = pattern.handleMatch(match)
            start = match.start(0)
            end = match.end(0)

        if node is None:
            return data, True, end

        if not isinstance(node, str):
            if not isinstance(node.text, util.AtomicString):
                # We need to process current node too
                for child in [node] + list(node):
                    if not isString(node):
                        if child.text:
                            self.ancestors.append(child.tag.lower())
                            child.text = self.__handleinline(
                                child.text, patternIndex + 1
                            )
                            self.ancestors.pop()
                        if child.tail:
                            child.tail = self.__handleinline(
                                child.tail, patternIndex
                            )

        placeholder = self.__stashnode(node, pattern.type())

        if newStyle:
            return "{}{}{}".format(data[:start],
                                   placeholder, data[end:]), True, 0
        else:  # pragma: no cover
            return "{}{}{}{}".format(leftData,
                                     match.group(1),
                                     placeholder, match.groups()[-1]), True, 0

    def __buildAncestors(self, parent: etree.Element | None, parents: list[str]) -> None:
        """Build the ancestor list."""
        ancestors = []
        while parent is not None:
            if parent is not None:
                ancestors.append(parent.tag.lower())
            parent = self.parentMap.get(parent)
        ancestors.reverse()
        parents.extend(ancestors)

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
        self.stashedNodes: dict[str, etree.Element | str] = {}

        # Ensure a valid parent list, but copy passed in lists
        # to ensure we don't have the user accidentally change it on us.
        treeParents = [] if ancestors is None else ancestors[:]

        self.parentMap = {c: p for p in tree.iter() for c in p}
        stack = [(tree, treeParents)]

        while stack:
            currElement, parents = stack.pop(0)

            self.ancestors = parents
            self.__buildAncestors(currElement, self.ancestors)

            insertQueue = []
            for child in currElement:
                if child.text and not isinstance(
                    child.text, util.AtomicString
                ):
                    self.ancestors.append(child.tag.lower())
                    text = child.text
                    child.text = None
                    lst = self.__processplaceholders(
                        self.__handleinline(text), child
                    )
                    for item in lst:
                        self.parentMap[item[0]] = child
                    stack += lst
                    insertQueue.append((child, lst))
                    self.ancestors.pop()
                if child.tail:
                    tail = self.__handleinline(child.tail)
                    dumby = etree.Element('d')
                    child.tail = None
                    tailResult = self.__processplaceholders(tail, dumby, False)
                    if dumby.tail:
                        child.tail = dumby.tail
                    pos = list(currElement).index(child) + 1
                    tailResult.reverse()
                    for newChild in tailResult:
                        self.parentMap[newChild[0]] = currElement
                        currElement.insert(pos, newChild[0])
                if len(child):
                    self.parentMap[child] = currElement
                    stack.append((child, self.ancestors[:]))

            for element, lst in insertQueue:
                for i, obj in enumerate(lst):
                    newChild = obj[0]
                    element.insert(i, newChild)
        return tree


class PrettifyTreeprocessor(Treeprocessor):
    """ Add line breaks to the html document. """

    def _prettifyetree(self, elem: etree.Element) -> None:
        """ Recursively add line breaks to `ElementTree` children. """

        i = "\n"
        if self.md.isBlockLevel(elem.tag) and elem.tag not in ['code', 'pre']:
            if (not elem.text or not elem.text.strip()) \
                    and len(elem) and self.md.isBlockLevel(elem[0].tag):
                elem.text = i
            for e in elem:
                if self.md.isBlockLevel(e.tag):
                    self._prettifyetree(e)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i

    def run(self, root: etree.Element) -> None:
        """ Add line breaks to `Element` object and its children. """

        self._prettifyetree(root)
        # Do `<br />`'s separately as they are often in the middle of
        # inline content and missed by `_prettifyETree`.
        brs = root.iter('br')
        for br in brs:
            if not br.tail or not br.tail.strip():
                br.tail = '\n'
            else:
                br.tail = '\n%s' % br.tail
        # Clean up extra empty lines at end of code blocks.
        pres = root.iter('pre')
        for pre in pres:
            if len(pre) and pre[0].tag == 'code':
                code = pre[0]
                # Only prettify code containing text only
                if not len(code) and code.text is not None:
                    code.text = util.AtomicString(code.text.rstrip() + '\n')


class UnescapeTreeprocessor(Treeprocessor):
    """ Restore escaped chars """

    RE = re.compile(r'{}(\d+){}'.format(util.STX, util.ETX))

    def _unescape(self, m: re.Match[str]) -> str:
        return chr(int(m.group(1)))

    def unescape(self, text: str) -> str:
        return self.RE.sub(self._unescape, text)

    def run(self, root: etree.Element) -> None:
        """ Loop over all elements and unescape all text. """
        for elem in root.iter():
            # Unescape text content
            if elem.text and not elem.tag == 'code':
                elem.text = self.unescape(elem.text)
            # Unescape tail content
            if elem.tail:
                elem.tail = self.unescape(elem.tail)
            # Unescape attribute values
            for key, value in elem.items():
                elem.set(key, self.unescape(value))
