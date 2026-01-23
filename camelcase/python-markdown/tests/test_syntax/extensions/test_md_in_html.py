# -*- coding: utf-8 -*-
"""
Python Markdown

A Python implementation of John Gruber's Markdown.

Documentation: https://python-markdown.github.io/
GitHub: https://github.com/Python-Markdown/markdown/
PyPI: https://pypi.org/project/Markdown/

Started by Manfred Stienstra (http://www.dwerg.net/).
Maintained for a few years by Yuri Takhteyev (http://www.freewisdom.org).
Currently maintained by Waylan Limberg (https://github.com/waylan),
Dmitry Shachnev (https://github.com/mitya57) and Isaac Muse (https://github.com/facelessuser).

Copyright 2007-2023 The Python Markdown Project (v. 1.7 and later)
Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
Copyright 2004 Manfred Stienstra (the original version)

License: BSD (see LICENSE.md for details).
"""

from unittest import TestSuite
from markdown.test_tools import TestCase
from ..blocks.test_html_blocks import TestHTMLBlocks
from markdown import Markdown
from xml.etree.ElementTree import Element


class TestMarkdownInHTMLPostProcessor(TestCase):
    """ Ensure any remaining elements in HTML stash are properly serialized. """

    def testStashToString(self):
        # There should be no known cases where this actually happens so we need to
        # forcefully pass an `etree` `Element` to the method to ensure proper behavior.
        element = Element('div')
        element.text = 'Foo bar.'
        md = Markdown(extensions=['md_in_html'])
        result = md.postprocessors['raw_html'].stashToString(element)
        self.assertEqual(result, '<div>Foo bar.</div>')


class TestDefaultwMdInHTML(TestHTMLBlocks):
    """ Ensure the md_in_html extension does not break the default behavior. """

    defaultKwargs = {'extensions': ['md_in_html']}


