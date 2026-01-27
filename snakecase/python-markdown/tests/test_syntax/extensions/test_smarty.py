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

Copyright 2007-2022 The Python Markdown Project (v. 1.7 and later)
Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
Copyright 2004 Manfred Stienstra (the original version)

License: BSD (see LICENSE.md for details).
"""

from markdown.test_tools import TestCase


class TestSmarty(TestCase):

    default_kwargs = {'extensions': ['smarty']}

    def test_basic(self):
        self.assert_markdown_renders(
            "It's fun. What's fun?",
            '<p>It&rsquo;s fun. What&rsquo;s fun?</p>'
        )
        self.assert_markdown_renders(
            '"Isn\'t this fun"? --- she said...',
            '<p>&ldquo;Isn&rsquo;t this fun&rdquo;? &mdash; she said&hellip;</p>'
        )
        self.assert_markdown_renders(
            '"\'Quoted\' words in a larger quote."',
            '<p>&ldquo;&lsquo;Quoted&rsquo; words in a larger quote.&rdquo;</p>'
        )
        self.assert_markdown_renders(
            '\'Quoted "words" in a larger quote.\'',
            '<p>&lsquo;Quoted &ldquo;words&rdquo; in a larger quote.&rsquo;</p>'
        )
        self.assert_markdown_renders(
            '"Quoted words at the \'end.\'"',
            '<p>&ldquo;Quoted words at the &lsquo;end.&rsquo;&rdquo;</p>'
        )
        self.assert_markdown_renders(
            '\'Quoted words at the "end."\'',
            '<p>&lsquo;Quoted words at the &ldquo;end.&rdquo;&rsquo;</p>'
        )
        self.assert_markdown_renders(
            '(He replied, "She said \'Hello.\'")',
            '<p>(He replied, &ldquo;She said &lsquo;Hello.&rsquo;&rdquo;)</p>'
        )
        self.assert_markdown_renders(
            '<span>He replied, "She said \'Hello.\'"</span>',
            '<p><span>He replied, &ldquo;She said &lsquo;Hello.&rsquo;&rdquo;</span></p>'
        )
        self.assert_markdown_renders(
            '"quoted" text and **bold "quoted" text**',
            '<p>&ldquo;quoted&rdquo; text and <strong>bold &ldquo;quoted&rdquo; text</strong></p>'
        )
        self.assert_markdown_renders(
            "'quoted' text and **bold 'quoted' text**",
            '<p>&lsquo;quoted&rsquo; text and <strong>bold &lsquo;quoted&rsquo; text</strong></p>'
        )
        self.assert_markdown_renders(
            'em-dashes (---) and ellipes (...)',
            '<p>em-dashes (&mdash;) and ellipes (&hellip;)</p>'
        )
        self.assert_markdown_renders(
            '"[Link](http://example.com)" --- she said.',
            '<p>&ldquo;<a href="http://example.com">Link</a>&rdquo; &mdash; she said.</p>'
        )
        self.assert_markdown_renders(
            '"Ellipsis within quotes..."',
            '<p>&ldquo;Ellipsis within quotes&hellip;&rdquo;</p>'
        )
        self.assert_markdown_renders(
            "*Custer*'s Last Stand",
            "<p><em>Custer</em>&rsquo;s Last Stand</p>"
        )

    def test_years(self):
        self.assert_markdown_renders("1440--80's", '<p>1440&ndash;80&rsquo;s</p>')
        self.assert_markdown_renders("1440--'80s", '<p>1440&ndash;&rsquo;80s</p>')
        self.assert_markdown_renders("1440---'80s", '<p>1440&mdash;&rsquo;80s</p>')
        self.assert_markdown_renders("1960's", '<p>1960&rsquo;s</p>')
        self.assert_markdown_renders("one two '60s", '<p>one two &rsquo;60s</p>')
        self.assert_markdown_renders("'60s", '<p>&rsquo;60s</p>')

    def test_wrapping_line(self):
        text = (
            "A line that 'wraps' with\n"
            "*emphasis* at the beginning of the next line."
        )
        html = (
            '<p>A line that &lsquo;wraps&rsquo; with\n'
            '<em>emphasis</em> at the beginning of the next line.</p>'
        )
        self.assert_markdown_renders(text, html)

    def test_escaped(self):
        self.assert_markdown_renders(
            'Escaped \\-- ndash',
            '<p>Escaped -- ndash</p>'
        )
        self.assert_markdown_renders(
            '\\\'Escaped\\\' \\"quotes\\"',
            '<p>\'Escaped\' "quotes"</p>'
        )
        self.assert_markdown_renders(
            'Escaped ellipsis\\...',
            '<p>Escaped ellipsis...</p>'
        )
        self.assert_markdown_renders(
            '\'Escaped \\"quotes\\" in real ones\'',
            '<p>&lsquo;Escaped "quotes" in real ones&rsquo;</p>'
        )
        self.assert_markdown_renders(
            '\\\'"Real" quotes in escaped ones\\\'',
            "<p>'&ldquo;Real&rdquo; quotes in escaped ones'</p>"
        )

    def test_escaped_attr(self):
        self.assert_markdown_renders(
            '![x\"x](x)',
            '<p><img alt="x&quot;x" src="x" /></p>'
        )

    def test_code_spans(self):
        self.assert_markdown_renders(
            'Skip `"code" -- --- \'spans\' ...`.',
            '<p>Skip <code>"code" -- --- \'spans\' ...</code>.</p>'
        )

    def test_code_blocks(self):
        text = (
            '    Also skip "code" \'blocks\'\n'
            '    foo -- bar --- baz ...'
        )
        html = (
            '<pre><code>Also skip "code" \'blocks\'\n'
            'foo -- bar --- baz ...\n'
            '</code></pre>'
        )
        self.assert_markdown_renders(text, html)

    def test_horizontal_rule(self):
        self.assert_markdown_renders('--- -- ---', '<hr />')


class TestSmartyAngledQuotes(TestCase):

    default_kwargs = {
        'extensions': ['smarty'],
        'extension_configs': {
            'smarty': {
                'smart_angled_quotes': True,
            },
        },
    }

    def test_angled_quotes(self):
        self.assert_markdown_renders(
            '<<hello>>',
            '<p>&laquo;hello&raquo;</p>'
        )
        self.assert_markdown_renders(
            'Кавычки-<<ёлочки>>',
            '<p>Кавычки-&laquo;ёлочки&raquo;</p>'
        )
        self.assert_markdown_renders(
            'Anführungszeichen->>Chevrons<<',
            '<p>Anführungszeichen-&raquo;Chevrons&laquo;</p>'
        )


class TestSmartyCustomSubstitutions(TestCase):

    default_kwargs = {
        'extensions': ['smarty'],
        'extension_configs': {
            'smarty': {
                'smart_angled_quotes': True,
                'substitutions': {
                    'ndash': '\u2013',
                    'mdash': '\u2014',
                    'ellipsis': '\u2026',
                    'left-single-quote': '&sbquo;',  # `sb` is not a typo!
                    'right-single-quote': '&lsquo;',
                    'left-double-quote': '&bdquo;',
                    'right-double-quote': '&ldquo;',
                    'left-angle-quote': '[',
                    'right-angle-quote': ']',
                },
            },
        },
    }

    def test_custom_substitutions(self):
        text = (
            '<< The "Unicode char of the year 2014"\n'
            "is the 'mdash': ---\n"
            "Must not be confused with 'ndash'  (--) ... >>"
        )
        html = (
            '<p>[ The &bdquo;Unicode char of the year 2014&ldquo;\n'
            'is the &sbquo;mdash&lsquo;: \u2014\n'
            'Must not be confused with &sbquo;ndash&lsquo;  (\u2013) \u2026 ]</p>'
        )
        self.assert_markdown_renders(text, html)


class TestSmartyAndToc(TestCase):

    default_kwargs = {
        'extensions': ['smarty', 'toc'],
    }

    def test_smarty_and_toc(self):
        self.assert_markdown_renders(
            '# *Foo* --- `bar`',
            '<h1 id="foo-bar"><em>Foo</em> &mdash; <code>bar</code></h1>',
            expected_attrs={
                'toc_tokens': [
                    {
                        'level': 1,
                        'id': 'foo-bar',
                        'name': 'Foo &mdash; bar',
                        'html': '<em>Foo</em> &mdash; <code>bar</code>',
                        'data-toc-label': '',
                        'children': [],
                    },
                ],
            },
        )
