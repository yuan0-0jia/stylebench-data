# Meta Data Extension for Python-Markdown
# =======================================

# This extension adds Meta Data handling to markdown.

# See https://Python-Markdown.github.io/extensions/meta_data
# for documentation.

# Original code Copyright 2007-2008 [Waylan Limberg](https://github.com/waylan).

# All changes Copyright 2008-2014 The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""
This extension adds Meta Data handling to markdown.

See the [documentation](https://Python-Markdown.github.io/extensions/meta_data)
for details.
"""

from __future__ import annotations

from . import Extension
from ..preprocessors import Preprocessor
import re
import logging
from typing import Any

log = logging.getLogger('MARKDOWN')

# Global Vars
META_RE = re.compile(r'^[ ]{0,3}(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)')
META_MORE_RE = re.compile(r'^[ ]{4,}(?P<value>.*)')
BEGIN_RE = re.compile(r'^-{3}(\s.*)?')
END_RE = re.compile(r'^(-{3}|\.{3})(\s.*)?')


class MetaExtension (Extension):
    """ Meta-Data extension for Python-Markdown. """

    def extendMarkdown(self, md):
        """ Add `MetaPreprocessor` to Markdown instance. """
        md.registerExtension(self)
        self.md = md
        md.preprocessors.register(MetaPreprocessor(md), 'meta', 27)

    def reset(self) -> None:
        self.md.Meta = {}


class MetaPreprocessor(Preprocessor):
    """ Get Meta-Data. """

    def run(self, lines: list[str]) -> list[str]:
        """ Parse Meta-Data and store in Markdown.Meta. """
        e: dict[str, Any] = {}
        a = None
        if lines and BEGIN_RE.match(lines[0]):
            lines.pop(0)
        while lines:
            b = lines.pop(0)
            c = META_RE.match(b)
            if b.strip() == '' or END_RE.match(b):
                break  # blank line or end of YAML header - done
            if c:
                a = c.group('key').lower().strip()
                f = c.group('value').strip()
                try:
                    e[a].append(f)
                except KeyError:
                    e[a] = [f]
            else:
                d = META_MORE_RE.match(b)
                if d and a:
                    # Add another line to existing key
                    e[a].append(d.group('value').strip())
                else:
                    lines.insert(0, b)
                    break  # no meta data - done
        self.md.Meta = e
        return lines


def makeExtension(**kwargs):  # pragma: no cover
    return MetaExtension(**kwargs)
