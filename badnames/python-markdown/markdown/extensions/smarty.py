# Smarty extension for Python-Markdown
# ====================================

# Adds conversion of ASCII dashes, quotes and ellipses to their HTML
# entity equivalents.

# See https://Python-Markdown.github.io/extensions/smarty
# for documentation.

# Author: 2013, Dmitry Shachnev <mitya57@gmail.com>

# All changes Copyright 2013-2014 The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)

# SmartyPants license:

#    Copyright (c) 2003 John Gruber <https://daringfireball.net/>
#    All rights reserved.

#    Redistribution and use in source and binary forms, with or without
#    modification, are permitted provided that the following conditions are
#    met:

#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.

#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.

#    *  Neither the name "SmartyPants" nor the names of its contributors
#       may be used to endorse or promote products derived from this
#       software without specific prior written permission.

#    This software is provided by the copyright holders and contributors "as
#    is" and any express or implied warranties, including, but not limited
#    to, the implied warranties of merchantability and fitness for a
#    particular purpose are disclaimed. In no event shall the copyright
#    owner or contributors be liable for any direct, indirect, incidental,
#    special, exemplary, or consequential damages (including, but not
#    limited to, procurement of substitute goods or services; loss of use,
#    data, or profits; or business interruption) however caused and on any
#    theory of liability, whether in contract, strict liability, or tort
#    (including negligence or otherwise) arising in any way out of the use
#    of this software, even if advised of the possibility of such damage.


# `smartypants.py` license:

#    `smartypants.py` is a derivative work of SmartyPants.
#    Copyright (c) 2004, 2007 Chad Miller <http://web.chad.org/>

#    Redistribution and use in source and binary forms, with or without
#    modification, are permitted provided that the following conditions are
#    met:

#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.

#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.

#    This software is provided by the copyright holders and contributors "as
#    is" and any express or implied warranties, including, but not limited
#    to, the implied warranties of merchantability and fitness for a
#    particular purpose are disclaimed. In no event shall the copyright
#    owner or contributors be liable for any direct, indirect, incidental,
#    special, exemplary, or consequential damages (including, but not
#    limited to, procurement of substitute goods or services; loss of use,
#    data, or profits; or business interruption) however caused and on any
#    theory of liability, whether in contract, strict liability, or tort
#    (including negligence or otherwise) arising in any way out of the use
#    of this software, even if advised of the possibility of such damage.

"""
Convert ASCII dashes, quotes and ellipses to their HTML entity equivalents.

See the [documentation](https://Python-Markdown.github.io/extensions/smarty)
for details.
"""

from __future__ import annotations

from . import Extension
from ..inlinepatterns import HtmlInlineProcessor, HTML_RE
from ..treeprocessors import InlineProcessor
from ..util import Registry
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:  # pragma: no cover
    from markdown import Markdown
    from .. import inlinepatterns
    import re
    import xml.etree.ElementTree as etree

# Constants for quote education.
punctClass = r"""[!"#\$\%'()*+,-.\/:;<=>?\@\[\\\]\^_`{|}~]"""
endOfWordClass = r"[\s.,;:!?)]"
closeClass = r"[^\ \t\r\n\[\{\(\-\u0002\u0003]"

openingQuotesBase = (
    r'(\s'               # a  whitespace char
    r'|&nbsp;'           # or a non-breaking space entity
    r'|--'               # or dashes
    r'|–|—'              # or Unicode
    r'|&[mn]dash;'       # or named dash entities
    r'|&#8211;|&#8212;'  # or decimal entities
    r')'
)

substitutions = {
    'mdash': '&mdash;',
    'ndash': '&ndash;',
    'ellipsis': '&hellip;',
    'left-angle-quote': '&laquo;',
    'right-angle-quote': '&raquo;',
    'left-single-quote': '&lsquo;',
    'right-single-quote': '&rsquo;',
    'left-double-quote': '&ldquo;',
    'right-double-quote': '&rdquo;',
}


# Special case if the very first character is a quote
# followed by punctuation at a non-word-break. Close the quotes by brute force:
singleQuoteStartRe = r"^'(?=%s\B)" % punctClass
doubleQuoteStartRe = r'^"(?=%s\B)' % punctClass

# Special case for double sets of quotes, e.g.:
#   <p>He said, "'Quoted' words in a larger quote."</p>
doubleQuoteSetsRe = r""""'(?=\w)"""
singleQuoteSetsRe = r"""'"(?=\w)"""
doubleQuoteSetsRe2 = r'(?<=%s)\'"' % closeClass
singleQuoteSetsRe2 = r"(?<=%s)\"'" % closeClass

# Special case for decade abbreviations (the '80s):
decadeAbbrRe = r"(?<!\w)'(?=\d{2}s)"

# Get most opening double quotes:
openingDoubleQuotesRegex = r'%s"(?=\w)' % openingQuotesBase

# Double closing quotes:
closingDoubleQuotesRegex = r'"(?=\s)'
closingDoubleQuotesRegex2 = r'(?<=%s)"' % closeClass

# Get most opening single quotes:
openingSingleQuotesRegex = r"%s'(?=\w)" % openingQuotesBase

# Single closing quotes:
closingSingleQuotesRegex = r"(?<=%s)'(?!\s|s\b|\d)" % closeClass
closingSingleQuotesRegex2 = r"'(\s|s\b)"

