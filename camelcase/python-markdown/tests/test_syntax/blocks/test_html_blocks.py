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

from markdown.test_tools import TestCase
import markdown


class TestHTMLBlocks(TestCase):

    def testRawParagraph(self):
        self.assertMarkdownRenders(
            '<p>A raw paragraph.</p>',
            '<p>A raw paragraph.</p>'
        )

    def testRawSkipInlineMarkdown(self):
        self.assertMarkdownRenders(
            '<p>A *raw* paragraph.</p>',
            '<p>A *raw* paragraph.</p>'
        )

    def testRawIndentOneSpace(self):
        self.assertMarkdownRenders(
            ' <p>A *raw* paragraph.</p>',
            '<p>A *raw* paragraph.</p>'
        )

    def testRawIndentTwoSpaces(self):
        self.assertMarkdownRenders(
            '  <p>A *raw* paragraph.</p>',
            '<p>A *raw* paragraph.</p>'
        )

    def testRawIndentThreeSpaces(self):
        self.assertMarkdownRenders(
            '   <p>A *raw* paragraph.</p>',
            '<p>A *raw* paragraph.</p>'
        )

    def testRawIndentFourSpaces(self):
        self.assertMarkdownRenders(
            '    <p>code block</p>',
            self.dedent(
                """
                <pre><code>&lt;p&gt;code block&lt;/p&gt;
                </code></pre>
                """
            )
        )

    def testRawSpan(self):
        self.assertMarkdownRenders(
            '<span>*inline*</span>',
            '<p><span><em>inline</em></span></p>'
        )

    def testCodeSpan(self):
        self.assertMarkdownRenders(
            '`<p>code span</p>`',
            '<p><code>&lt;p&gt;code span&lt;/p&gt;</code></p>'
        )

    def testCodeSpanOpenGt(self):
        self.assertMarkdownRenders(
            '*bar* `<` *foo*',
            '<p><em>bar</em> <code>&lt;</code> <em>foo</em></p>'
        )

    def testRawEmpty(self):
        self.assertMarkdownRenders(
            '<p></p>',
            '<p></p>'
        )

    def testRawEmptySpace(self):
        self.assertMarkdownRenders(
            '<p> </p>',
            '<p> </p>'
        )

    def testRawEmptyNewline(self):
        self.assertMarkdownRenders(
            '<p>\n</p>',
            '<p>\n</p>'
        )

    def testRawEmptyBlankLine(self):
        self.assertMarkdownRenders(
            '<p>\n\n</p>',
            '<p>\n\n</p>'
        )

    def testRawUppercase(self):
        self.assertMarkdownRenders(
            '<DIV>*foo*</DIV>',
            '<DIV>*foo*</DIV>'
        )

    def testRawUppercaseMultiline(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <DIV>
                *foo*
                </DIV>
                """
            ),
            self.dedent(
                """
                <DIV>
                *foo*
                </DIV>
                """
            )
        )

    def testMultipleRawSingleLine(self):
        self.assertMarkdownRenders(
            '<p>*foo*</p><div>*bar*</div>',
            self.dedent(
                """
                <p>*foo*</p>
                <div>*bar*</div>
                """
            )
        )

    def testMultipleRawSingleLineWithPi(self):
        self.assertMarkdownRenders(
            "<p>*foo*</p><?php echo '>'; ?>",
            self.dedent(
                """
                <p>*foo*</p>
                <?php echo '>'; ?>
                """
            )
        )

    def testMultilineRaw(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <p>
                    A raw paragraph
                    with multiple lines.
                </p>
                """
            ),
            self.dedent(
                """
                <p>
                    A raw paragraph
                    with multiple lines.
                </p>
                """
            )
        )

    def testBlankLinesInRaw(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <p>

                    A raw paragraph...

                    with many blank lines.

                </p>
                """
            ),
            self.dedent(
                """
                <p>

                    A raw paragraph...

                    with many blank lines.

                </p>
                """
            )
        )

    def testRawSurroundedByMarkdown(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                Some *Markdown* text.

                <p>*Raw* HTML.</p>

                More *Markdown* text.
                """
            ),
            self.dedent(
                """
                <p>Some <em>Markdown</em> text.</p>
                <p>*Raw* HTML.</p>

                <p>More <em>Markdown</em> text.</p>
                """
            )
        )

    def testRawSurroundedByTextWithoutBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                Some *Markdown* text.
                <p>*Raw* HTML.</p>
                More *Markdown* text.
                """
            ),
            self.dedent(
                """
                <p>Some <em>Markdown</em> text.</p>
                <p>*Raw* HTML.</p>
                <p>More <em>Markdown</em> text.</p>
                """
            )
        )

    def testMultilineMarkdownWithCodeSpan(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                A paragraph with a block-level
                `<p>code span</p>`, which is
                at the start of a line.
                """
            ),
            self.dedent(
                """
                <p>A paragraph with a block-level
                <code>&lt;p&gt;code span&lt;/p&gt;</code>, which is
                at the start of a line.</p>
                """
            )
        )

    def testRawBlockPrecededByMarkdownCodeSpanWithUnclosedBlockTag(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                A paragraph with a block-level code span: `<div>`.

                <p>*not markdown*</p>

                This is *markdown*
                """
            ),
            self.dedent(
                """
                <p>A paragraph with a block-level code span: <code>&lt;div&gt;</code>.</p>
                <p>*not markdown*</p>

                <p>This is <em>markdown</em></p>
                """
            )
        )

    def testRawOneLineFollowedByText(self):
        self.assertMarkdownRenders(
            '<p>*foo*</p>*bar*',
            self.dedent(
                """
                <p>*foo*</p>
                <p><em>bar</em></p>
                """
            )
        )

    def testRawOneLineFollowedBySpan(self):
        self.assertMarkdownRenders(
            "<p>*foo*</p><span>*bar*</span>",
            self.dedent(
                """
                <p>*foo*</p>
                <p><span><em>bar</em></span></p>
                """
            )
        )

    def testRawWithMarkdownBlocks(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div>
                    Not a Markdown paragraph.

                    * Not a list item.
                    * Another non-list item.

                    Another non-Markdown paragraph.
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                    Not a Markdown paragraph.

                    * Not a list item.
                    * Another non-list item.

                    Another non-Markdown paragraph.
                </div>
                """
            )
        )

    def testAdjacentRawBlocks(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <p>A raw paragraph.</p>
                <p>A second raw paragraph.</p>
                """
            ),
            self.dedent(
                """
                <p>A raw paragraph.</p>
                <p>A second raw paragraph.</p>
                """
            )
        )

    def testAdjacentRawBlocksWithBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <p>A raw paragraph.</p>

                <p>A second raw paragraph.</p>
                """
            ),
            self.dedent(
                """
                <p>A raw paragraph.</p>

                <p>A second raw paragraph.</p>
                """
            )
        )

    def testNestedRawOneLine(self):
        self.assertMarkdownRenders(
            '<div><p>*foo*</p></div>',
            '<div><p>*foo*</p></div>'
        )

    def testNestedRawBlock(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div>
                <p>A raw paragraph.</p>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p>A raw paragraph.</p>
                </div>
                """
            )
        )

    def testNestedIndentedRawBlock(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div>
                    <p>A raw paragraph.</p>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                    <p>A raw paragraph.</p>
                </div>
                """
            )
        )

    def testNestedRawBlocks(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div>
                <p>A raw paragraph.</p>
                <p>A second raw paragraph.</p>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <p>A raw paragraph.</p>
                <p>A second raw paragraph.</p>
                </div>
                """
            )
        )

    def testNestedRawBlocksWithBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div>

                <p>A raw paragraph.</p>

                <p>A second raw paragraph.</p>

                </div>
                """
            ),
            self.dedent(
                """
                <div>

                <p>A raw paragraph.</p>

                <p>A second raw paragraph.</p>

                </div>
                """
            )
        )

    def testNestedInlineOneLine(self):
        self.assertMarkdownRenders(
            '<p><em>foo</em><br></p>',
            '<p><em>foo</em><br></p>'
        )

    def testRawNestedInline(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div>
                    <p>
                        <span>*text*</span>
                    </p>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                    <p>
                        <span>*text*</span>
                    </p>
                </div>
                """
            )
        )

    def testRawNestedInlineWithBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div>

                    <p>

                        <span>*text*</span>

                    </p>

                </div>
                """
            ),
            self.dedent(
                """
                <div>

                    <p>

                        <span>*text*</span>

                    </p>

                </div>
                """
            )
        )

    def testRawHtml5(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <section>
                    <header>
                        <hgroup>
                            <h1>Hello :-)</h1>
                        </hgroup>
                    </header>
                    <figure>
                        <img src="image.png" alt="" />
                        <figcaption>Caption</figcaption>
                    </figure>
                    <footer>
                        <p>Some footer</p>
                    </footer>
                </section>
                """
            ),
            self.dedent(
                """
                <section>
                    <header>
                        <hgroup>
                            <h1>Hello :-)</h1>
                        </hgroup>
                    </header>
                    <figure>
                        <img src="image.png" alt="" />
                        <figcaption>Caption</figcaption>
                    </figure>
                    <footer>
                        <p>Some footer</p>
                    </footer>
                </section>
                """
            )
        )

    def testRawPreTag(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                Preserve whitespace in raw html

                <pre>
                class Foo():
                    bar = 'bar'

                    @property
                    def baz(self):
                        return self.bar
                </pre>
                """
            ),
            self.dedent(
                """
                <p>Preserve whitespace in raw html</p>
                <pre>
                class Foo():
                    bar = 'bar'

                    @property
                    def baz(self):
                        return self.bar
                </pre>
                """
            )
        )

    def testRawPreTagNestedEscapedHtml(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <pre>
                &lt;p&gt;foo&lt;/p&gt;
                </pre>
                """
            ),
            self.dedent(
                """
                <pre>
                &lt;p&gt;foo&lt;/p&gt;
                </pre>
                """
            )
        )

    def testRawPNoEndTag(self):
        self.assertMarkdownRenders(
            '<p>*text*',
            '<p>*text*'
        )

    def testRawMultiplePNoEndTag(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <p>*text*'

                <p>more *text*
                """
            ),
            self.dedent(
                """
                <p>*text*'

                <p>more *text*
                """
            )
        )

    def testRawPNoEndTagFollowedByBlankLine(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <p>*raw text*'

                Still part of *raw* text.
                """
            ),
            self.dedent(
                """
                <p>*raw text*'

                Still part of *raw* text.
                """
            )
        )

    def testRawNestedPNoEndTag(self):
        self.assertMarkdownRenders(
            '<div><p>*text*</div>',
            '<div><p>*text*</div>'
        )

    def testRawOpenBracketOnly(self):
        self.assertMarkdownRenders(
            '<',
            '<p>&lt;</p>'
        )

    def testRawOpenBracketFollowedBySpace(self):
        self.assertMarkdownRenders(
            '< foo',
            '<p>&lt; foo</p>'
        )

    def testRawMissingCloseBracket(self):
        self.assertMarkdownRenders(
            '<foo',
            '<p>&lt;foo</p>'
        )

    def testRawUnclosedTagInCodeSpan(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                `<div`.

                <div>
                hello
                </div>
                """
            ),
            self.dedent(
                """
                <p><code>&lt;div</code>.</p>
                <div>
                hello
                </div>
                """
            )
        )

    def testRawUnclosedTagInCodeSpanSpace(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ` <div `.

                <div>
                hello
                </div>
                """
            ),
            self.dedent(
                """
                <p><code>&lt;div</code>.</p>
                <div>
                hello
                </div>
                """
            )
        )

    def testRawAttributes(self):
        self.assertMarkdownRenders(
            '<p id="foo", class="bar baz", style="margin: 15px; line-height: 1.5; text-align: center;">text</p>',
            '<p id="foo", class="bar baz", style="margin: 15px; line-height: 1.5; text-align: center;">text</p>'
        )

    def testRawAttributesNested(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div id="foo, class="bar", style="background: #ffe7e8; border: 2px solid #e66465;">
                    <p id="baz", style="margin: 15px; line-height: 1.5; text-align: center;">
                        <img scr="../foo.jpg" title="with 'quoted' text." valueless_attr weirdness="<i>foo</i>" />
                    </p>
                </div>
                """
            ),
            self.dedent(
                """
                <div id="foo, class="bar", style="background: #ffe7e8; border: 2px solid #e66465;">
                    <p id="baz", style="margin: 15px; line-height: 1.5; text-align: center;">
                        <img scr="../foo.jpg" title="with 'quoted' text." valueless_attr weirdness="<i>foo</i>" />
                    </p>
                </div>
                """
            )
        )

    def testRawCommentOneLine(self):
        self.assertMarkdownRenders(
            '<!-- *foo* -->',
            '<!-- *foo* -->'
        )

    def testRawCommentOneLineWithTag(self):
        self.assertMarkdownRenders(
            '<!-- <tag> -->',
            '<!-- <tag> -->'
        )

    def testCommentInCodeSpan(self):
        self.assertMarkdownRenders(
            '`<!-- *foo* -->`',
            '<p><code>&lt;!-- *foo* --&gt;</code></p>'
        )

    def testRawCommentOneLineFollowedByText(self):
        self.assertMarkdownRenders(
            '<!-- *foo* -->*bar*',
            self.dedent(
                """
                <!-- *foo* -->
                <p><em>bar</em></p>
                """
            )
        )

    def testRawCommentOneLineFollowedByHtml(self):
        self.assertMarkdownRenders(
            '<!-- *foo* --><p>*bar*</p>',
            self.dedent(
                """
                <!-- *foo* -->
                <p>*bar*</p>
                """
            )
        )

    # Note: Trailing (insignificant) whitespace is not preserved, which does not match the
    # reference implementation. However, it is not a change in behavior for Python-Markdown.
    def testRawCommentTrailingWhitespace(self):
        self.assertMarkdownRenders(
            '<!-- *foo* --> ',
            '<!-- *foo* -->'
        )

    def testBogusComment(self):
        self.assertMarkdownRenders(
            '<!invalid>',
            '<p>&lt;!invalid&gt;</p>'
        )

    def testBogusCommentEndtag(self):
        self.assertMarkdownRenders(
            '</#invalid>',
            '<p>&lt;/#invalid&gt;</p>'
        )

    def testRawMultilineComment(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!--
                *foo*
                -->
                """
            ),
            self.dedent(
                """
                <!--
                *foo*
                -->
                """
            )
        )

    def testRawMultilineCommentWithTag(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!--
                <tag>
                -->
                """
            ),
            self.dedent(
                """
                <!--
                <tag>
                -->
                """
            )
        )

    def testRawMultilineCommentFirstLine(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!-- *foo*
                -->
                """
            ),
            self.dedent(
                """
                <!-- *foo*
                -->
                """
            )
        )

    def testRawMultilineCommentLastLine(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!--
                *foo* -->
                """
            ),
            self.dedent(
                """
                <!--
                *foo* -->
                """
            )
        )

    def testRawCommentWithBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!--

                *foo*

                -->
                """
            ),
            self.dedent(
                """
                <!--

                *foo*

                -->
                """
            )
        )

    def testRawCommentWithBlankLinesWithTag(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!--

                <tag>

                -->
                """
            ),
            self.dedent(
                """
                <!--

                <tag>

                -->
                """
            )
        )

    def testRawCommentWithBlankLinesFirstLine(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!-- *foo*

                -->
                """
            ),
            self.dedent(
                """
                <!-- *foo*

                -->
                """
            )
        )

    def testRawCommentWithBlankLinesLastLine(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!--

                *foo* -->
                """
            ),
            self.dedent(
                """
                <!--

                *foo* -->
                """
            )
        )

    def testRawCommentIndented(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!--

                    *foo*

                -->
                """
            ),
            self.dedent(
                """
                <!--

                    *foo*

                -->
                """
            )
        )

    def testRawCommentIndentedWithTag(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!--

                    <tag>

                -->
                """
            ),
            self.dedent(
                """
                <!--

                    <tag>

                -->
                """
            )
        )

    def testRawCommentNested(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div>
                <!-- *foo* -->
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                <!-- *foo* -->
                </div>
                """
            )
        )

    def testCommentInCodeBlock(self):
        self.assertMarkdownRenders(
            '    <!-- *foo* -->',
            self.dedent(
                """
                <pre><code>&lt;!-- *foo* --&gt;
                </code></pre>
                """
            )
        )

    # Note: This is a change in behavior. Previously, Python-Markdown interpreted this in the same manner
    # as browsers and all text after the opening comment tag was considered to be in a comment. However,
    # that did not match the reference implementation. The new behavior does.
    def testUnclosedComment(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!-- unclosed comment

                *not* a comment
                """
            ),
            self.dedent(
                """
                <p>&lt;!-- unclosed comment</p>
                <p><em>not</em> a comment</p>
                """
            )
        )

    def testInvalidCommentEnd(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!-- This comment is malformed and never closes -- >
                Some content after the bad comment.
                """
            ),
            self.dedent(
                """
                <p>&lt;!-- This comment is malformed and never closes -- &gt;
                Some content after the bad comment.</p>
                """
            )
        )

    def testRawProcessingInstructionOneLine(self):
        self.assertMarkdownRenders(
            "<?php echo '>'; ?>",
            "<?php echo '>'; ?>"
        )

    # This is a change in behavior and does not match the reference implementation.
    # We have no way to determine if text is on the same line, so we get this. TODO: reevaluate!
    def testRawProcessingInstructionOneLineFollowedByText(self):
        self.assertMarkdownRenders(
            "<?php echo '>'; ?>*bar*",
            self.dedent(
                """
                <?php echo '>'; ?>
                <p><em>bar</em></p>
                """
            )
        )

    def testRawMultilineProcessingInstruction(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <?php
                echo '>';
                ?>
                """
            ),
            self.dedent(
                """
                <?php
                echo '>';
                ?>
                """
            )
        )

    def testRawProcessingInstructionWithBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <?php

                echo '>';

                ?>
                """
            ),
            self.dedent(
                """
                <?php

                echo '>';

                ?>
                """
            )
        )

    def testRawProcessingInstructionIndented(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <?php

                    echo '>';

                ?>
                """
            ),
            self.dedent(
                """
                <?php

                    echo '>';

                ?>
                """
            )
        )

    def testRawProcessingInstructionCodeSpan(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                `<?php`

                <div>
                foo
                </div>
                """
            ),
            self.dedent(
                """
                <p><code>&lt;?php</code></p>
                <div>
                foo
                </div>
                """
            )
        )

    def testRawDeclarationOneLine(self):
        self.assertMarkdownRenders(
            '<!DOCTYPE html>',
            '<!DOCTYPE html>'
        )

    # This is a change in behavior and does not match the reference implementation.
    # We have no way to determine if text is on the same line, so we get this. TODO: reevaluate!
    def testRawDeclarationOneLineFollowedByText(self):
        self.assertMarkdownRenders(
            '<!DOCTYPE html>*bar*',
            self.dedent(
                """
                <!DOCTYPE html>
                <p><em>bar</em></p>
                """
            )
        )

    def testRawMultilineDeclaration(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <!DOCTYPE html PUBLIC
                  "-//W3C//DTD XHTML 1.1//EN"
                  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
                """
            ),
            self.dedent(
                """
                <!DOCTYPE html PUBLIC
                  "-//W3C//DTD XHTML 1.1//EN"
                  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
                """
            )
        )

    def testRawDeclarationCodeSpan(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                `<!`

                <div>
                foo
                </div>
                """
            ),
            self.dedent(
                """
                <p><code>&lt;!</code></p>
                <div>
                foo
                </div>
                """
            )
        )

    def testRawCdataOneLine(self):
        self.assertMarkdownRenders(
            '<![CDATA[ document.write(">"); ]]>',
            '<![CDATA[ document.write(">"); ]]>'
        )

    # Note: this is a change. Neither previous output nor this match reference implementation.
    def testRawCdataOneLineFollowedByText(self):
        self.assertMarkdownRenders(
            '<![CDATA[ document.write(">"); ]]>*bar*',
            self.dedent(
                """
                <![CDATA[ document.write(">"); ]]>
                <p><em>bar</em></p>
                """
            )
        )

    def testRawMultilineCdata(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <![CDATA[
                document.write(">");
                ]]>
                """
            ),
            self.dedent(
                """
                <![CDATA[
                document.write(">");
                ]]>
                """
            )
        )

    def testRawCdataWithBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <![CDATA[

                document.write(">");

                ]]>
                """
            ),
            self.dedent(
                """
                <![CDATA[

                document.write(">");

                ]]>
                """
            )
        )

    def testRawCdataIndented(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <![CDATA[

                    document.write(">");

                ]]>
                """
            ),
            self.dedent(
                """
                <![CDATA[

                    document.write(">");

                ]]>
                """
            )
        )

    def testNotActuallyCdata(self):
        # Ensure bug reported in #1534 is avoided.
        self.assertMarkdownRenders(
            '<![',
            '<p>&lt;![</p>'
        )

    def testRawCdataCodeSpan(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                `<![`

                <div>
                foo
                </div>
                """
            ),
            self.dedent(
                """
                <p><code>&lt;![</code></p>
                <div>
                foo
                </div>
                """
            )
        )

    def testCharref(self):
        self.assertMarkdownRenders(
            '&sect;',
            '<p>&sect;</p>'
        )

    def testNestedCharref(self):
        self.assertMarkdownRenders(
            '<p>&sect;</p>',
            '<p>&sect;</p>'
        )

    def testEntityref(self):
        self.assertMarkdownRenders(
            '&#167;',
            '<p>&#167;</p>'
        )

    def testNestedEntityref(self):
        self.assertMarkdownRenders(
            '<p>&#167;</p>',
            '<p>&#167;</p>'
        )

    def testAmperstand(self):
        self.assertMarkdownRenders(
            'AT&T & AT&amp;T',
            '<p>AT&amp;T &amp; AT&amp;T</p>'
        )

    def testStartendtag(self):
        self.assertMarkdownRenders(
            '<hr>',
            '<hr>'
        )

    def testStartendtagWithAttrs(self):
        self.assertMarkdownRenders(
            '<hr id="foo" class="bar">',
            '<hr id="foo" class="bar">'
        )

    def testStartendtagWithSpace(self):
        self.assertMarkdownRenders(
            '<hr >',
            '<hr >'
        )

    def testClosedStartendtag(self):
        self.assertMarkdownRenders(
            '<hr />',
            '<hr />'
        )

    def testClosedStartendtagWithoutSpace(self):
        self.assertMarkdownRenders(
            '<hr/>',
            '<hr/>'
        )

    def testClosedStartendtagWithAttrs(self):
        self.assertMarkdownRenders(
            '<hr id="foo" class="bar" />',
            '<hr id="foo" class="bar" />'
        )

    def testNestedStartendtag(self):
        self.assertMarkdownRenders(
            '<div><hr></div>',
            '<div><hr></div>'
        )

    def testNestedClosedStartendtag(self):
        self.assertMarkdownRenders(
            '<div><hr /></div>',
            '<div><hr /></div>'
        )

    def testMultilineAttributes(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div id="foo"
                     class="bar">
                    text
                </div>

                <hr class="foo"
                    id="bar" >
                """
            ),
            self.dedent(
                """
                <div id="foo"
                     class="bar">
                    text
                </div>

                <hr class="foo"
                    id="bar" >
                """
            )
        )

    def testAutoLinksDontBreakParser(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <https://example.com>

                <email@example.com>
                """
            ),
            '<p><a href="https://example.com">https://example.com</a></p>\n'
            '<p><a href="&#109;&#97;&#105;&#108;&#116;&#111;&#58;&#101;&#109;'
            '&#97;&#105;&#108;&#64;&#101;&#120;&#97;&#109;&#112;&#108;&#101;'
            '&#46;&#99;&#111;&#109;">&#101;&#109;&#97;&#105;&#108;&#64;&#101;'
            '&#120;&#97;&#109;&#112;&#108;&#101;&#46;&#99;&#111;&#109;</a></p>'
        )

    def testTextLinksIgnored(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                https://example.com

                email@example.com
                """
            ),
            self.dedent(
                """
                <p>https://example.com</p>
                <p>email@example.com</p>
                """
            ),
        )

    def textInvalidTags(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <some [weird](http://example.com) stuff>

                <some>> <<unbalanced>> <<brackets>
                """
            ),
            self.dedent(
                """
                <p><some <a href="http://example.com">weird</a> stuff></p>
                <p><some>&gt; &lt;<unbalanced>&gt; &lt;<brackets></p>
                """
            )
        )

    def testScriptTags(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <script>
                *random stuff* <div> &amp;
                </script>

                <style>
                **more stuff**
                </style>
                """
            ),
            self.dedent(
                """
                <script>
                *random stuff* <div> &amp;
                </script>

                <style>
                **more stuff**
                </style>
                """
            )
        )

    def testUnclosedScriptTag(self):
        # Ensure we have a working fix for https://bugs.python.org/issue41989
        self.assertMarkdownRenders(
            self.dedent(
                """
                <script>
                *random stuff* <div> &amp;

                Still part of the *script* tag
                """
            ),
            self.dedent(
                """
                <script>
                *random stuff* <div> &amp;

                Still part of the *script* tag
                """
            )
        )

    def testInlineScriptTags(self):
        # Ensure inline script tags doesn't cause the parser to eat content (see #1036).
        self.assertMarkdownRenders(
            self.dedent(
                """
                Text `<script>` more *text*.

                <div>
                *foo*
                </div>

                <div>

                bar

                </div>

                A new paragraph with a closing `</script>` tag.
                """
            ),
            self.dedent(
                """
                <p>Text <code>&lt;script&gt;</code> more <em>text</em>.</p>
                <div>
                *foo*
                </div>

                <div>

                bar

                </div>

                <p>A new paragraph with a closing <code>&lt;/script&gt;</code> tag.</p>
                """
            )
        )

    def testHrOnlyStart(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                *emphasis1*
                <hr>
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

    def testHrSelfClose(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                *emphasis1*
                <hr/>
                *emphasis2*
                """
            ),
            self.dedent(
                """
                <p><em>emphasis1</em></p>
                <hr/>
                <p><em>emphasis2</em></p>
                """
            )
        )

    def testHrStartAndEnd(self):
        # Browsers ignore ending hr tags, so we don't try to do anything to handle them special.
        self.assertMarkdownRenders(
            self.dedent(
                """
                *emphasis1*
                <hr></hr>
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

    def testHrOnlyEnd(self):
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

    def testHrWithContent(self):
        # Browsers ignore ending hr tags, so we don't try to do anything to handle them special.
        # Content is not allowed and will be treated as normal content between two hr tags.
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

    def testPlaceholderInSource(self):
        # This should never occur, but third party extensions could create weird edge cases.
        md = markdown.Markdown()
        # Ensure there is an `htmlstash` so relevant code (nested in `if replacements`) is run.
        md.htmlStash.store('foo')
        # Run with a placeholder which is not in the stash
        placeholder = md.htmlStash.getPlaceholder(md.htmlStash.htmlCounter + 1)
        result = md.postprocessors['raw_html'].run(placeholder)
        self.assertEqual(placeholder, result)

    def testNonameTag(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                <div>
                </>
                </div>
                """
            ),
            self.dedent(
                """
                <div>
                </>
                </div>
                """
            )
        )

    def testMultipleBogusCommentsNoHang(self):
        """Test that multiple bogus comments (</` patterns) don't cause infinite loop."""
        self.assertMarkdownRenders(
            '`</` and `</`',
            '<p><code>&lt;/</code> and <code>&lt;/</code></p>'
        )

    def testMultipleUnclosedCommentsNoHang(self):
        """Test that multiple unclosed comments don't cause infinite loop."""
        self.assertMarkdownRenders(
            '<!-- and <!--',
            '<p>&lt;!-- and &lt;!--</p>'
        )

    def testNoHangIssue1586(self):
        """Test no hang condition for issue #1586."""

        self.assertMarkdownRenders(
            'Test `<!--[if mso]>` and `<!--[if !mso]>`',
            '<p>Test <code>&lt;!--[if mso]&gt;</code> and <code>&lt;!--[if !mso]&gt;</code></p>'
        )
