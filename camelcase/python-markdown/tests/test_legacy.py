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

from markdown.test_tools import LegacyTestCase, Kwargs
import os
import warnings

# Warnings should cause tests to fail...
warnings.simplefilter('error')
# Except for the warnings that shouldn't
warnings.filterwarnings('default', category=PendingDeprecationWarning)
warnings.filterwarnings('default', category=DeprecationWarning, module='markdown')

parentTestDir = os.path.abspath(os.path.dirname(__file__))


class TestBasic(LegacyTestCase):
    location = os.path.join(parentTestDir, 'basic')


class TestMisc(LegacyTestCase):
    location = os.path.join(parentTestDir, 'misc')


class TestPhp(LegacyTestCase):
    """
    Notes on "excluded" tests:

    Quotes in attributes: attributes get output in different order

    Inline HTML (Span): Backtick in raw HTML attribute TODO: fix me

    Backslash escapes: Weird whitespace issue in output

    `Ins` & `del`: Our behavior follows `markdown.pl`. I think PHP is wrong here

    Auto Links: TODO: fix raw HTML so is doesn't match <hr@example.com> as a `<hr>`.

    Empty List Item: We match `markdown.pl` here. Maybe someday we'll support this

    Headers: TODO: fix headers to not require blank line before

    Mixed `OL`s and `UL`s: We match `markdown.pl` here. I think PHP is wrong here

    Emphasis: We have various minor differences in combined & incorrect em markup.
    Maybe fix a few of them - but most aren't too important

    Code block in a list item: We match `markdown.pl` - not sure how PHP gets that output??

    PHP-Specific Bugs: Not sure what to make of the escaping stuff here.
    Why is PHP not removing a backslash?
    """
    location = os.path.join(parentTestDir, 'php')
    normalize = True
    inputExt = '.text'
    outputExt = '.xhtml'
    exclude = [
        'Quotes_in_attributes',
        'Inline_HTML_(Span)',
        'Backslash_escapes',
        'Ins_&_del',
        'Auto_Links',
        'Empty_List_Item',
        'Headers',
        'Mixed_OLs_and_ULs',
        'Emphasis',
        'Code_block_in_a_list_item',
        'PHP_Specific_Bugs'
    ]


class TestPl2004(LegacyTestCase):
    location = os.path.join(parentTestDir, 'pl/Tests_2004')
    normalize = True
    inputExt = '.text'
    exclude = ['Yuri_Footnotes', 'Yuri_Attributes']


class TestPl2007(LegacyTestCase):
    """
    Notes on "excluded" tests:

    Images: the attributes don't get ordered the same so we skip this

    Code Blocks: some weird whitespace issue

    Links, reference style: weird issue with nested brackets TODO: fix me

    Backslash escapes: backticks in raw html attributes TODO: fix me

    Code Spans: more backticks in raw html attributes TODO: fix me
    """
    location = os.path.join(parentTestDir, 'pl/Tests_2007')
    normalize = True
    inputExt = '.text'
    exclude = [
        'Images',
        'Code_Blocks',
        'Links,_reference_style',
        'Backslash_escapes',
        'Code_Spans'
    ]


class TestExtensions(LegacyTestCase):
    location = os.path.join(parentTestDir, 'extensions')
    exclude = ['codehilite']

    attrList = Kwargs(extensions=['attr_list', 'def_list', 'smarty'])

    codehilite = Kwargs(extensions=['codehilite'])

    toc = Kwargs(extensions=['toc'])

    tocInvalid = Kwargs(extensions=['toc'])

    tocOutOfOrder = Kwargs(extensions=['toc'])

    tocNested = Kwargs(
        extensions=['toc'],
        extensionConfigs={'toc': {'permalink': True}}
    )

    tocNested2 = Kwargs(
        extensions=['toc'],
        extensionConfigs={'toc': {'permalink': "[link]"}}
    )

    tocNestedList = Kwargs(extensions=['toc'])

    wikilinks = Kwargs(extensions=['wikilinks'])

    githubFlavored = Kwargs(extensions=['fenced_code'])

    saneLists = Kwargs(extensions=['sane_lists'])

    nl2brWAttrList = Kwargs(extensions=['nl2br', 'attr_list'])

    admonition = Kwargs(extensions=['admonition'])


class TestExtensionsExtra(LegacyTestCase):
    location = os.path.join(parentTestDir, 'extensions/extra')
    defaultKwargs = Kwargs(extensions=['extra'])

    looseDefList = Kwargs(extensions=['def_list'])

    simpleDefLists = Kwargs(extensions=['def_list'])

    abbr = Kwargs(extensions=['abbr'])

    footnotes = Kwargs(extensions=['footnotes'])

    extraConfig = Kwargs(
        extensions=['extra'],
        extensionConfigs={
            'extra': {
                'footnotes': {
                    'PLACE_MARKER': '~~~placemarker~~~'
                }
            }
        }
    )