class TestMdInHTML(TestCase):

    defaultKwargs = {'extensions': ['md_in_html']}

    def testMd1Paragraph(self):
        self.assertMarkdownRenders(
            '<p markdown="1">*foo*</p>',
            '<p><em>foo</em></p>'
        )

    def testMd1PLinebreaks(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <p markdown="1">
                *foo*
                </p>
                """
            ),
            self.dedent(
                """
                <p>
                <em>foo</em>
                </p>
                """
            )
        )

    def testMd1PBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <p markdown="1">

                *foo*

                </p>
                """
            ),
            self.dedent(
                """
                <p>

                <em>foo</em>

                </p>
                """
            )
        )

    def testMd1Div(self):
        self.assertMarkdownRenders(
            '<div markdown="1">*foo*</div>',
            self.dedent(
                """
                <div>
                <p><em>foo</em></p>
                </div>
                """
            )
        )

    def testMd1DivLinebreaks(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                *foo*
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><em>foo</em></p>
                </div>
                """
            )
        )

    def testMd1CodeSpan(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                `<h1>code span</h1>`
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><code>&lt;h1&gt;code span&lt;/h1&gt;</code></p>
                </div>
                """
            )
        )

    def testMd1CodeSpanOneline(self):
        self.assertMarkdownRenders(
            '<div markdown="1">`<h1>code span</h1>`</div>',
            self.dedent(
                """
                <div>
                <p><code>&lt;h1&gt;code span&lt;/h1&gt;</code></p>
                </div>
                """
            )
        )

    def testMd1CodeSpanUnclosed(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                `<p>`
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><code>&lt;p&gt;</code></p>
                </div>
                """
            )
        )

    def testMd1CodeSpanScriptTag(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                `<script>`
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><code>&lt;script&gt;</code></p>
                </div>
                """
            )
        )

    def testMd1DivBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">

                *foo*

                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><em>foo</em></p>
                </div>
                """
            )
        )

    def testMd1DivMulti(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">

                *foo*

                __bar__

                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><em>foo</em></p>
                <p><strong>bar</strong></p>
                </div>
                """
            )
        )

    def testMd1DivNested(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">

                <div markdown="1">
                *foo*
                </div>

                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <div>
                <p><em>foo</em></p>
                </div>
                </div>
                """
            )
        )

    def testMd1DivMultiNest(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">

                <div markdown="1">
                <p markdown="1">*foo*</p>
                </div>

                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <div>
                <p><em>foo</em></p>
                </div>
                </div>
                """
            )
        )

    def textMd1Details(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <details markdown="1">
                <summary>Click to expand</summary>
                *foo*
                </details>
                """
            ),
            self.dedent(
                """
                <details>
                <summary>Click to expand</summary>
                <p><em>foo</em></p>
                </details>
                """
            )
        )

    def testMd1Mix(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                A _Markdown_ paragraph before a raw child.

                <p markdown="1">A *raw* child.</p>

                A _Markdown_ tail to the raw child.
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p>A <em>Markdown</em> paragraph before a raw child.</p>
                <p>A <em>raw</em> child.</p>
                <p>A <em>Markdown</em> tail to the raw child.</p>
                </div>
                """
            )
        )

    def testMd1DeepMix(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">

                A _Markdown_ paragraph before a raw child.

                A second Markdown paragraph
                with two lines.

                <div markdown="1">

                A *raw* child.

                <p markdown="1">*foo*</p>

                Raw child tail.

                </div>

                A _Markdown_ tail to the raw child.

                A second tail item
                with two lines.

                <p markdown="1">More raw.</p>

                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p>A <em>Markdown</em> paragraph before a raw child.</p>
                <p>A second Markdown paragraph
                with two lines.</p>
                <div>
                <p>A <em>raw</em> child.</p>
                <p><em>foo</em></p>
                <p>Raw child tail.</p>
                </div>
                <p>A <em>Markdown</em> tail to the raw child.</p>
                <p>A second tail item
                with two lines.</p>
                <p>More raw.</p>
                </div>
                """
            )
        )

    def testMd1DivRawInline(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">

                <em>foo</em>

                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><em>foo</em></p>
                </div>
                """
            )
        )

    def testNoMd1Paragraph(self):
        self.assertMarkdownRenders(
            '<p>*foo*</p>',
            '<p>*foo*</p>'
        )

    def testNoMd1Nest(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                A _Markdown_ paragraph before a raw child.

                <p>A *raw* child.</p>

                A _Markdown_ tail to the raw child.
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p>A <em>Markdown</em> paragraph before a raw child.</p>
                <p>A *raw* child.</p>
                <p>A <em>Markdown</em> tail to the raw child.</p>
                </div>
                """
            )
        )

    def testMd1NestedEmpty(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                A _Markdown_ paragraph before a raw empty tag.

                <img src="image.png" alt="An image" />

                A _Markdown_ tail to the raw empty tag.
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p>A <em>Markdown</em> paragraph before a raw empty tag.</p>
                <p><img src="image.png" alt="An image" /></p>
                <p>A <em>Markdown</em> tail to the raw empty tag.</p>
                </div>
                """
            )
        )

    def testMd1NestedEmptyBlock(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                A _Markdown_ paragraph before a raw empty tag.

                <hr />

                A _Markdown_ tail to the raw empty tag.
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p>A <em>Markdown</em> paragraph before a raw empty tag.</p>
                <hr />
                <p>A <em>Markdown</em> tail to the raw empty tag.</p>
                </div>
                """
            )
        )

    def testEmptyTags(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                <div></div>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <div></div>
                </div>
                """
            )
        )

    def testOrphanEndTagInRawHtml(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                <div>
                Test

                </pre>

                Test
                </div>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <div>
                Test

                </pre>

                Test
                </div>
                </div>
                """
            )
        )

    def testComplexNestedCase(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                **test**
                <div>
                **test**
                <img src=""/>
                <code>Test</code>
                <span>**test**</span>
                <p>Test 2</p>
                </div>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><strong>test</strong></p>
                <div>
                **test**
                <img src=""/>
                <code>Test</code>
                <span>**test**</span>
                <p>Test 2</p>
                </div>
                </div>
                """
            )
        )

    def testComplexNestedCaseWhitespace(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                Text with space\t
                <div markdown="1">\t
                \t
                 <div>
                **test**
                <img src=""/>
                <code>Test</code>
                <span>**test**</span>
                  <div>With whitespace</div>
                <p>Test 2</p>
                </div>
                **test**
                </div>
                """
            ),
            self.dedent(
                """
                <p>Text with space </p>
                <div>
                <div>
                **test**
                <img src=""/>
                <code>Test</code>
                <span>**test**</span>
                  <div>With whitespace</div>
                <p>Test 2</p>
                </div>
                <p><strong>test</strong></p>
                </div>
                """
            )
        )

    def testMd1IntailMd1(self):
        self.assertMarkdownRenders(
            '<div markdown="1">*foo*</div><div markdown="1">*bar*</div>',
            self.dedent(
                """
                <div>
                <p><em>foo</em></p>
                </div>
                <div>
                <p><em>bar</em></p>
                </div>
                """
            )
        )

    def testMd1NoBlankLineBefore(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                A _Markdown_ paragraph with no blank line after.
                <div markdown="1">
                A _Markdown_ paragraph in an HTML block with no blank line before.
                </div>
                """
            ),
            self.dedent(
                """
                <p>A <em>Markdown</em> paragraph with no blank line after.</p>
                <div>
                <p>A <em>Markdown</em> paragraph in an HTML block with no blank line before.</p>
                </div>
                """
            )
        )

    def testMd1NoLineBreak(self):
        # The div here is parsed as a span-level element. Bad input equals bad output!
        self.assertMarkdownRenders(
            'A _Markdown_ paragraph with <div markdown="1">no _line break_.</div>',
            '<p>A <em>Markdown</em> paragraph with <div markdown="1">no <em>line break</em>.</div></p>'
        )

    def testMd1InTail(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div></div><div markdown="1">
                A _Markdown_ paragraph in an HTML block in tail of previous element.
                </div>
                """
            ),
            self.dedent(
                """
                <div></div>
                <div>
                <p>A <em>Markdown</em> paragraph in an HTML block in tail of previous element.</p>
                </div>
                """
            )
        )

    def testMd1PiOneliner(self):
        self.assertMarkdownRenders(
            '<div markdown="1"><?php print("foo"); ?></div>',
            self.dedent(
                """
                <div>
                <?php print("foo"); ?>
                </div>
                """
            )
        )

    def testMd1PiMultiline(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                <?php print("foo"); ?>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <?php print("foo"); ?>
                </div>
                """
            )
        )

    def testMd1PiBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">

                <?php print("foo"); ?>

                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <?php print("foo"); ?>
                </div>
                """
            )
        )

    def testMdSpanParagraph(self):
        self.assertMarkdownRenders(
            '<p markdown="span">*foo*</p>',
            '<p><em>foo</em></p>'
        )

    def testMdBlockParagraph(self):
        self.assertMarkdownRenders(
            '<p markdown="block">*foo*</p>',
            self.dedent(
                """
                <p>
                <p><em>foo</em></p>
                </p>
                """
            )
        )

    def testMdSpanDiv(self):
        self.assertMarkdownRenders(
            '<div markdown="span">*foo*</div>',
            '<div><em>foo</em></div>'
        )

    def testMdBlockDiv(self):
        self.assertMarkdownRenders(
            '<div markdown="block">*foo*</div>',
            self.dedent(
                """
                <div>
                <p><em>foo</em></p>
                </div>
                """
            )
        )

    def testMdSpanNestedInBlock(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="block">
                <div markdown="span">*foo*</div>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <div><em>foo</em></div>
                </div>
                """
            )
        )

    def testMdBlockNestedInSpan(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="span">
                <div markdown="block">*foo*</div>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <div><em>foo</em></div>
                </div>
                """
            )
        )

    def testMdBlockAfterSpanNestedInBlock(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="block">
                <div markdown="span">*foo*</div>
                <div markdown="block">*bar*</div>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <div><em>foo</em></div>
                <div>
                <p><em>bar</em></p>
                </div>
                </div>
                """
            )
        )

    def testNomdNestedInMd1(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                *foo*
                <div>
                *foo*
                <p>*bar*</p>
                *baz*
                </div>
                *bar*
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><em>foo</em></p>
                <div>
                *foo*
                <p>*bar*</p>
                *baz*
                </div>
                <p><em>bar</em></p>
                </div>
                """
            )
        )

    def testMd1NestedInNomd(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div>
                <div markdown="1">*foo*</div>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <div markdown="1">*foo*</div>
                </div>
                """
            )
        )

    def testMd1SingleQuotes(self):
        self.assertMarkdownRenders(
            "<p markdown='1'>*foo*</p>",
            '<p><em>foo</em></p>'
        )

    def testMd1NoQuotes(self):
        self.assertMarkdownRenders(
            '<p markdown=1>*foo*</p>',
            '<p><em>foo</em></p>'
        )

    def testMdNoValue(self):
        self.assertMarkdownRenders(
            '<p markdown>*foo*</p>',
            '<p><em>foo</em></p>'
        )

    def testMd1PreserveAttrs(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1" id="parent">

                <div markdown="1" class="foo">
                <p markdown="1" class="bar baz">*foo*</p>
                </div>

                </div>
                """
            ),
            self.dedent(
                """
                <div id="parent">
                <div class="foo">
                <p class="bar baz"><em>foo</em></p>
                </div>
                </div>
                """
            )
        )

    def testMd1UnclosedDiv(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">

                _foo_

                <div class="unclosed">

                _bar_

                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><em>foo</em></p>
                <div class="unclosed">

                _bar_

                </div>
                </div>
                """
            )
        )

    def testMd1OrphanEndtag(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">

                _foo_

                </p>

                _bar_

                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><em>foo</em></p>
                </p>
                <p><em>bar</em></p>
                </div>
                """
            )
        )

    def testMd1UnclosedP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <p markdown="1">_foo_
                <p markdown="1">_bar_
                """
            ),
            self.dedent(
                """
                <p><em>foo</em>
                </p>
                <p><em>bar</em>

                </p>
                """
            )
        )

    def testMd1NestedUnclosedP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                <p markdown="1">_foo_
                <p markdown="1">_bar_
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p><em>foo</em>
                </p>
                <p><em>bar</em>
                </p>
                </div>
                """
            )
        )

    def testMd1NestedComment(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                A *Markdown* paragraph.
                <!-- foobar -->
                A *Markdown* paragraph.
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p>A <em>Markdown</em> paragraph.</p>
                <!-- foobar -->
                <p>A <em>Markdown</em> paragraph.</p>
                </div>
                """
            )
        )

    def testMd1NestedLinkRef(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                [link]: http://example.com
                <div markdown="1">
                [link][link]
                </div>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <div>
                <p><a href="http://example.com">link</a></p>
                </div>
                </div>
                """
            )
        )

    def testMd1HrOnlyStart(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                *emphasis1*
                <hr markdown="1">
                *emphasis2*
                """
            ),
            self.dedent(
                """
                <p><em>emphasis1</em></p>
                <hr>
                <p><em>emphasis2</em></p>
                """
            )
        )

    def testMd1HrSelfClose(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                *emphasis1*
                <hr markdown="1" />
                *emphasis2*
                """
            ),
            self.dedent(
                """
                <p><em>emphasis1</em></p>
                <hr>
                <p><em>emphasis2</em></p>
                """
            )
        )

    def testMd1HrStartAndEnd(self):
        # Browsers ignore ending hr tags, so we don't try to do anything to handle them special.
        self.assertMarkdownRenders(
            self.dedent(
                """
                *emphasis1*
                <hr markdown="1"></hr>
                *emphasis2*
                """
            ),
            self.dedent(
                """
                <p><em>emphasis1</em></p>
                <hr>
                <p></hr>
                <em>emphasis2</em></p>
                """
            )
        )

    def testMd1HrOnlyEnd(self):
        # Browsers ignore ending hr tags, so we don't try to do anything to handle them special.
        self.assertMarkdownRenders(
            self.dedent(
                """
                *emphasis1*
                </hr>
                *emphasis2*
                """
            ),
            self.dedent(
                """
                <p><em>emphasis1</em>
                </hr>
                <em>emphasis2</em></p>
                """
            )
        )

    def testMd1HrWithContent(self):
        # Browsers ignore ending hr tags, so we don't try to do anything to handle them special.
        # Content is not allowed and will be treated as normal content between two hr tags
        self.assertMarkdownRenders(
            self.dedent(
                """
                *emphasis1*
                <hr markdown="1">
                **content**
                </hr>
                *emphasis2*
                """
            ),
            self.dedent(
                """
                <p><em>emphasis1</em></p>
                <hr>
                <p><strong>content</strong>
                </hr>
                <em>emphasis2</em></p>
                """
            )
        )

    def testNoMd1HrWithContent(self):
        # Browsers ignore ending hr tags, so we don't try to do anything to handle them special.
        # Content is not allowed and will be treated as normal content between two hr tags
        self.assertMarkdownRenders(
            self.dedent(
                """
                *emphasis1*
                <hr>
                **content**
                </hr>
                *emphasis2*
                """
            ),
            self.dedent(
                """
                <p><em>emphasis1</em></p>
                <hr>
                <p><strong>content</strong>
                </hr>
                <em>emphasis2</em></p>
                """
            )
        )

    def testMd1NestedAbbrRef(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                *[abbr]: Abbreviation
                <div markdown="1">
                abbr
                </div>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <div>
                <p><abbr title="Abbreviation">abbr</abbr></p>
                </div>
                </div>
                """
            ),
            extensions=['md_in_html', 'abbr']
        )

    def testMd1NestedFootnoteRef(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown="1">
                [^1]: The footnote.
                <div markdown="1">
                Paragraph with a footnote.[^1]
                </div>
                </div>
                """
            ),
            '<div>\n'
            '<div>\n'
            '<p>Paragraph with a footnote.<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '</div>\n'
            '</div>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>The footnote.&#160;'
            '<a class="footnote-backref" href="#fnref:1" title="Jump back to footnote 1 in the text">&#8617;</a>'
            '</p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>',
            extensions=['md_in_html', 'footnotes']
        )

    def testMd1CodeVoidTag(self):

        # https://github.com/Python-Markdown/markdown/issues/1075
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div class="outer" markdown="1">

                Code: `<label><input/></label>`

                </div>

                <div class="outer" markdown="1">

                HTML: <label><input/></label>

                </div>
                """
            ),
            '<div class="outer">\n'
            '<p>Code: <code>&lt;label&gt;&lt;input/&gt;&lt;/label&gt;</code></p>\n'
            '</div>\n'
            '<div class="outer">\n'
            '<p>HTML: <label><input/></label></p>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1CodeVoidTagMultiline(self):

        # https://github.com/Python-Markdown/markdown/issues/1075
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div class="outer" markdown="1">

                Code: `
                <label>
                <input/>
                </label>
                `

                </div>

                <div class="outer" markdown="1">

                HTML:
                <label>
                <input/>
                </label>

                </div>
                """
            ),
            '<div class="outer">\n'
            '<p>Code: <code>&lt;label&gt;\n'
            '&lt;input/&gt;\n'
            '&lt;/label&gt;</code></p>\n'
            '</div>\n'
            '<div class="outer">\n'
            '<p>HTML:\n'
            '<label>\n'
            '<input/>\n'
            '</label></p>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1OnelinerBlock(self):
        # https://github.com/Python-Markdown/markdown/issues/1074
        self.assertMarkdownRenders(
            self.dedent(
                '<div class="outer" markdown="block"><div class="inner" markdown="block">*foo*</div></div>'
            ),
            '<div class="outer">\n'
            '<div class="inner">\n'
            '<p><em>foo</em></p>\n'
            '</div>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1OnelinerBlockMixed(self):
        # https://github.com/Python-Markdown/markdown/issues/1074
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div class="a" markdown="block"><div class="b" markdown="block">

                <div class="c" markdown="block"><div class="d" markdown="block">
                *foo*
                </div></div>

                </div></div>
                """
            ),
            '<div class="a">\n'
            '<div class="b">\n'
            '<div class="c">\n'
            '<div class="d">\n'
            '<p><em>foo</em></p>\n'
            '</div>\n'
            '</div>\n'
            '</div>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1OnelinerBlockTail(self):
        # https://github.com/Python-Markdown/markdown/issues/1074
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div class="a" markdown="block"><div class="b" markdown="block">
                **foo**
                </div><div class="c" markdown="block"><div class="d" markdown="block">
                *bar*
                </div></div></div>
                """
            ),
            '<div class="a">\n'
            '<div class="b">\n'
            '<p><strong>foo</strong></p>\n'
            '</div>\n'
            '<div class="c">\n'
            '<div class="d">\n'
            '<p><em>bar</em></p>\n'
            '</div>\n'
            '</div>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1OnelinerBlockComplexStartTail(self):
        # https://github.com/Python-Markdown/markdown/issues/1074
        self.assertMarkdownRenders(
            '<div class="a" markdown><div class="b" markdown>**foo**</div>'
            '<div class="c" markdown>*bar*</div><div class="d">*not md*</div></div>',
            '<div class="a">\n'
            '<div class="b">\n'
            '<p><strong>foo</strong></p>\n'
            '</div>\n'
            '<div class="c">\n'
            '<p><em>bar</em></p>\n'
            '</div>\n'
            '<div class="d">*not md*</div>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1OnelinerBlockComplexFail(self):
        # https://github.com/Python-Markdown/markdown/issues/1074
        # Nested will fail because an inline tag is only considered at the beginning if it is not preceded by text.
        self.assertMarkdownRenders(
            '<div class="a" markdown>**strong**<div class="b" markdown>**strong**</div></div>',
            '<div class="a">\n'
            '<p><strong>strong</strong><div class="b" markdown><strong>strong</strong></p>\n'
            '</div>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1OnelinerBlockStart(self):
        # https://github.com/Python-Markdown/markdown/issues/1074
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div class="outer" markdown="block"><div class="inner" markdown="block">
                *foo*
                </div></div>
                """
            ),
            '<div class="outer">\n'
            '<div class="inner">\n'
            '<p><em>foo</em></p>\n'
            '</div>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1OnelinerBlockSpan(self):
        # https://github.com/Python-Markdown/markdown/issues/1074
        self.assertMarkdownRenders(
            self.dedent(
                '<div class="outer" markdown="block"><div class="inner" markdown="span">*foo*</div></div>'
            ),
            '<div class="outer">\n'
            '<div class="inner"><em>foo</em></div>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1OnelinerBlockSpanStart(self):
        # https://github.com/Python-Markdown/markdown/issues/1074
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div class="outer" markdown="block"><div class="inner" markdown="span">
                *foo*
                </div></div>
                """
            ),
            '<div class="outer">\n'
            '<div class="inner">\n'
            '<em>foo</em>\n'
            '</div>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1OnelinerSpanBlockStart(self):
        # https://github.com/Python-Markdown/markdown/issues/1074
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div class="outer" markdown="span"><div class="inner" markdown="block">
                *foo*
                </div>
                *foo*
                </div>
                """
            ),
            '<div class="outer">\n'
            '<div class="inner">\n'
            '<em>foo</em>\n'
            '</div>\n\n'
            '<em>foo</em></div>',
            extensions=['md_in_html']
        )

    def testMd1CodeComment(self):

        self.assertMarkdownRenders(
            self.dedent(
                """
                <div class="outer" markdown="1">

                Code: `<label><!-- **comment** --></label>`

                </div>

                <div class="outer" markdown="1">

                HTML: <label><!-- **comment** --></label>

                </div>
                """
            ),
            '<div class="outer">\n'
            '<p>Code: <code>&lt;label&gt;&lt;!-- **comment** --&gt;&lt;/label&gt;</code></p>\n'
            '</div>\n'
            '<div class="outer">\n'
            '<p>HTML: <label><!-- **comment** --></label></p>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1CodePi(self):

        self.assertMarkdownRenders(
            self.dedent(
                """
                <div class="outer" markdown="1">

                Code: `<label><?php # echo '**simple**';?></label>`

                </div>

                <div class="outer" markdown="1">

                HTML: <label><?php # echo '**simple**';?></label>

                </div>
                """
            ),
            '<div class="outer">\n'
            '<p>Code: <code>&lt;label&gt;&lt;?php # echo \'**simple**\';?&gt;&lt;/label&gt;</code></p>\n'
            '</div>\n'
            '<div class="outer">\n'
            '<p>HTML: <label><?php # echo \'**simple**\';?></label></p>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testMd1CodeCdata(self):

        self.assertMarkdownRenders(
            self.dedent(
                """
                <div class="outer" markdown="1">

                Code: `<label><![CDATA[some stuff]]></label>`

                </div>

                <div class="outer" markdown="1">

                HTML: <label><![CDATA[some stuff]]></label>

                </div>
                """
            ),
            '<div class="outer">\n'
            '<p>Code: <code>&lt;label&gt;&lt;![CDATA[some stuff]]&gt;&lt;/label&gt;</code></p>\n'
            '</div>\n'
            '<div class="outer">\n'
            '<p>HTML: <label><![CDATA[some stuff]]></label></p>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testTrailingContentAfterTagInMdBlock(self):

        # It should be noted that this is not the way `md_in_html` is intended to be used.
        # What we are specifically testing is an edge case where content was previously lost.
        # Lost content should not happen.
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown>
                <div class="circle"></div>AAAAA<div class="circle"></div>
                </div>
                """
            ),
            '<div>\n'
            '<div class="circle"></div>\n'
            '<p>AAAAA<div class="circle"></p>\n'
            '</div>\n'
            '</div>',
            extensions=['md_in_html']
        )

    def testNonameTag(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div markdown>
                </>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p>&lt;/&gt;</p>
                </div>
                """
            )
        )


def loadTests(loader, tests, pattern):
    """ Ensure `TestHTMLBlocks` doesn't get run twice by excluding it here. """
    suite = TestSuite()
    for testClass in [TestDefaultwMdInHTML, TestMdInHTML, TestMarkdownInHTMLPostProcessor]:
        tests = loader.loadTestsFromTestCase(testClass)
        suite.addTests(tests)
    return suite
