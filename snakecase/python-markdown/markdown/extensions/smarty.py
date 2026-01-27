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
punct_class = r"""[!"#\$\%'()*+,-.\/:;<=>?\@\[\\\]\^_`{|}~]"""
end_of_word_class = r"[\s.,;:!?)]"
close_class = r"[^\ \t\r\n\[\{\(\-\u0002\u0003]"

opening_quotes_base = (
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
single_quote_start_re = r"^'(?=%s\B)" % punct_class
double_quote_start_re = r'^"(?=%s\B)' % punct_class

# Special case for double sets of quotes, e.g.:
#   <p>He said, "'Quoted' words in a larger quote."</p>
double_quote_sets_re = r""""'(?=\w)"""
single_quote_sets_re = r"""'"(?=\w)"""
double_quote_sets_re2 = r'(?<=%s)\'"' % close_class
single_quote_sets_re2 = r"(?<=%s)\"'" % close_class

# Special case for decade abbreviations (the '80s):
decade_abbr_re = r"(?<!\w)'(?=\d{2}s)"

# Get most opening double quotes:
opening_double_quotes_regex = r'%s"(?=\w)' % opening_quotes_base

# Double closing quotes:
closing_double_quotes_regex = r'"(?=\s)'
closing_double_quotes_regex2 = r'(?<=%s)"' % close_class

# Get most opening single quotes:
opening_single_quotes_regex = r"%s'(?=\w)" % opening_quotes_base

# Single closing quotes:
closing_single_quotes_regex = r"(?<=%s)'(?!\s|s\b|\d)" % close_class
closing_single_quotes_regex2 = r"'(\s|s\b)"

# All remaining quotes should be opening ones
remaining_single_quotes_regex = r"'"
remaining_double_quotes_regex = r'"'

HTML_STRICT_RE = HTML_RE + r'(?!\>)'


class SubstituteTextPattern(HtmlInlineProcessor):
    def __init__(self, pattern: str, replace: Sequence[int | str | etree.Element], md: Markdown):
        """ Replaces matches with some text. """
        HtmlInlineProcessor.__init__(self, pattern)
        self.replace = replace
        self.md = md

    def handle_match(self, m: re.Match[str], data: str) -> tuple[str, int, int]:
        result = ''
        for part in self.replace:
            if isinstance(part, int):
                result += m.group(part)
            else:
                result += self.md.html_stash.store(part)
        return result, m.start(0), m.end(0)


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
        self.substitutions.update(self.get_config('substitutions', default={}))

    def _addpatterns(
        self,
        md: Markdown,
        patterns: Sequence[tuple[str, Sequence[int | str | etree.Element]]],
        serie: str,
        priority: int,
    ):
        for ind, pattern in enumerate(patterns):
            pattern += (md,)
            pattern = SubstituteTextPattern(*pattern)
            name = 'smarty-%s-%d' % (serie, ind)
            self.inline_patterns.register(pattern, name, priority-ind)

    def educate_dashes(self, md: Markdown) -> None:
        em_dashes_pattern = SubstituteTextPattern(
            r'(?<!-)---(?!-)', (self.substitutions['mdash'],), md
        )
        en_dashes_pattern = SubstituteTextPattern(
            r'(?<!-)--(?!-)', (self.substitutions['ndash'],), md
        )
        self.inline_patterns.register(em_dashes_pattern, 'smarty-em-dashes', 50)
        self.inline_patterns.register(en_dashes_pattern, 'smarty-en-dashes', 45)

    def educate_ellipses(self, md: Markdown) -> None:
        ellipses_pattern = SubstituteTextPattern(
            r'(?<!\.)\.{3}(?!\.)', (self.substitutions['ellipsis'],), md
        )
        self.inline_patterns.register(ellipses_pattern, 'smarty-ellipses', 10)

    def educate_angled_quotes(self, md: Markdown) -> None:
        left_angled_quote_pattern = SubstituteTextPattern(
            r'\<\<', (self.substitutions['left-angle-quote'],), md
        )
        right_angled_quote_pattern = SubstituteTextPattern(
            r'\>\>', (self.substitutions['right-angle-quote'],), md
        )
        self.inline_patterns.register(left_angled_quote_pattern, 'smarty-left-angle-quotes', 40)
        self.inline_patterns.register(right_angled_quote_pattern, 'smarty-right-angle-quotes', 35)

    def educate_quotes(self, md: Markdown) -> None:
        lsquo = self.substitutions['left-single-quote']
        rsquo = self.substitutions['right-single-quote']
        ldquo = self.substitutions['left-double-quote']
        rdquo = self.substitutions['right-double-quote']
        patterns = (
            (single_quote_start_re, (rsquo,)),
            (double_quote_start_re, (rdquo,)),
            (double_quote_sets_re, (ldquo + lsquo,)),
            (single_quote_sets_re, (lsquo + ldquo,)),
            (double_quote_sets_re2, (rsquo + rdquo,)),
            (single_quote_sets_re2, (rdquo + rsquo,)),
            (decade_abbr_re, (rsquo,)),
            (opening_single_quotes_regex, (1, lsquo)),
            (closing_single_quotes_regex, (rsquo,)),
            (closing_single_quotes_regex2, (rsquo, 1)),
            (remaining_single_quotes_regex, (lsquo,)),
            (opening_double_quotes_regex, (1, ldquo)),
            (closing_double_quotes_regex, (rdquo,)),
            (closing_double_quotes_regex2, (rdquo,)),
            (remaining_double_quotes_regex, (ldquo,))
        )
        self._addpatterns(md, patterns, 'quotes', 30)

    def extend_markdown(self, md):
        configs = self.get_configs()
        self.inline_patterns: Registry[inlinepatterns.InlineProcessor] = Registry()
        if configs['smart_ellipses']:
            self.educate_ellipses(md)
        if configs['smart_quotes']:
            self.educate_quotes(md)
        if configs['smart_angled_quotes']:
            self.educate_angled_quotes(md)
            # Override `HTML_RE` from `inlinepatterns.py` so that it does not
            # process tags with duplicate closing quotes.
            md.inline_patterns.register(HtmlInlineProcessor(HTML_STRICT_RE, md), 'html', 90)
        if configs['smart_dashes']:
            self.educate_dashes(md)
        inline_processor = InlineProcessor(md)
        inline_processor.inline_patterns = self.inline_patterns
        md.treeprocessors.register(inline_processor, 'smarty', 6)
        md.ESCAPED_CHARS.extend(['"', "'"])


def make_extension(**kwargs):  # pragma: no cover
    return SmartyExtension(**kwargs)
