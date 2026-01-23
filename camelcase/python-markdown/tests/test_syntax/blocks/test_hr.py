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


class TestHorizontalRules(TestCase):

    def testHrAsterisks(self):
        self.assertMarkdownRenders(
            '***',

            '<hr />'
        )

    def testHrAsterisksSpaces(self):
        self.assertMarkdownRenders(
            '* * *',

            '<hr />'
        )

    def testHrAsterisksLong(self):
        self.assertMarkdownRenders(
            '*******',

            '<hr />'
        )

    def testHrAsterisksSpacesLong(self):
        self.assertMarkdownRenders(
            '* * * * * * *',

            '<hr />'
        )

    def testHrAsterisks1Indent(self):
        self.assertMarkdownRenders(
            ' ***',

            '<hr />'
        )

    def testHrAsterisksSpaces1Indent(self):
        self.assertMarkdownRenders(
            ' * * *',

            '<hr />'
        )

    def testHrAsterisks2Indent(self):
        self.assertMarkdownRenders(
            '  ***',

            '<hr />'
        )

    def testHrAsterisksSpaces2Indent(self):
        self.assertMarkdownRenders(
            '  * * *',

            '<hr />'
        )

    def testHrAsterisks3Indent(self):
        self.assertMarkdownRenders(
            '   ***',

            '<hr />'
        )

    def testHrAsterisksSpaces3Indent(self):
        self.assertMarkdownRenders(
            '   * * *',

            '<hr />'
        )

    def testHrAsterisksTrailingSpace(self):
        self.assertMarkdownRenders(
            '*** ',

            '<hr />'
        )

    def testHrAsterisksSpacesTrailingSpace(self):
        self.assertMarkdownRenders(
            '* * * ',

            '<hr />'
        )

    def testHrHyphens(self):
        self.assertMarkdownRenders(
            '---',

            '<hr />'
        )

    def testHrHyphensSpaces(self):
        self.assertMarkdownRenders(
            '- - -',

            '<hr />'
        )

    def testHrHyphensLong(self):
        self.assertMarkdownRenders(
            '-------',

            '<hr />'
        )

    def testHrHyphensSpacesLong(self):
        self.assertMarkdownRenders(
            '- - - - - - -',

            '<hr />'
        )

    def testHrHyphens1Indent(self):
        self.assertMarkdownRenders(
            ' ---',

            '<hr />'
        )

    def testHrHyphensSpaces1Indent(self):
        self.assertMarkdownRenders(
            ' - - -',

            '<hr />'
        )

    def testHrHyphens2Indent(self):
        self.assertMarkdownRenders(
            '  ---',

            '<hr />'
        )

    def testHrHyphensSpaces2Indent(self):
        self.assertMarkdownRenders(
            '  - - -',

            '<hr />'
        )

    def testHrHyphens3Indent(self):
        self.assertMarkdownRenders(
            '   ---',

            '<hr />'
        )

    def testHrHyphensSpaces3Indent(self):
        self.assertMarkdownRenders(
            '   - - -',

            '<hr />'
        )

    def testHrHyphensTrailingSpace(self):
        self.assertMarkdownRenders(
            '--- ',

            '<hr />'
        )

    def testHrHyphensSpacesTrailingSpace(self):
        self.assertMarkdownRenders(
            '- - - ',

            '<hr />'
        )

    def testHrUnderscores(self):
        self.assertMarkdownRenders(
            '___',

            '<hr />'
        )

    def testHrUnderscoresSpaces(self):
        self.assertMarkdownRenders(
            '_ _ _',

            '<hr />'
        )

    def testHrUnderscoresLong(self):
        self.assertMarkdownRenders(
            '_______',

            '<hr />'
        )

    def testHrUnderscoresSpacesLong(self):
        self.assertMarkdownRenders(
            '_ _ _ _ _ _ _',

            '<hr />'
        )

    def testHrUnderscores1Indent(self):
        self.assertMarkdownRenders(
            ' ___',

            '<hr />'
        )

    def testHrUnderscoresSpaces1Indent(self):
        self.assertMarkdownRenders(
            ' _ _ _',

            '<hr />'
        )

    def testHrUnderscores2Indent(self):
        self.assertMarkdownRenders(
            '  ___',

            '<hr />'
        )

    def testHrUnderscoresSpaces2Indent(self):
        self.assertMarkdownRenders(
            '  _ _ _',

            '<hr />'
        )

    def testHrUnderscores3Indent(self):
        self.assertMarkdownRenders(
            '   ___',

            '<hr />'
        )

    def testHrUnderscoresSpaces3Indent(self):
        self.assertMarkdownRenders(
            '   _ _ _',

            '<hr />'
        )

    def testHrUnderscoresTrailingSpace(self):
        self.assertMarkdownRenders(
            '___ ',

            '<hr />'
        )

    def testHrUnderscoresSpacesTrailingSpace(self):
        self.assertMarkdownRenders(
            '_ _ _ ',

            '<hr />'
        )

    def testHrBeforeParagraph(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ***
                An HR followed by a paragraph with no blank line.
                """
            ),
            self.dedent(
                """
                <hr />
                <p>An HR followed by a paragraph with no blank line.</p>
                """
            )
        )

    def testHrAfterParagraph(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                A paragraph followed by an HR with no blank line.
                ***
                """
            ),
            self.dedent(
                """
                <p>A paragraph followed by an HR with no blank line.</p>
                <hr />
                """
            )
        )

    def testHrAfterEmstrong(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ***text***
                ***
                """
            ),
            self.dedent(
                """
                <p><strong><em>text</em></strong></p>
                <hr />
                """
            )
        )

    def testNotHr2Asterisks(self):
        self.assertMarkdownRenders(
            '**',

            '<p>**</p>'
        )

    def testNotHr2AsterisksSpaces(self):
        self.assertMarkdownRenders(
            '* *',

            self.dedent(
                """
                <ul>
                <li>*</li>
                </ul>
                """
            )
        )

    def testNotHr2Hyphens(self):
        self.assertMarkdownRenders(
            '--',

            '<p>--</p>'
        )

    def testNotHr2HyphensSpaces(self):
        self.assertMarkdownRenders(
            '- -',

            self.dedent(
                """
                <ul>
                <li>-</li>
                </ul>
                """
            )
        )

    def testNotHr2Underscores(self):
        self.assertMarkdownRenders(
            '__',

            '<p>__</p>'
        )

    def testNotHr2UnderscoresSpaces(self):
        self.assertMarkdownRenders(
            '_ _',

            '<p>_ _</p>'
        )

    def test2ConsecutiveHr(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                - - -
                - - -
                """
            ),
            self.dedent(
                """
                <hr />
                <hr />
                """
            )
        )

    def testNotHrEndInChar(self):
        self.assertMarkdownRenders(
            '--------------------------------------c',

            '<p>--------------------------------------c</p>'
        )
