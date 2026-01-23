# Python-Markdown Markdown in HTML Extension
# ===============================

# An implementation of [PHP Markdown Extra](http://michelf.com/projects/php-markdown/extra/)'s
# parsing of Markdown syntax in raw HTML.

# See https://Python-Markdown.github.io/extensions/raw_html
# for documentation.

# Copyright The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""
Parse Markdown syntax within raw HTML.
Based on the implementation in [PHP Markdown Extra](http://michelf.com/projects/php-markdown/extra/).

See the [documentation](https://Python-Markdown.github.io/extensions/raw_html)
for details.
"""

from __future__ import annotations

from . import Extension
from ..blockprocessors import BlockProcessor
from ..preprocessors import Preprocessor
from ..postprocessors import RawHtmlPostprocessor
from .. import util
from ..htmlparser import HTMLExtractor, blankLineRe
import xml.etree.ElementTree as etree
from typing import TYPE_CHECKING, Literal, Mapping

if TYPE_CHECKING:  # pragma: no cover
    from markdown import Markdown


class HTMLExtractorExtra(HTMLExtractor):
    """
    Override `HTMLExtractor` and create `etree` `Elements` for any elements which should have content parsed as
    Markdown.
    """

    def __init__(self, md: Markdown, *args, **kwargs):
        # All block-level tags.
        self.blockLevelTags = set(md.blockLevelElements.copy())
        # Block-level tags in which the content only gets span level parsing
        self.spanTags = set(
            ['address', 'dd', 'dt', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'legend', 'li', 'p', 'summary', 'td', 'th']
        )
        # Block-level tags which never get their content parsed.
        self.rawTags = set(['canvas', 'math', 'option', 'pre', 'script', 'style', 'textarea'])

        super().__init__(md, *args, **kwargs)

        # Block-level tags in which the content gets parsed as blocks
        self.blockTags = set(self.blockLevelTags) - (self.spanTags | self.rawTags | self.emptyTags)
        self.spanAndBlocksTags = self.blockTags | self.spanTags

    def reset(self):
        """Reset this instance.  Loses all unprocessed data."""
        self.mdstack: list[str] = []  # When markdown=1, stack contains a list of tags
        self.treebuilder = etree.TreeBuilder()
        self.mdstate: list[Literal['block', 'span', 'off', None]] = []
        self.mdstarted: list[bool] = []
        super().reset()

    def close(self):
        """Handle any buffered data."""
        super().close()
        # Handle any unclosed tags.
        if self.mdstack:
            # Close the outermost parent. `handle_endtag` will close all unclosed children.
            self.handle_endtag(self.mdstack[0])

    def getElement(self) -> etree.Element:
        """ Return element from `treebuilder` and reset `treebuilder` for later use. """
        element = self.treebuilder.close()
        self.treebuilder = etree.TreeBuilder()
        return element

    def getState(self, tag, attrs: Mapping[str, str]) -> Literal['block', 'span', 'off', None]:
        """ Return state from tag and `markdown` attribute. One of 'block', 'span', or 'off'. """
        mdAttr = attrs.get('markdown', '0')
        if mdAttr == 'markdown':
            # `<tag markdown>` is the same as `<tag markdown='1'>`.
            mdAttr = '1'
        parentState = self.mdstate[-1] if self.mdstate else None
        if parentState == 'off' or (parentState == 'span' and mdAttr != '0'):
            # Only use the parent state if it is more restrictive than the markdown attribute.
            mdAttr = parentState
        if ((mdAttr == '1' and tag in self.blockTags) or
                (mdAttr == 'block' and tag in self.spanAndBlocksTags)):
            return 'block'
        elif ((mdAttr == '1' and tag in self.spanTags) or
              (mdAttr == 'span' and tag in self.spanAndBlocksTags)):
            return 'span'
        elif tag in self.blockLevelTags:
            return 'off'
        else:  # pragma: no cover
            return None

    def handle_starttag(self, tag, attrs):
        # Handle tags that should always be empty and do not specify a closing tag
        if tag in self.emptyTags and (self.atLineStart() or self.intail):
            attrs = {key: value if value is not None else key for key, value in attrs}
            if "markdown" in attrs:
                attrs.pop('markdown')
                element = etree.Element(tag, attrs)
                data = etree.tostring(element, encoding='unicode', method='html')
            else:
                data = self.get_starttag_text()
            self.handleEmptyTag(data, True)
            return

        if (
            tag in self.blockLevelTags and
            (self.atLineStart() or self.intail or self.mdstarted and self.mdstarted[-1])
        ):
            # Valueless attribute (ex: `<tag checked>`) results in `[('checked', None)]`.
            # Convert to `{'checked': 'checked'}`.
            attrs = {key: value if value is not None else key for key, value in attrs}
            state = self.getState(tag, attrs)
            if self.inraw or (state in [None, 'off'] and not self.mdstack):
                # fall back to default behavior
                attrs.pop('markdown', None)
                super().handle_starttag(tag, attrs)
            else:
                if 'p' in self.mdstack and tag in self.blockLevelTags:
                    # Close unclosed 'p' tag
                    self.handle_endtag('p')
                self.mdstate.append(state)
                self.mdstack.append(tag)
                self.mdstarted.append(True)
                attrs['markdown'] = state
                self.treebuilder.start(tag, attrs)

        else:
            # Span level tag
            if self.inraw:
                super().handle_starttag(tag, attrs)
            else:
                text = self.get_starttag_text()
                if self.mdstate and self.mdstate[-1] == "off":
                    self.handle_data(self.md.htmlStash.store(text))
                else:
                    self.handle_data(text)
                if tag in self.CDATA_CONTENT_ELEMENTS:
                    # This is presumably a standalone tag in a code span (see #1036).
                    self.clear_cdata_mode()

    def handle_endtag(self, tag):
        if tag in self.blockLevelTags:
            if self.inraw:
                super().handle_endtag(tag)
            elif tag in self.mdstack:
                # Close element and any unclosed children
                while self.mdstack:
                    item = self.mdstack.pop()
                    self.mdstate.pop()
                    self.mdstarted.pop()
                    self.treebuilder.end(item)
                    if item == tag:
                        break
                if not self.mdstack:
                    # Last item in stack is closed. Stash it
                    element = self.getElement()
                    # Get last entry to see if it ends in newlines
                    # If it is an element, assume there is no newlines
                    item = self.cleandoc[-1] if self.cleandoc else ''
                    # If we only have one newline before block element, add another
                    if not item.endswith('\n\n') and item.endswith('\n'):
                        self.cleandoc.append('\n')

                    # Flatten the HTML structure of "markdown" blocks such that when they
                    # get parsed, content will be parsed similar inside the blocks as it
                    # does outside the block. Having real HTML elements in the tree before
                    # the content adjacent content is processed can cause unpredictable
                    # issues for extensions.
                    current = element
                    last = []
                    while current is not None:
                        for child in list(current):
                            current.remove(child)
                            text = current.text if current.text is not None else ''
                            tail = child.tail if child.tail is not None else ''
                            child.tail = None
                            state = child.attrib.get('markdown', 'off')

                            # Add a newline to tail if it is not just a trailing newline
                            if tail != '\n':
                                tail = '\n' + tail.rstrip('\n')

                            # Ensure there is an empty new line between blocks
                            if not text.endswith('\n\n'):
                                text = text.rstrip('\n') + '\n\n'

                            # Process the block nested under the span appropriately
                            if state in ('span', 'block'):
                                current.text = f'{text}{self.md.htmlStash.store(child)}{tail}'
                                last.append(child)
                            else:
                                # Non-Markdown HTML will not be recursively parsed for Markdown,
                                # so we can just remove markers and leave them unflattened.
                                # Additionally, we don't need to append to our list for further
                                # processing.
                                child.attrib.pop('markdown')
                                [c.attrib.pop('markdown', None) for c in child.iter()]
                                current.text = f'{text}{self.md.htmlStash.store(child)}{tail}'
                        # Target the child elements that have been expanded.
                        current = last.pop(0) if last else None

                    self.cleandoc.append(self.md.htmlStash.store(element))
                    self.cleandoc.append('\n\n')
                    self.state = []
                    # Check if element has a tail
                    if not blankLineRe.match(
                            self.rawdata[self.lineOffset + self.offset + len(self.getEndtagText(tag)):]):
                        # More content exists after `endtag`.
                        self.intail = True
            else:
                # Treat orphan closing tag as a span level tag.
                text = self.getEndtagText(tag)
                if self.mdstate and self.mdstate[-1] == "off":
                    self.handle_data(self.md.htmlStash.store(text))
                else:
                    self.handle_data(text)
        else:
            # Span level tag
            if self.inraw:
                super().handle_endtag(tag)
            else:
                text = self.getEndtagText(tag)
                if self.mdstate and self.mdstate[-1] == "off":
                    self.handle_data(self.md.htmlStash.store(text))
                else:
                    self.handle_data(text)

    def handle_startendtag(self, tag, attrs):
        if tag in self.emptyTags:
            attrs = {key: value if value is not None else key for key, value in attrs}
            if "markdown" in attrs:
                attrs.pop('markdown')
                element = etree.Element(tag, attrs)
                data = etree.tostring(element, encoding='unicode', method='html')
            else:
                data = self.get_starttag_text()
        else:
            data = self.get_starttag_text()
        self.handleEmptyTag(data, isBlock=self.md.isBlockLevel(tag))

    def handle_data(self, data):
        if self.intail and '\n' in data:
            self.intail = False
        if self.inraw or not self.mdstack:
            super().handle_data(data)
        else:
            self.mdstarted[-1] = False
            self.treebuilder.data(data)

    def handleEmptyTag(self, data, isBlock):
        if self.inraw or not self.mdstack:
            super().handleEmptyTag(data, isBlock)
        else:
            if self.atLineStart() and isBlock:
                self.handle_data('\n' + self.md.htmlStash.store(data) + '\n\n')
            elif self.mdstate and self.mdstate[-1] == "off":
                self.handle_data(self.md.htmlStash.store(data))
            else:
                self.handle_data(data)

    def parse_pi(self, i: int) -> int:
        if self.atLineStart() or self.intail or self.mdstack:
            # The same override exists in `HTMLExtractor` without the check
            # for `mdstack`. Therefore, use parent of `HTMLExtractor` instead.
            return super(HTMLExtractor, self).parse_pi(i)
        # This is not the beginning of a raw block so treat as plain data
        # and avoid consuming any tags which may follow (see #1066).
        self.handle_data('<?')
        return i + 2

    def parse_html_declaration(self, i: int) -> int:
        if self.atLineStart() or self.intail or self.mdstack:
            if self.rawdata[i:i+3] == '<![' and not self.rawdata[i:i+9] == '<![CDATA[':
                # We have encountered the bug in #1534 (Python bug `gh-77057`).
                # Provide an override until we drop support for Python < 3.13.
                result = self.parse_bogus_comment(i)
                if result == -1:
                    self.handle_data(self.rawdata[i:i + 1])
                    return i + 1
                return result
            # The same override exists in `HTMLExtractor` without the check
            # for `mdstack`. Therefore, use parent of `HTMLExtractor` instead.
            return super(HTMLExtractor, self).parse_html_declaration(i)
        # This is not the beginning of a raw block so treat as plain data
        # and avoid consuming any tags which may follow (see #1066).
        self.handle_data('<!')
        return i + 2


class HtmlBlockPreprocessor(Preprocessor):
    """Remove html blocks from the text and store them for later retrieval."""

    def run(self, lines: list[str]) -> list[str]:
        source = '\n'.join(lines)
        parser = HTMLExtractorExtra(self.md)
        parser.feed(source)
        parser.close()
        return ''.join(parser.cleandoc).split('\n')


class MarkdownInHtmlProcessor(BlockProcessor):
    """Process Markdown Inside HTML Blocks which have been stored in the `HtmlStash`."""

    def test(self, parent: etree.Element, block: str) -> bool:
        # Always return True. `run` will return `False` it not a valid match.
        return True

    def parseElementContent(self, element: etree.Element) -> None:
        """
        Recursively parse the text content of an `etree` Element as Markdown.

        Any block level elements generated from the Markdown will be inserted as children of the element in place
        of the text content. All `markdown` attributes are removed. For any elements in which Markdown parsing has
        been disabled, the text content of it and its children are wrapped in an `AtomicString`.
        """

        mdAttr = element.attrib.pop('markdown', 'off')

        if mdAttr == 'block':
            # Parse the block elements content as Markdown
            if element.text:
                block = element.text.rstrip('\n')
                element.text = ''
                self.parser.parseBlocks(element, block.split('\n\n'))

        elif mdAttr == 'span':
            # Span elements need to be recursively processed for block elements and raw HTML
            # as their content is not normally accessed by block processors, so expand stashed
            # HTML under the span. Span content itself will not be parsed here, but will await
            # the inline parser.
            block = element.text if element.text is not None else ''
            element.text = ''
            child = None
            start = 0

            # Search the content for HTML placeholders and process the elements
            for m in util.HTML_PLACEHOLDER_RE.finditer(block):
                index = int(m.group(1))
                el = self.parser.md.htmlStash.rawHtmlBlocks[index]
                end = m.start()

                if isinstance(el, etree.Element):
                    # Replace the placeholder with the element and process it.
                    # Content after the placeholder should be attached to the tail.
                    if child is None:
                        element.text += block[start:end]
                    else:
                        child.tail += block[start:end]
                    element.append(el)
                    self.parseElementContent(el)
                    child = el
                    if child.tail is None:
                        child.tail = ''
                    self.parser.md.htmlStash.rawHtmlBlocks.pop(index)
                    self.parser.md.htmlStash.rawHtmlBlocks.insert(index, '')

                else:
                    # Not an element object, so insert content back into the element
                    if child is None:
                        element.text += block[start:end]
                    else:
                        child.tail += block[start:end]
                start = end

            # Insert anything left after last element
            if child is None:
                element.text += block[start:]
            else:
                child.tail += block[start:]

        else:
            # Disable inline parsing for everything else
            if element.text is None:
                element.text = ''
            element.text = util.AtomicString(element.text)
            for child in list(element):
                self.parseElementContent(child)
                if child.tail:
                    child.tail = util.AtomicString(child.tail)

    def run(self, parent: etree.Element, blocks: list[str]) -> bool:
        m = util.HTML_PLACEHOLDER_RE.match(blocks[0])
        if m:
            index = int(m.group(1))
            element = self.parser.md.htmlStash.rawHtmlBlocks[index]
            if isinstance(element, etree.Element):
                # We have a matched element. Process it.
                block = blocks.pop(0)
                parent.append(element)
                self.parseElementContent(element)
                # Cleanup stash. Replace element with empty string to avoid confusing postprocessor.
                self.parser.md.htmlStash.rawHtmlBlocks.pop(index)
                self.parser.md.htmlStash.rawHtmlBlocks.insert(index, '')
                content = block[m.end(0):]
                # Ensure the rest of the content gets handled
                if content:
                    blocks.insert(0, content)
                # Confirm the match to the `blockparser`.
                return True
        # No match found.
        return False


class MarkdownInHTMLPostprocessor(RawHtmlPostprocessor):
    def stashToString(self, text: str | etree.Element) -> str:
        """ Override default to handle any `etree` elements still in the stash. """
        if isinstance(text, etree.Element):
            return self.md.serializer(text)
        else:
            return str(text)


class MarkdownInHtmlExtension(Extension):
    """Add Markdown parsing in HTML to Markdown class."""

    def extendMarkdown(self, md):
        """ Register extension instances. """

        # Replace raw HTML preprocessor
        md.preprocessors.register(HtmlBlockPreprocessor(md), 'html_block', 20)
        # Add `blockprocessor` which handles the placeholders for `etree` elements
        md.parser.blockprocessors.register(
            MarkdownInHtmlProcessor(md.parser), 'markdown_block', 105
        )
        # Replace raw HTML postprocessor
        md.postprocessors.register(MarkdownInHTMLPostprocessor(md), 'raw_html', 30)


def makeExtension(**kwargs):  # pragma: no cover
    return MarkdownInHtmlExtension(**kwargs)
