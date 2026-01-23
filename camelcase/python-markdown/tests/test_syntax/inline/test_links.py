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

Copyright 2007-2019 The Python Markdown Project (v. 1.7 and later)
Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
Copyright 2004 Manfred Stienstra (the original version)

License: BSD (see LICENSE.md for details).
"""

from markdown.test_tools import TestCase


class TestInlineLinks(TestCase):

    def testNestedSquareBrackets(self):
        self.assertMarkdownRenders(
            """[Text[[[[[[[]]]]]]][]](http://link.com) more text""",
            """<p><a href="http://link.com">Text[[[[[[[]]]]]]][]</a> more text</p>"""
        )

    def testNestedRoundBrackets(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/(((((((()))))))())) more text""",
            """<p><a href="http://link.com/(((((((()))))))())">Text</a> more text</p>"""
        )

    def testNestedEscapedBrackets(self):
        self.assertMarkdownRenders(
            R"""[Text](/url\(test\) "title").""",
            """<p><a href="/url(test)" title="title">Text</a>.</p>"""
        )

    def testNestedEscapedBracketsAndAngles(self):
        self.assertMarkdownRenders(
            R"""[Text](</url\(test\)> "title").""",
            """<p><a href="/url(test)" title="title">Text</a>.</p>"""
        )

    def testNestedUnescapedBrackets(self):
        self.assertMarkdownRenders(
            R"""[Text](/url(test) "title").""",
            """<p><a href="/url(test)" title="title">Text</a>.</p>"""
        )

    def testNestedUnescapedBracketsAndAngles(self):
        self.assertMarkdownRenders(
            R"""[Text](</url(test)> "title").""",
            """<p><a href="/url(test)" title="title">Text</a>.</p>"""
        )

    def testUnevenBracketsWithTitles1(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/("title") more text""",
            """<p><a href="http://link.com/(" title="title">Text</a> more text</p>"""
        )

    def testUnevenBracketsWithTitles2(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/('"title") more text""",
            """<p><a href="http://link.com/('" title="title">Text</a> more text</p>"""
        )

    def testUnevenBracketsWithTitles3(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/("title)") more text""",
            """<p><a href="http://link.com/(" title="title)">Text</a> more text</p>"""
        )

    def testUnevenBracketsWithTitles4(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/( "title") more text""",
            """<p><a href="http://link.com/(" title="title">Text</a> more text</p>"""
        )

    def testUnevenBracketsWithTitles5(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/( "title)") more text""",
            """<p><a href="http://link.com/(" title="title)">Text</a> more text</p>"""
        )

    def testMixedTitleQuotes1(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/'"title") more text""",
            """<p><a href="http://link.com/'" title="title">Text</a> more text</p>"""
        )

    def testMixedTitleQuotes2(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/"'title') more text""",
            """<p><a href="http://link.com/&quot;" title="title">Text</a> more text</p>"""
        )

    def testMixedTitleQuotes3(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/with spaces'"and quotes" 'and title') more text""",
            """<p><a href="http://link.com/with spaces" title="&quot;and quotes&quot; 'and title">"""
            """Text</a> more text</p>"""
        )

    def testMixedTitleQuotes4(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/with spaces'"and quotes" 'and title") more text""",
            """<p><a href="http://link.com/with spaces'" title="and quotes&quot; 'and title">Text</a> more text</p>"""
        )

    def testMixedTitleQuotes5(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/with spaces '"and quotes" 'and title') more text""",
            """<p><a href="http://link.com/with spaces" title="&quot;and quotes&quot; 'and title">"""
            """Text</a> more text</p>"""
        )

    def testMixedTitleQuotes6(self):
        self.assertMarkdownRenders(
            """[Text](http://link.com/with spaces "and quotes" 'and title') more text""",
            """<p><a href="http://link.com/with spaces &quot;and quotes&quot;" title="and title">"""
            """Text</a> more text</p>"""
        )

    def testSingleQuote(self):
        self.assertMarkdownRenders(
            """[test](link"notitle)""",
            """<p><a href="link&quot;notitle">test</a></p>"""
        )

    def testAngleWithMixedTitleQuotes(self):
        self.assertMarkdownRenders(
            """[Text](<http://link.com/with spaces '"and quotes"> 'and title') more text""",
            """<p><a href="http://link.com/with spaces '&quot;and quotes&quot;" title="and title">"""
            """Text</a> more text</p>"""
        )

    def testAmpInUrl(self):
        """Test amp in URLs."""

        self.assertMarkdownRenders(
            '[link](http://www.freewisdom.org/this&that)',
            '<p><a href="http://www.freewisdom.org/this&amp;that">link</a></p>'
        )
        self.assertMarkdownRenders(
            '[title](http://example.com/?a=1&amp;b=2)',
            '<p><a href="http://example.com/?a=1&amp;b=2">title</a></p>'
        )
        self.assertMarkdownRenders(
            '[title](http://example.com/?a=1&#x26;b=2)',
            '<p><a href="http://example.com/?a=1&#x26;b=2">title</a></p>'
        )

    def testAnglesAndNonsenseUrl(self):
        self.assertMarkdownRenders(
            '[test nonsense](<?}]*+|&)>).',
            '<p><a href="?}]*+|&amp;)">test nonsense</a>.</p>'
        )


class TestReferenceLinks(TestCase):

    def testRefLink(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]: http://example.com
                """
            ),
            """<p><a href="http://example.com">Text</a></p>"""
        )

    def testRefLinkAngleBrackets(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]: <http://example.com>
                """
            ),
            """<p><a href="http://example.com">Text</a></p>"""
        )

    def testRefLinkNoSpace(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]:http://example.com
                """
            ),
            """<p><a href="http://example.com">Text</a></p>"""
        )

    def testRefLinkAngleBracketsNoSpace(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]:<http://example.com>
                """
            ),
            """<p><a href="http://example.com">Text</a></p>"""
        )

    def testRefLinkAngleBracketsTitle(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]: <http://example.com> "title"
                """
            ),
            """<p><a href="http://example.com" title="title">Text</a></p>"""
        )

    def testRefLinkTitle(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]: http://example.com "title"
                """
            ),
            """<p><a href="http://example.com" title="title">Text</a></p>"""
        )

    def testRefLinkAngleBracketsTitleNoSpace(self):
        # TODO: Maybe reevaluate this?
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]: <http://example.com>"title"
                """
            ),
            """<p><a href="http://example.com&gt;&quot;title&quot;">Text</a></p>"""
        )

    def testRefLinkTitleNoSpace(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]: http://example.com"title"
                """
            ),
            """<p><a href="http://example.com&quot;title&quot;">Text</a></p>"""
        )

    def testRefLinkSingleQuotedTitle(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]: http://example.com 'title'
                """
            ),
            """<p><a href="http://example.com" title="title">Text</a></p>"""
        )

    def testRefLinkTitleNestedQuote(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]: http://example.com "title'"
                """
            ),
            """<p><a href="http://example.com" title="title'">Text</a></p>"""
        )

    def testRefLinkSingleQuotedTitleNestedQuote(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]: http://example.com 'title"'
                """
            ),
            """<p><a href="http://example.com" title="title&quot;">Text</a></p>"""
        )

    def testRefLinkOverride(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]: http://example.com 'ignore'
                [Text]: https://example.com 'override'
                """
            ),
            """<p><a href="https://example.com" title="override">Text</a></p>"""
        )

    def testRefLinkTitleNoBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]
                [Text]: http://example.com "title"
                [Text]
                """
            ),
            self.dedent(
                """
                <p><a href="http://example.com" title="title">Text</a></p>
                <p><a href="http://example.com" title="title">Text</a></p>
                """
            )
        )

    def testRefLinkMultiLine(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]

                [Text]:
                    http://example.com
                    "title"
                """
            ),
            """<p><a href="http://example.com" title="title">Text</a></p>"""
        )

    def testReferenceNewlines(self):
        """Test reference id whitespace cleanup."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                Two things:

                 - I would like to tell you about the [code of
                   conduct][] we are using in this project.
                 - Only one in fact.

                [code of conduct]: https://github.com/Python-Markdown/markdown/blob/master/CODE_OF_CONDUCT.md
                """
            ),
            '<p>Two things:</p>\n<ul>\n<li>I would like to tell you about the '
            '<a href="https://github.com/Python-Markdown/markdown/blob/master/CODE_OF_CONDUCT.md">code of\n'
            '   conduct</a> we are using in this project.</li>\n<li>Only one in fact.</li>\n</ul>'
        )

    def testReferenceAcrossBlocks(self):
        """Test references across blocks."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                I would like to tell you about the [code of

                conduct][] we are using in this project.

                [code of conduct]: https://github.com/Python-Markdown/markdown/blob/master/CODE_OF_CONDUCT.md
                """
            ),
            '<p>I would like to tell you about the [code of</p>\n'
            '<p>conduct][] we are using in this project.</p>'
        )

    def testRefLinkNestedLeftBracket(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text[]

                [Text[]: http://example.com
                """
            ),
            self.dedent(
                """
                <p>[Text[]</p>
                <p>[Text[]: http://example.com</p>
                """
            )
        )

    def testRefLinkNestedRightBracket(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text]]

                [Text]]: http://example.com
                """
            ),
            self.dedent(
                """
                <p>[Text]]</p>
                <p>[Text]]: http://example.com</p>
                """
            )
        )

    def testRefRoundBrackets(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [Text][1].

                [Text][2].

                  [1]: /url(test) "title"
                  [2]: </url(test)> "title"
                """
            ),
            self.dedent(
                """
                <p><a href="/url(test)" title="title">Text</a>.</p>
                <p><a href="/url(test)" title="title">Text</a>.</p>
                """
            )
        )
