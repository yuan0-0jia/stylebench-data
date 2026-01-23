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


class TestAttrList(TestCase):
    maxDiff = None
    defaultKwargs = {'extensions': ['attr_list']}

    # TODO: Move the rest of the `attr_list` tests here.

    def testEmptyAttrList(self):
        self.assertMarkdownRenders(
            '*foo*{ }',
            '<p><em>foo</em>{ }</p>'
        )

    def testCurlyAfterInline(self):
        self.assertMarkdownRenders(
            '*inline*{.a} } *text*{.a }}',
            '<p><em class="a">inline</em> } <em class="a">text</em>}</p>'
        )

    def testExtraEqGetsIgnoredInsideCurlyInline(self):
        # Undesired behavior but kept for historic compatibility.
        self.assertMarkdownRenders(
            '*inline*{data-test="x" =a} *text*',
            '<p><em data-test="x">inline</em> <em>text</em></p>'
        )

    def testCurlyAfterBlock(self):
        self.assertMarkdownRenders(
            '# Heading {.a} }',
            '<h1>Heading {.a} }</h1>'
        )

    def testCurlyInSingleQuote(self):
        self.assertMarkdownRenders(
            "# Heading {data-test='{}'}",
            '<h1 data-test="{}">Heading</h1>'
        )

    def testCurlyInDoubleQuote(self):
        self.assertMarkdownRenders(
            '# Heading {data-test="{}"}',
            '<h1 data-test="{}">Heading</h1>'
        )

    def testUnclosedQuoteIgnored(self):
        # Undesired behavior but kept for historic compatibility.
        self.assertMarkdownRenders(
            '# Heading {foo="bar}',
            '<h1 foo="&quot;bar">Heading</h1>'
        )

    def testBackslashEscapeValue(self):
        self.assertMarkdownRenders(
            '# `*Foo*` { id="\\*Foo\\*" }',
            '<h1 id="*Foo*"><code>*Foo*</code></h1>'
        )

    def testTableTd(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                | A { .foo }  | *B*{ .foo } | C { } | D{ .foo }     | E { .foo } F |
                |-------------|-------------|-------|---------------|--------------|
                | a { .foo }  | *b*{ .foo } | c { } | d{ .foo }     | e { .foo } f |
                | valid on td | inline      | empty | missing space | not at end   |
                """
            ),
            self.dedent(
                """
                <table>
                <thead>
                <tr>
                <th class="foo">A</th>
                <th><em class="foo">B</em></th>
                <th>C { }</th>
                <th>D{ .foo }</th>
                <th>E { .foo } F</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                <td class="foo">a</td>
                <td><em class="foo">b</em></td>
                <td>c { }</td>
                <td>d{ .foo }</td>
                <td>e { .foo } f</td>
                </tr>
                <tr>
                <td>valid on td</td>
                <td>inline</td>
                <td>empty</td>
                <td>missing space</td>
                <td>not at end</td>
                </tr>
                </tbody>
                </table>
                """
            ),
            extensions=['attr_list', 'tables']
        )