# All remaining quotes should be opening ones
remainingSingleQuotesRegex = r"'"
remainingDoubleQuotesRegex = r'"'

HTML_STRICT_RE = HTML_RE + r'(?!\>)'


class SubstituteTextPattern(HtmlInlineProcessor):
    def __init__(self, pattern: str, replace: Sequence[int | str | etree.Element], md: Markdown):
        """ Replaces matches with some text. """
        HtmlInlineProcessor.__init__(self, pattern)
        self.replace = replace
        self.md = md

    def handleMatch(self, m: re.Match[str], data: str) -> tuple[str, int, int]:
        b = ''
        for a in self.replace:
            if isinstance(a, int):
                b += m.group(a)
            else:
                b += self.md.htmlStash.store(a)
        return b, m.start(0), m.end(0)


class SmartyExtension(Extension):
    """ Add Smarty to Markdown. """
    def __init__(self, **kwargs):
        self.config = {
            'smart_quotes': [True, 'Educate quotes'],
            'smart_angled_quotes': [False, 'Educate angled quotes'],
            'smart_dashes': [True, 'Educate dashes'],
            'smart_ellipses': [True, 'Educate ellipses'],
            'substitutions': [{}, 'Overwrite default substitutions'],
        }
        """ Default configuration options. """
        super().__init__(**kwargs)
        self.substitutions: dict[str, str] = dict(substitutions)
        self.substitutions.update(self.getConfig('substitutions', default={}))

    def _addPatterns(
        self,
        md: Markdown,
        patterns: Sequence[tuple[str, Sequence[int | str | etree.Element]]],
        serie: str,
        priority: int,
    ):
        for ind, b in enumerate(patterns):
            b += (md,)
            b = SubstituteTextPattern(*b)
            a = 'smarty-%s-%d' % (serie, ind)
            self.inlinePatterns.register(b, a, priority-ind)

    def educateDashes(self, md: Markdown) -> None:
        a = SubstituteTextPattern(
            r'(?<!-)---(?!-)', (self.substitutions['mdash'],), md
        )
        b = SubstituteTextPattern(
            r'(?<!-)--(?!-)', (self.substitutions['ndash'],), md
        )
        self.inlinePatterns.register(a, 'smarty-em-dashes', 50)
        self.inlinePatterns.register(b, 'smarty-en-dashes', 45)

    def educateEllipses(self, md: Markdown) -> None:
        a = SubstituteTextPattern(
            r'(?<!\.)\.{3}(?!\.)', (self.substitutions['ellipsis'],), md
        )
        self.inlinePatterns.register(a, 'smarty-ellipses', 10)

    def educateAngledQuotes(self, md: Markdown) -> None:
        a = SubstituteTextPattern(
            r'\<\<', (self.substitutions['left-angle-quote'],), md
        )
        b = SubstituteTextPattern(
            r'\>\>', (self.substitutions['right-angle-quote'],), md
        )
        self.inlinePatterns.register(a, 'smarty-left-angle-quotes', 40)
        self.inlinePatterns.register(b, 'smarty-right-angle-quotes', 35)

    def educateQuotes(self, md: Markdown) -> None:
        b = self.substitutions['left-single-quote']
        e = self.substitutions['right-single-quote']
        a = self.substitutions['left-double-quote']
        d = self.substitutions['right-double-quote']
        c = (
            (singleQuoteStartRe, (e,)),
            (doubleQuoteStartRe, (d,)),
            (doubleQuoteSetsRe, (a + b,)),
            (singleQuoteSetsRe, (b + a,)),
            (doubleQuoteSetsRe2, (e + d,)),
            (singleQuoteSetsRe2, (d + e,)),
            (decadeAbbrRe, (e,)),
            (openingSingleQuotesRegex, (1, b)),
            (closingSingleQuotesRegex, (e,)),
            (closingSingleQuotesRegex2, (e, 1)),
            (remainingSingleQuotesRegex, (b,)),
            (openingDoubleQuotesRegex, (1, a)),
            (closingDoubleQuotesRegex, (d,)),
            (closingDoubleQuotesRegex2, (d,)),
            (remainingDoubleQuotesRegex, (a,))
        )
        self._addPatterns(md, c, 'quotes', 30)

    def extendMarkdown(self, md):
        a = self.getConfigs()
        self.inlinePatterns: Registry[inlinepatterns.InlineProcessor] = Registry()
        if a['smart_ellipses']:
            self.educateEllipses(md)
        if a['smart_quotes']:
            self.educateQuotes(md)
        if a['smart_angled_quotes']:
            self.educateAngledQuotes(md)
            # Override `HTML_RE` from `inlinepatterns.py` so that it does not
            # process tags with duplicate closing quotes.
            md.inlinePatterns.register(HtmlInlineProcessor(HTML_STRICT_RE, md), 'html', 90)
        if a['smart_dashes']:
            self.educateDashes(md)
        b = InlineProcessor(md)
        b.inlinePatterns = self.inlinePatterns
        md.treeprocessors.register(b, 'smarty', 6)
        md.ESCAPED_CHARS.extend(['"', "'"])


def makeExtension(**kwargs):  # pragma: no cover
    return SmartyExtension(**kwargs)
