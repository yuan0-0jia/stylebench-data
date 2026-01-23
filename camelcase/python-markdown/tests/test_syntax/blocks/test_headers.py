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

import unittest
from markdown.test_tools import TestCase


class TestSetextHeaders(TestCase):

    def testSetextH1(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This is an H1
                =============
                """
            ),

            '<h1>This is an H1</h1>'
        )

    def testSetextH2(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This is an H2
                -------------
                """
            ),

            '<h2>This is an H2</h2>'
        )

    def testSetextH1MismatchedLength(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This is an H1
                ===
                """
            ),

            '<h1>This is an H1</h1>'
        )

    def testSetextH2MismatchedLength(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This is an H2
                ---
                """
            ),

            '<h2>This is an H2</h2>'
        )

    def testSetextH1FollowedByP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This is an H1
                =============
                Followed by a Paragraph with no blank line.
                """
            ),
            self.dedent(
                """
                <h1>This is an H1</h1>
                <p>Followed by a Paragraph with no blank line.</p>
                """
            )
        )

    def testSetextH2FollowedByP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This is an H2
                -------------
                Followed by a Paragraph with no blank line.
                """
            ),
            self.dedent(
                """
                <h2>This is an H2</h2>
                <p>Followed by a Paragraph with no blank line.</p>
                """
            )
        )

    # TODO: fix this
    # see https://johnmacfarlane.net/babelmark2/?normalize=1&text=Paragraph%0AAn+H1%0A%3D%3D%3D%3D%3D
    @unittest.skip('This is broken in Python-Markdown')
    def testPFollowedBySetextH1(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This is a Paragraph.
                Followed by an H1 with no blank line.
                =====================================
                """
            ),
            self.dedent(
                """
                <p>This is a Paragraph.</p>
                <h1>Followed by an H1 with no blank line.</h1>
                """
            )
        )

    # TODO: fix this
    # see https://johnmacfarlane.net/babelmark2/?normalize=1&text=Paragraph%0AAn+H2%0A-----
    @unittest.skip('This is broken in Python-Markdown')
    def testPFollowedBySetextH2(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This is a Paragraph.
                Followed by an H2 with no blank line.
                -------------------------------------
                """
            ),
            self.dedent(
                """
                <p>This is a Paragraph.</p>
                <h2>Followed by an H2 with no blank line.</h2>
                """
            )
        )


