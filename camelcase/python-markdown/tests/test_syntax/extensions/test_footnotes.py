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


class TestFootnotes(TestCase):

    defaultKwargs = {'extensions': ['footnotes']}
    maxDiff = None

    def testBasicFootnote(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                paragraph[^1]

                [^1]: A Footnote
                """
            ),
            '<p>paragraph<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>A Footnote&#160;<a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testMultipleFootnotes(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                foo[^1]

                bar[^2]

                [^1]: Footnote 1
                [^2]: Footnote 2
                """
            ),
            '<p>foo<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '<p>bar<sup id="fnref:2"><a class="footnote-ref" href="#fn:2">2</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>Footnote 1&#160;<a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '<li id="fn:2">\n'
            '<p>Footnote 2&#160;<a class="footnote-backref" href="#fnref:2"'
            ' title="Jump back to footnote 2 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testMultipleFootnotesMultiline(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                foo[^1]

                bar[^2]

                [^1]: Footnote 1
                    line 2
                [^2]: Footnote 2
                """
            ),
            '<p>foo<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '<p>bar<sup id="fnref:2"><a class="footnote-ref" href="#fn:2">2</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>Footnote 1\nline 2&#160;<a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '<li id="fn:2">\n'
            '<p>Footnote 2&#160;<a class="footnote-backref" href="#fnref:2"'
            ' title="Jump back to footnote 2 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteMultiLine(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                paragraph[^1]
                [^1]: A Footnote
                    line 2
                """
            ),
            '<p>paragraph<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>A Footnote\nline 2&#160;<a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteMultiLineLazyIndent(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                paragraph[^1]
                [^1]: A Footnote
                line 2
                """
            ),
            '<p>paragraph<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>A Footnote\nline 2&#160;<a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteMultiLineComplex(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                paragraph[^1]

                [^1]:

                    A Footnote
                    line 2

                    * list item

                    > blockquote
                """
            ),
            '<p>paragraph<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>A Footnote\nline 2</p>\n'
            '<ul>\n<li>list item</li>\n</ul>\n'
            '<blockquote>\n<p>blockquote</p>\n</blockquote>\n'
            '<p><a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteMultpleComplex(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                foo[^1]

                bar[^2]

                [^1]:

                    A Footnote
                    line 2

                    * list item

                    > blockquote

                [^2]: Second footnote

                    paragraph 2
                """
            ),
            '<p>foo<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '<p>bar<sup id="fnref:2"><a class="footnote-ref" href="#fn:2">2</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>A Footnote\nline 2</p>\n'
            '<ul>\n<li>list item</li>\n</ul>\n'
            '<blockquote>\n<p>blockquote</p>\n</blockquote>\n'
            '<p><a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '<li id="fn:2">\n'
            '<p>Second footnote</p>\n'
            '<p>paragraph 2&#160;<a class="footnote-backref" href="#fnref:2"'
            ' title="Jump back to footnote 2 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteMultpleComplexNoBlankLineBetween(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                foo[^1]

                bar[^2]

                [^1]:

                    A Footnote
                    line 2

                    * list item

                    > blockquote
                [^2]: Second footnote

                    paragraph 2
                """
            ),
            '<p>foo<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '<p>bar<sup id="fnref:2"><a class="footnote-ref" href="#fn:2">2</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>A Footnote\nline 2</p>\n'
            '<ul>\n<li>list item</li>\n</ul>\n'
            '<blockquote>\n<p>blockquote</p>\n</blockquote>\n'
            '<p><a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '<li id="fn:2">\n'
            '<p>Second footnote</p>\n'
            '<p>paragraph 2&#160;<a class="footnote-backref" href="#fnref:2"'
            ' title="Jump back to footnote 2 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testBacklinkText(self):
        """Test back-link configuration."""

        self.assertMarkdownRenders(
            'paragraph[^1]\n\n[^1]: A Footnote',
            '<p>paragraph<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>A Footnote&#160;<a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote 1 in the text">back</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>',
            extension_configs={'footnotes': {'BACKLINK_TEXT': 'back'}}
        )

    def testFootnoteSeparator(self):
        """Test separator configuration."""

        self.assertMarkdownRenders(
            'paragraph[^1]\n\n[^1]: A Footnote',
            '<p>paragraph<sup id="fnref-1"><a class="footnote-ref" href="#fn-1">1</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn-1">\n'
            '<p>A Footnote&#160;<a class="footnote-backref" href="#fnref-1"'
            ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>',
            extension_configs={'footnotes': {'SEPARATOR': '-'}}
        )

    def testBacklinkTitle(self):
        """Test back-link title configuration without placeholder."""

        self.assertMarkdownRenders(
            'paragraph[^1]\n\n[^1]: A Footnote',
            '<p>paragraph<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>A Footnote&#160;<a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>',
            extension_configs={'footnotes': {'BACKLINK_TITLE': 'Jump back to footnote'}}
        )

    def testSuperscriptText(self):
        """Test superscript text configuration."""

        self.assertMarkdownRenders(
            'paragraph[^1]\n\n[^1]: A Footnote',
            '<p>paragraph<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">[1]</a></sup></p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>A Footnote&#160;<a class="footnote-backref" href="#fnref:1"'
            ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>',
            extension_configs={'footnotes': {'SUPERSCRIPT_TEXT': '[{}]'}}
        )

    def testFootnoteOrderByDocOrder(self):
        """Test that footnotes occur in order of reference appearance when so configured."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                First footnote reference[^first]. Second footnote reference[^last].

                [^last]: Second footnote.
                [^first]: First footnote.
                """
            ),
            '<p>First footnote reference<sup id="fnref:first"><a class="footnote-ref" '
            'href="#fn:first">1</a></sup>. Second footnote reference<sup id="fnref:last">'
            '<a class="footnote-ref" href="#fn:last">2</a></sup>.</p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:first">\n'
            '<p>First footnote.&#160;<a class="footnote-backref" href="#fnref:first" '
            'title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '<li id="fn:last">\n'
            '<p>Second footnote.&#160;<a class="footnote-backref" href="#fnref:last" '
            'title="Jump back to footnote 2 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>',
            extension_configs={'footnotes': {'USE_DEFINITION_ORDER': False}}
        )

    def testFootnoteOrderTricky(self):
        """Test a tricky sequence of footnote references."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                `Footnote reference in code spans should be ignored[^tricky]`.
                A footnote reference[^ordinary].
                Another footnote reference[^tricky].

                [^ordinary]: This should be the first footnote.
                [^tricky]: This should be the second footnote.
                """
            ),
            '<p><code>Footnote reference in code spans should be ignored[^tricky]</code>.\n'
            'A footnote reference<sup id="fnref:ordinary">'
            '<a class="footnote-ref" href="#fn:ordinary">1</a></sup>.\n'
            'Another footnote reference<sup id="fnref:tricky">'
            '<a class="footnote-ref" href="#fn:tricky">2</a></sup>.</p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:ordinary">\n'
            '<p>This should be the first footnote.&#160;<a class="footnote-backref" '
            'href="#fnref:ordinary" title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '<li id="fn:tricky">\n'
            '<p>This should be the second footnote.&#160;<a class="footnote-backref" '
            'href="#fnref:tricky" title="Jump back to footnote 2 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteOrderByDefinition(self):
        """Test that footnotes occur in order of definition occurrence when so configured."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                First footnote reference[^last_def]. Second footnote reference[^first_def].

                [^first_def]: First footnote.
                [^last_def]: Second footnote.
                """
            ),
            '<p>First footnote reference<sup id="fnref:last_def"><a class="footnote-ref" '
            'href="#fn:last_def">2</a></sup>. Second footnote reference<sup id="fnref:first_def">'
            '<a class="footnote-ref" href="#fn:first_def">1</a></sup>.</p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:first_def">\n'
            '<p>First footnote.&#160;<a class="footnote-backref" href="#fnref:first_def" '
            'title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '<li id="fn:last_def">\n'
            '<p>Second footnote.&#160;<a class="footnote-backref" href="#fnref:last_def" '
            'title="Jump back to footnote 2 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>',
            extension_configs={'footnotes': {'USE_DEFINITION_ORDER': True}}
        )

    def testFootnoteReferenceWithinCodeSpan(self):
        """Test footnote reference within a code span."""

        self.assertMarkdownRenders(
            'A `code span with a footnote[^1] reference`.',
            '<p>A <code>code span with a footnote[^1] reference</code>.</p>'
        )

    def testFootnoteReferenceWithinLink(self):
        """Test footnote reference within a link."""

        self.assertMarkdownRenders(
            'A [link with a footnote[^1] reference](http://example.com).',
            '<p>A <a href="http://example.com">link with a footnote[^1] reference</a>.</p>'
        )

    def testFootnoteReferenceWithinFootnoteDefinition(self):
        """Test footnote definition containing another footnote reference."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                Main footnote[^main].

                [^main]: This footnote references another[^nested].
                [^nested]: Nested footnote.
                """
            ),
            '<p>Main footnote<sup id="fnref:main"><a class="footnote-ref" href="#fn:main">1</a></sup>.</p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:main">\n'
            '<p>This footnote references another<sup id="fnref:nested"><a class="footnote-ref" '
            'href="#fn:nested">2</a></sup>.&#160;<a class="footnote-backref" href="#fnref:main" '
            'title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '<li id="fn:nested">\n'
            '<p>Nested footnote.&#160;<a class="footnote-backref" href="#fnref:nested" '
            'title="Jump back to footnote 2 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteReferenceWithinBlockquote(self):
        """Test footnote reference within a blockquote."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                > This is a quote with a footnote[^quote].

                [^quote]: Quote footnote.
                """
            ),
            '<blockquote>\n'
            '<p>This is a quote with a footnote<sup id="fnref:quote">'
            '<a class="footnote-ref" href="#fn:quote">1</a></sup>.</p>\n'
            '</blockquote>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:quote">\n'
            '<p>Quote footnote.&#160;<a class="footnote-backref" href="#fnref:quote" '
            'title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteReferenceWithinList(self):
        """Test footnote reference within a list item."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                1. First item with footnote[^note]
                1. Second item

                [^note]: List footnote.
                """
            ),
            '<ol>\n'
            '<li>First item with footnote<sup id="fnref:note">'
            '<a class="footnote-ref" href="#fn:note">1</a></sup></li>\n'
            '<li>Second item</li>\n'
            '</ol>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:note">\n'
            '<p>List footnote.&#160;<a class="footnote-backref" href="#fnref:note" '
            'title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteReferencesWithinLooseList(self):
        """Test footnote references within loose list items."""

        self.assertMarkdownRenders(
            self.dedent(
                '''
                * Reference to [^first]

                * Reference to [^second]

                [^first]: First footnote definition
                [^second]: Second footnote definition
                '''
            ),
            '<ul>\n'
            '<li>\n'
            '<p>Reference to <sup id="fnref:first"><a class="footnote-ref" href="#fn:first">1</a></sup></p>\n'
            '</li>\n'
            '<li>\n'
            '<p>Reference to <sup id="fnref:second"><a class="footnote-ref" href="#fn:second">2</a></sup></p>\n'
            '</li>\n'
            '</ul>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:first">\n'
            '<p>First footnote definition&#160;<a class="footnote-backref" href="#fnref:first" '
            'title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '<li id="fn:second">\n'
            '<p>Second footnote definition&#160;<a class="footnote-backref" href="#fnref:second" '
            'title="Jump back to footnote 2 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteReferenceWithinHtml(self):
        """Test footnote reference within HTML tags."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                A <span>footnote reference[^1] within a span element</span>.

                [^1]: The footnote.
                """
            ),
            '<p>A <span>footnote reference<sup id="fnref:1">'
            '<a class="footnote-ref" href="#fn:1">1</a>'
            '</sup> within a span element</span>.</p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:1">\n'
            '<p>The footnote.&#160;<a class="footnote-backref" href="#fnref:1" '
            'title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testDuplicateFootnoteReferences(self):
        """Test multiple references to the same footnote."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                First[^dup] and second[^dup] reference.

                [^dup]: Duplicate footnote.
                """
            ),
            '<p>First<sup id="fnref:dup">'
            '<a class="footnote-ref" href="#fn:dup">1</a></sup> and second<sup id="fnref2:dup">'
            '<a class="footnote-ref" href="#fn:dup">1</a></sup> reference.</p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:dup">\n'
            '<p>Duplicate footnote.&#160;'
            '<a class="footnote-backref" href="#fnref:dup" '
            'title="Jump back to footnote 1 in the text">&#8617;</a>'
            '<a class="footnote-backref" href="#fnref2:dup" '
            'title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteReferenceWithoutDefinition(self):
        """Test footnote reference without corresponding definition."""

        self.assertMarkdownRenders(
            'This has a missing footnote[^missing].',
            '<p>This has a missing footnote[^missing].</p>'
        )

    def testFootnoteDefinitionWithoutReference(self):
        """Test footnote definition without corresponding reference."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                No reference here.

                [^orphan]: Orphaned footnote.
                """
            ),
            '<p>No reference here.</p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:orphan">\n'
            '<p>Orphaned footnote.&#160;<a class="footnote-backref" href="#fnref:orphan" '
            'title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )

    def testFootnoteIdWithSpecialChars(self):
        """Test footnote id containing special and Unicode characters."""

        self.assertMarkdownRenders(
            self.dedent(
                """
                Special footnote id[^!#¤%/()=?+}{§øé].

                [^!#¤%/()=?+}{§øé]: The footnote.
                """
            ),
            '<p>Special footnote id<sup id="fnref:!#¤%/()=?+}{§øé">'
            '<a class="footnote-ref" href="#fn:!#¤%/()=?+}{§øé">1</a></sup>.</p>\n'
            '<div class="footnote">\n'
            '<hr />\n'
            '<ol>\n'
            '<li id="fn:!#¤%/()=?+}{§øé">\n'
            '<p>The footnote.&#160;<a class="footnote-backref" href="#fnref:!#¤%/()=?+}{§øé" '
            'title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
            '</li>\n'
            '</ol>\n'
            '</div>'
        )
