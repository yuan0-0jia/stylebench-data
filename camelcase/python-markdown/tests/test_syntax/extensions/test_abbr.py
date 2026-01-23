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
from markdown import Markdown
from markdown.extensions.abbr import AbbrExtension


class TestAbbr(TestCase):
    maxDiff = None

    defaultKwargs = {'extensions': ['abbr']}

    def testIgnoreAtomic(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This <https://example.com/{YAFR}>

                *[YAFR]: Yet Another Feature Request
                """
            ),
            '<p>This <a href="https://example.com/{YAFR}">https://example.com/{YAFR}</a></p>'
        )

    def testAbbrUpper(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR

                *[ABBR]: Abbreviation
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR</abbr></p>
                """
            )
        )

    def testAbbrLower(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                abbr

                *[abbr]: Abbreviation
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">abbr</abbr></p>
                """
            )
        )

    def testAbbrMultipleInText(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                The HTML specification
                is maintained by the W3C.

                *[HTML]: Hyper Text Markup Language
                *[W3C]:  World Wide Web Consortium
                """
            ),
            self.dedent(
                """
                <p>The <abbr title="Hyper Text Markup Language">HTML</abbr> specification
                is maintained by the <abbr title="World Wide Web Consortium">W3C</abbr>.</p>
                """
            )
        )

    def testAbbrMultipleInTail(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                *The* HTML specification
                is maintained by the W3C.

                *[HTML]: Hyper Text Markup Language
                *[W3C]:  World Wide Web Consortium
                """
            ),
            self.dedent(
                """
                <p><em>The</em> <abbr title="Hyper Text Markup Language">HTML</abbr> specification
                is maintained by the <abbr title="World Wide Web Consortium">W3C</abbr>.</p>
                """
            )
        )

    def testAbbrMultipleNested(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                The *HTML* specification
                is maintained by the *W3C*.

                *[HTML]: Hyper Text Markup Language
                *[W3C]:  World Wide Web Consortium
                """
            ),
            self.dedent(
                """
                <p>The <em><abbr title="Hyper Text Markup Language">HTML</abbr></em> specification
                is maintained by the <em><abbr title="World Wide Web Consortium">W3C</abbr></em>.</p>
                """
            )
        )

    def testAbbrOverride(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR

                *[ABBR]: Ignored
                *[ABBR]: The override
                """
            ),
            self.dedent(
                """
                <p><abbr title="The override">ABBR</abbr></p>
                """
            )
        )

    def testAbbrGlossary(self):

        glossary = {
            "ABBR": "Abbreviation",
            "abbr": "Abbreviation",
            "HTML": "Hyper Text Markup Language",
            "W3C": "World Wide Web Consortium"
        }

        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR
                abbr

                HTML
                W3C
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR</abbr>
                <abbr title="Abbreviation">abbr</abbr></p>
                <p><abbr title="Hyper Text Markup Language">HTML</abbr>
                <abbr title="World Wide Web Consortium">W3C</abbr></p>
                """
            ),
            extensions=[AbbrExtension(glossary=glossary)]
        )

    def testAbbrGlossary2(self):

        glossary = {
            "ABBR": "Abbreviation",
            "abbr": "Abbreviation",
            "HTML": "Hyper Text Markup Language",
            "W3C": "World Wide Web Consortium"
        }

        glossary2 = {
            "ABBR": "New Abbreviation"
        }

        abbrExt = AbbrExtension(glossary=glossary)
        abbrExt.loadGlossary(glossary2)

        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR abbr HTML W3C
                """
            ),
            self.dedent(
                """
                <p><abbr title="New Abbreviation">ABBR</abbr> """
                + """<abbr title="Abbreviation">abbr</abbr> """
                + """<abbr title="Hyper Text Markup Language">HTML</abbr> """
                + """<abbr title="World Wide Web Consortium">W3C</abbr></p>
                """
            ),
            extensions=[abbrExt]
        )

    def testAbbrNested(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                [ABBR](/foo)

                _ABBR_

                *[ABBR]: Abbreviation
                """
            ),
            self.dedent(
                """
                <p><a href="/foo"><abbr title="Abbreviation">ABBR</abbr></a></p>
                <p><em><abbr title="Abbreviation">ABBR</abbr></em></p>
                """
            )
        )

    def testAbbrNoBlankLines(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR
                *[ABBR]: Abbreviation
                ABBR
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR</abbr></p>
                <p><abbr title="Abbreviation">ABBR</abbr></p>
                """
            )
        )

    def testAbbrNoSpace(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR

                *[ABBR]:Abbreviation
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR</abbr></p>
                """
            )
        )

    def testAbbrExtraSpace(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR

                *[ABBR] :      Abbreviation
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR</abbr></p>
                """
            )
        )

    def testAbbrLineBreak(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR

                *[ABBR]:
                    Abbreviation
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR</abbr></p>
                """
            )
        )

    def testAbbrIgnoreUnmatchedCase(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR abbr

                *[ABBR]: Abbreviation
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR</abbr> abbr</p>
                """
            )
        )

    def testAbbrPartialWord(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR ABBREVIATION

                *[ABBR]: Abbreviation
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR</abbr> ABBREVIATION</p>
                """
            )
        )

    def testAbbrUnused(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                foo bar

                *[ABBR]: Abbreviation
                """
            ),
            self.dedent(
                """
                <p>foo bar</p>
                """
            )
        )

    def testAbbrDoubleQuoted(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR

                *[ABBR]: "Abbreviation"
                """
            ),
            self.dedent(
                """
                <p><abbr title="&quot;Abbreviation&quot;">ABBR</abbr></p>
                """
            )
        )

    def testAbbrSingleQuoted(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR

                *[ABBR]: 'Abbreviation'
                """
            ),
            self.dedent(
                """
                <p><abbr title="'Abbreviation'">ABBR</abbr></p>
                """
            )
        )

    def testAbbrIgnoreBackslash(self):
        self.assertMarkdownRenders(
            self.dedent(
                r"""
                \\foo

                *[\\foo]: Not an abbreviation
                """
            ),
            self.dedent(
                r"""
                <p>\foo</p>
                <p>*[\foo]: Not an abbreviation</p>
                """
            )
        )

    def testAbbrHyphen(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR-abbr

                *[ABBR-abbr]: Abbreviation
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR-abbr</abbr></p>
                """
            )
        )

    def testAbbrCarrot(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR^abbr

                *[ABBR^abbr]: Abbreviation
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR^abbr</abbr></p>
                """
            )
        )

    def testAbbrBracket(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ABBR]abbr

                *[ABBR]abbr]: Abbreviation
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation">ABBR]abbr</abbr></p>
                """
            )
        )

    def testAbbrWithAttrList(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                *[abbr]: Abbreviation Definition

                ![Image with abbr in title](abbr.png){title="Image with abbr in title"}
                """
            ),
            self.dedent(
                """
                <p><img alt="Image with abbr in title" src="abbr.png" title="Image with abbr in title" /></p>
                """
            ),
            extensions=['abbr', 'attr_list']
        )

    def testAbbrSupersetVsSubset(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                abbr, SS, and abbr-SS should have different definitions.

                *[abbr]: Abbreviation Definition
                *[abbr-SS]: Abbreviation Superset Definition
                *[SS]: Superset Definition
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation Definition">abbr</abbr>, """
                + """<abbr title="Superset Definition">SS</abbr>, """
                + """and <abbr title="Abbreviation Superset Definition">abbr-SS</abbr> """
                + """should have different definitions.</p>
                """
            )
        )

    def testAbbrEmpty(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                *[abbr]:
                Abbreviation Definition

                abbr

                *[]: Empty

                *[ ]: Empty

                *[abbr]:

                *[ABBR]:

                Testing document text.
                """
            ),
            self.dedent(
                """
                <p><abbr title="Abbreviation Definition">abbr</abbr></p>\n"""
                + """<p>*[]: Empty</p>\n"""
                + """<p>*[ ]: Empty</p>\n"""
                + """<p>*[<abbr title="Abbreviation Definition">abbr</abbr>]:</p>\n"""
                + """<p>*[ABBR]:</p>\n"""
                + """<p>Testing document text.</p>
                """
            )
        )

    def testAbbrClear(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                *[abbr]: Abbreviation Definition
                *[ABBR]: Abbreviation Definition

                abbr ABBR

                *[abbr]: ""
                *[ABBR]: ''
                """
            ),
            self.dedent(
                """
                <p>abbr ABBR</p>
                """
            )
        )

    def testAbbrReset(self):
        ext = AbbrExtension()
        md = Markdown(extensions=[ext])
        md.convert('*[abbr]: Abbreviation Definition')
        self.assertEqual(ext.abbrs, {'abbr': 'Abbreviation Definition'})
        md.convert('*[ABBR]: Capitalised Abbreviation')
        self.assertEqual(ext.abbrs, {'abbr': 'Abbreviation Definition', 'ABBR': 'Capitalised Abbreviation'})
        md.reset()
        self.assertEqual(ext.abbrs, {})
        md.convert('*[foo]: Foo Definition')
        self.assertEqual(ext.abbrs, {'foo': 'Foo Definition'})