class TestHashHeaders(TestCase):

    def testHashH1Open(self):
        self.assertMarkdownRenders(
            '# This is an H1',

            '<h1>This is an H1</h1>'
        )

    def testHashH2Open(self):
        self.assertMarkdownRenders(
            '## This is an H2',

            '<h2>This is an H2</h2>'
        )

    def testHashH3Open(self):
        self.assertMarkdownRenders(
            '### This is an H3',

            '<h3>This is an H3</h3>'
        )

    def testHashH4Open(self):
        self.assertMarkdownRenders(
            '#### This is an H4',

            '<h4>This is an H4</h4>'
        )

    def testHashH5Open(self):
        self.assertMarkdownRenders(
            '##### This is an H5',

            '<h5>This is an H5</h5>'
        )

    def testHashH6Open(self):
        self.assertMarkdownRenders(
            '###### This is an H6',

            '<h6>This is an H6</h6>'
        )

    def testHashGt6Open(self):
        self.assertMarkdownRenders(
            '####### This is an H6',

            '<h6># This is an H6</h6>'
        )

    def testHashH1OpenMissingSpace(self):
        self.assertMarkdownRenders(
            '#This is an H1',

            '<h1>This is an H1</h1>'
        )

    def testHashH2OpenMissingSpace(self):
        self.assertMarkdownRenders(
            '##This is an H2',

            '<h2>This is an H2</h2>'
        )

    def testHashH3OpenMissingSpace(self):
        self.assertMarkdownRenders(
            '###This is an H3',

            '<h3>This is an H3</h3>'
        )

    def testHashH4OpenMissingSpace(self):
        self.assertMarkdownRenders(
            '####This is an H4',

            '<h4>This is an H4</h4>'
        )

    def testHashH5OpenMissingSpace(self):
        self.assertMarkdownRenders(
            '#####This is an H5',

            '<h5>This is an H5</h5>'
        )

    def testHashH6OpenMissingSpace(self):
        self.assertMarkdownRenders(
            '######This is an H6',

            '<h6>This is an H6</h6>'
        )

    def testHashGt6OpenMissingSpace(self):
        self.assertMarkdownRenders(
            '#######This is an H6',

            '<h6>#This is an H6</h6>'
        )

    def testHashH1Closed(self):
        self.assertMarkdownRenders(
            '# This is an H1 #',

            '<h1>This is an H1</h1>'
        )

    def testHashH2Closed(self):
        self.assertMarkdownRenders(
            '## This is an H2 ##',

            '<h2>This is an H2</h2>'
        )

    def testHashH3Closed(self):
        self.assertMarkdownRenders(
            '### This is an H3 ###',

            '<h3>This is an H3</h3>'
        )

    def testHashH4Closed(self):
        self.assertMarkdownRenders(
            '#### This is an H4 ####',

            '<h4>This is an H4</h4>'
        )

    def testHashH5Closed(self):
        self.assertMarkdownRenders(
            '##### This is an H5 #####',

            '<h5>This is an H5</h5>'
        )

    def testHashH6Closed(self):
        self.assertMarkdownRenders(
            '###### This is an H6 ######',

            '<h6>This is an H6</h6>'
        )

    def testHashGt6Closed(self):
        self.assertMarkdownRenders(
            '####### This is an H6 #######',

            '<h6># This is an H6</h6>'
        )

    def testHashH1ClosedMissingSpace(self):
        self.assertMarkdownRenders(
            '#This is an H1#',

            '<h1>This is an H1</h1>'
        )

    def testHashH2ClosedMissingSpace(self):
        self.assertMarkdownRenders(
            '##This is an H2##',

            '<h2>This is an H2</h2>'
        )

    def testHashH3ClosedMissingSpace(self):
        self.assertMarkdownRenders(
            '###This is an H3###',

            '<h3>This is an H3</h3>'
        )

    def testHashH4ClosedMissingSpace(self):
        self.assertMarkdownRenders(
            '####This is an H4####',

            '<h4>This is an H4</h4>'
        )

    def testHashH5ClosedMissingSpace(self):
        self.assertMarkdownRenders(
            '#####This is an H5#####',

            '<h5>This is an H5</h5>'
        )

    def testHashH6ClosedMissingSpace(self):
        self.assertMarkdownRenders(
            '######This is an H6######',

            '<h6>This is an H6</h6>'
        )

    def testHashGt6ClosedMissingSpace(self):
        self.assertMarkdownRenders(
            '#######This is an H6#######',

            '<h6>#This is an H6</h6>'
        )

    def testHashH1ClosedMismatch(self):
        self.assertMarkdownRenders(
            '# This is an H1 ##',

            '<h1>This is an H1</h1>'
        )

    def testHashH2ClosedMismatch(self):
        self.assertMarkdownRenders(
            '## This is an H2 #',

            '<h2>This is an H2</h2>'
        )

    def testHashH3ClosedMismatch(self):
        self.assertMarkdownRenders(
            '### This is an H3 #',

            '<h3>This is an H3</h3>'
        )

    def testHashH4ClosedMismatch(self):
        self.assertMarkdownRenders(
            '#### This is an H4 #',

            '<h4>This is an H4</h4>'
        )

    def testHashH5ClosedMismatch(self):
        self.assertMarkdownRenders(
            '##### This is an H5 #',

            '<h5>This is an H5</h5>'
        )

    def testHashH6ClosedMismatch(self):
        self.assertMarkdownRenders(
            '###### This is an H6 #',

            '<h6>This is an H6</h6>'
        )

    def testHashGt6ClosedMismatch(self):
        self.assertMarkdownRenders(
            '####### This is an H6 ##################',

            '<h6># This is an H6</h6>'
        )

    def testHashH1FollowedByP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                # This is an H1
                Followed by a Paragraph with no blank line.
                """
            ),
            self.dedent(
                """
                <h1>This is an H1</h1>
                <p>Followed by a Paragraph with no blank line.</p>
                """
            )
        )

    def testHashH2FollowedByP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ## This is an H2
                Followed by a Paragraph with no blank line.
                """
            ),
            self.dedent(
                """
                <h2>This is an H2</h2>
                <p>Followed by a Paragraph with no blank line.</p>
                """
            )
        )

    def testHashH3FollowedByP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ### This is an H3
                Followed by a Paragraph with no blank line.
                """
            ),
            self.dedent(
                """
                <h3>This is an H3</h3>
                <p>Followed by a Paragraph with no blank line.</p>
                """
            )
        )

    def testHashH4FollowedByP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                #### This is an H4
                Followed by a Paragraph with no blank line.
                """
            ),
            self.dedent(
                """
                <h4>This is an H4</h4>
                <p>Followed by a Paragraph with no blank line.</p>
                """
            )
        )

    def testHashH5FollowedByP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ##### This is an H5
                Followed by a Paragraph with no blank line.
                """
            ),
            self.dedent(
                """
                <h5>This is an H5</h5>
                <p>Followed by a Paragraph with no blank line.</p>
                """
            )
        )

    def testHashH6FollowedByP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ###### This is an H6
                Followed by a Paragraph with no blank line.
                """
            ),
            self.dedent(
                """
                <h6>This is an H6</h6>
                <p>Followed by a Paragraph with no blank line.</p>
                """
            )
        )

    def testHashH1LeadingSpace(self):
        self.assertMarkdownRenders(
            ' # This is an H1',

            '<p># This is an H1</p>'
        )

    def testHashH2LeadingSpace(self):
        self.assertMarkdownRenders(
            ' ## This is an H2',

            '<p>## This is an H2</p>'
        )

    def testHashH3LeadingSpace(self):
        self.assertMarkdownRenders(
            ' ### This is an H3',

            '<p>### This is an H3</p>'
        )

    def testHashH4LeadingSpace(self):
        self.assertMarkdownRenders(
            ' #### This is an H4',

            '<p>#### This is an H4</p>'
        )

    def testHashH5LeadingSpace(self):
        self.assertMarkdownRenders(
            ' ##### This is an H5',

            '<p>##### This is an H5</p>'
        )

    def testHashH6LeadingSpace(self):
        self.assertMarkdownRenders(
            ' ###### This is an H6',

            '<p>###### This is an H6</p>'
        )

    def testHashH1OpenTrailingSpace(self):
        self.assertMarkdownRenders(
            '# This is an H1 ',

            '<h1>This is an H1</h1>'
        )

    def testHashH2OpenTrailingSpace(self):
        self.assertMarkdownRenders(
            '## This is an H2 ',

            '<h2>This is an H2</h2>'
        )

    def testHashH3OpenTrailingSpace(self):
        self.assertMarkdownRenders(
            '### This is an H3 ',

            '<h3>This is an H3</h3>'
        )

    def testHashH4OpenTrailingSpace(self):
        self.assertMarkdownRenders(
            '#### This is an H4 ',

            '<h4>This is an H4</h4>'
        )

    def testHashH5OpenTrailingSpace(self):
        self.assertMarkdownRenders(
            '##### This is an H5 ',

            '<h5>This is an H5</h5>'
        )

    def testHashH6OpenTrailingSpace(self):
        self.assertMarkdownRenders(
            '###### This is an H6 ',

            '<h6>This is an H6</h6>'
        )

    def testHashGt6OpenTrailingSpace(self):
        self.assertMarkdownRenders(
            '####### This is an H6 ',

            '<h6># This is an H6</h6>'
        )

    # TODO: Possibly change the following behavior. While this follows the behavior
    # of markdown.pl, it is rather uncommon and not necessarily intuitive.
    # See: https://johnmacfarlane.net/babelmark2/?normalize=1&text=%23+This+is+an+H1+%23+
    def testHashH1ClosedTrailingSpace(self):
        self.assertMarkdownRenders(
            '# This is an H1 # ',

            '<h1>This is an H1 #</h1>'
        )

    def testHashH2ClosedTrailingSpace(self):
        self.assertMarkdownRenders(
            '## This is an H2 ## ',

            '<h2>This is an H2 ##</h2>'
        )

    def testHashH3ClosedTrailingSpace(self):
        self.assertMarkdownRenders(
            '### This is an H3 ### ',

            '<h3>This is an H3 ###</h3>'
        )

    def testHashH4ClosedTrailingSpace(self):
        self.assertMarkdownRenders(
            '#### This is an H4 #### ',

            '<h4>This is an H4 ####</h4>'
        )

    def testHashH5ClosedTrailingSpace(self):
        self.assertMarkdownRenders(
            '##### This is an H5 ##### ',

            '<h5>This is an H5 #####</h5>'
        )

    def testHashH6ClosedTrailingSpace(self):
        self.assertMarkdownRenders(
            '###### This is an H6 ###### ',

            '<h6>This is an H6 ######</h6>'
        )

    def testHashGt6ClosedTrailingSpace(self):
        self.assertMarkdownRenders(
            '####### This is an H6 ####### ',

            '<h6># This is an H6 #######</h6>'
        )

    def testNoBlankLinesBetweenHashs(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                # This is an H1
                ## This is an H2
                """
            ),
            self.dedent(
                """
                <h1>This is an H1</h1>
                <h2>This is an H2</h2>
                """
            )
        )

    def testRandomHashLevels(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                ### H3
                ###### H6
                # H1
                ##### H5
                #### H4
                ## H2
                ### H3
                """
            ),
            self.dedent(
                """
                <h3>H3</h3>
                <h6>H6</h6>
                <h1>H1</h1>
                <h5>H5</h5>
                <h4>H4</h4>
                <h2>H2</h2>
                <h3>H3</h3>
                """
            )
        )

    def testHashFollowedByP(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                # This is an H1
                Followed by a Paragraph with no blank line.
                """
            ),
            self.dedent(
                """
                <h1>This is an H1</h1>
                <p>Followed by a Paragraph with no blank line.</p>
                """
            )
        )

    def testPFollowedByHash(self):
        self.assertMarkdownRenders(
            self.dedent(
                """
                This is a Paragraph.
                # Followed by an H1 with no blank line.
                """
            ),
            self.dedent(
                """
                <p>This is a Paragraph.</p>
                <h1>Followed by an H1 with no blank line.</h1>
                """
            )
        )

    def testEscapedHash(self):
        self.assertMarkdownRenders(
            "### H3 \\###",
            self.dedent(
                """
                <h3>H3 #</h3>
                """
            )
        )

    def testUnescapedHash(self):
        self.assertMarkdownRenders(
            "### H3 \\\\###",
            self.dedent(
                """
                <h3>H3 \\</h3>
                """
            )
        )
