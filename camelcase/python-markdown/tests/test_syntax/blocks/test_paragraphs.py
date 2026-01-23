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


class TestParagraphBlocks(TestCase):

    def testSimpleParagraph(self):
        self.assertMarkdownRenders(
            'A simple paragraph.',

            '<p>A simple paragraph.</p>'
        )

    def testBlankLineBeforeParagraph(self):
        self.assertMarkdownRenders(
            '\nA paragraph preceded by a blank line.',

            '<p>A paragraph preceded by a blank line.</p>'
        )

    def testMultilineParagraph(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This is a paragraph
                on multiple lines
                with hard returns.
                """
            ),
            self.dedent(
                """
                <p>This is a paragraph
                on multiple lines
                with hard returns.</p>
                """
            )
        )

    def testParagraphLongLine(self):
        self.assertMarkdownRenders(
            'A very long long long long long long long long long long long long long long long long long long long '
            'long long long long long long long long long long long long long paragraph on 1 line.',

            '<p>A very long long long long long long long long long long long long long long long long long long '
            'long long long long long long long long long long long long long long paragraph on 1 line.</p>'
        )

    def test2ParagraphsLongLine(self):
        self.assertMarkdownRenders(
            'A very long long long long long long long long long long long long long long long long long long long '
            'long long long long long long long long long long long long long paragraph on 1 line.\n\n'

            'A new long long long long long long long long long long long long long long long '
            'long paragraph on 1 line.',

            '<p>A very long long long long long long long long long long long long long long long long long long '
            'long long long long long long long long long long long long long long paragraph on 1 line.</p>\n'
            '<p>A new long long long long long long long long long long long long long long long '
            'long paragraph on 1 line.</p>'
        )

    def testConsecutiveParagraphs(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                Paragraph 1.

                Paragraph 2.
                """
            ),
            self.dedent(
                """
                <p>Paragraph 1.</p>
                <p>Paragraph 2.</p>
                """
            )
        )

    def testConsecutiveParagraphsTab(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                Paragraph followed by a line with a tab only.
                \t
                Paragraph after a line with a tab only.
                """
            ),
            self.dedent(
                """
                <p>Paragraph followed by a line with a tab only.</p>
                <p>Paragraph after a line with a tab only.</p>
                """
            )
        )

    def testConsecutiveParagraphsSpace(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                Paragraph followed by a line with a space only.

                Paragraph after a line with a space only.
                """
            ),
            self.dedent(
                """
                <p>Paragraph followed by a line with a space only.</p>
                <p>Paragraph after a line with a space only.</p>
                """
            )
        )

    def testConsecutiveMultilineParagraphs(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                Paragraph 1, line 1.
                Paragraph 1, line 2.

                Paragraph 2, line 1.
                Paragraph 2, line 2.
                """
            ),
            self.dedent(
                """
                <p>Paragraph 1, line 1.
                Paragraph 1, line 2.</p>
                <p>Paragraph 2, line 1.
                Paragraph 2, line 2.</p>
                """
            )
        )

    def testParagraphLeadingSpace(self):
        self.assertMarkdownRenders(
            ' A paragraph with 1 leading space.',

            '<p>A paragraph with 1 leading space.</p>'
        )

    def testParagraph2LeadingSpaces(self):
        self.assertMarkdownRenders(
            '  A paragraph with 2 leading spaces.',

            '<p>A paragraph with 2 leading spaces.</p>'
        )

    def testParagraph3LeadingSpaces(self):
        self.assertMarkdownRenders(
            '   A paragraph with 3 leading spaces.',

            '<p>A paragraph with 3 leading spaces.</p>'
        )

    def testParagraphTrailingLeadingSpace(self):
        self.assertMarkdownRenders(
            ' A paragraph with 1 trailing and 1 leading space. ',

            '<p>A paragraph with 1 trailing and 1 leading space. </p>'
        )

    def testParagraphTrailingTab(self):
        self.assertMarkdownRenders(
            'A paragraph with 1 trailing tab.\t',

            '<p>A paragraph with 1 trailing tab.    </p>'
        )

    def testParagraphsCr(self):
        self.assertMarkdownRenders(
            'Paragraph 1, line 1.\rParagraph 1, line 2.\r\rParagraph 2, line 1.\rParagraph 2, line 2.\r',

            self.dedent(
                """
                <p>Paragraph 1, line 1.
                Paragraph 1, line 2.</p>
                <p>Paragraph 2, line 1.
                Paragraph 2, line 2.</p>
                """
            )
        )

    def testParagraphsLf(self):
        self.assertMarkdownRenders(
            'Paragraph 1, line 1.\nParagraph 1, line 2.\n\nParagraph 2, line 1.\nParagraph 2, line 2.\n',

            self.dedent(
                """
                <p>Paragraph 1, line 1.
                Paragraph 1, line 2.</p>
                <p>Paragraph 2, line 1.
                Paragraph 2, line 2.</p>
                """
            )
        )

    def testParagraphsCrLf(self):
        self.assertMarkdownRenders(
            'Paragraph 1, line 1.\r\nParagraph 1, line 2.\r\n\r\nParagraph 2, line 1.\r\nParagraph 2, line 2.\r\n',

            self.dedent(
                """
                <p>Paragraph 1, line 1.
                Paragraph 1, line 2.</p>
                <p>Paragraph 2, line 1.
                Paragraph 2, line 2.</p>
                """
            )
        )

    def testParagraphsNoList(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                Paragraph:
                * no list

                Paragraph
                 * no list

                Paragraph:
                  * no list

                Paragraph:
                   * no list
                """
            ),
            '<p>Paragraph:\n'
            '* no list</p>\n'
            '<p>Paragraph\n'
            ' * no list</p>\n'
            '<p>Paragraph:\n'
            '  * no list</p>\n'
            '<p>Paragraph:\n'
            '   * no list</p>',
        )
