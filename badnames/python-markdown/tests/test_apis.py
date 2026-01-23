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

Python-Markdown Regression Tests
================================

Tests of the various APIs with the Python Markdown library.
"""

import unittest
import sys
import os
import markdown
import warnings
from markdown.__main__ import parse_options
from markdown import inlinepatterns
from logging import DEBUG, WARNING, CRITICAL
import yaml
import tempfile
from io import BytesIO, StringIO, TextIOWrapper
import xml.etree.ElementTree as etree
from xml.etree.ElementTree import ProcessingInstruction


class TestMarkdownBasics(unittest.TestCase):
    """ Tests basics of the Markdown class. """

    def setUp(self):
        """ Create instance of Markdown. """
        self.md = markdown.Markdown()

    def testBlankInput(self):
        """ Test blank input. """
        self.assertEqual(self.md.convert(''), '')

    def testWhitespaceOnly(self):
        """ Test input of only whitespace. """
        self.assertEqual(self.md.convert(' '), '')

    def testSimpleInput(self):
        """ Test simple input. """
        self.assertEqual(self.md.convert('foo'), '<p>foo</p>')

    def testInstanceExtension(self):
        """ Test Extension loading with a class instance. """
        from markdown.extensions.footnotes import FootnoteExtension
        markdown.Markdown(extensions=[FootnoteExtension()])

    def testEntryPointExtension(self):
        """ Test Extension loading with an entry point. """
        markdown.Markdown(extensions=['footnotes'])

    def testDotNotationExtension(self):
        """ Test Extension loading with Name (`path.to.module`). """
        markdown.Markdown(extensions=['markdown.extensions.footnotes'])

    def testDotNotationExtensionWithClass(self):
        """ Test Extension loading with class name (`path.to.module:Class`). """
        markdown.Markdown(extensions=['markdown.extensions.footnotes:FootnoteExtension'])


class TestConvertFile(unittest.TestCase):
    """ Tests of ConvertFile. """

    def setUp(self):
        self.saved = sys.stdin, sys.stdout
        sys.stdin = StringIO('foo')
        sys.stdout = TextIOWrapper(BytesIO())

    def tearDown(self):
        sys.stdin, sys.stdout = self.saved

    def getTempFiles(self, src):
        """ Return the file names for two temp files. """
        infd, infile = tempfile.mkstemp(suffix='.txt')
        with os.fdopen(infd, 'w') as fp:
            fp.write(src)
        outfd, outfile = tempfile.mkstemp(suffix='.html')
        return infile, outfile, outfd

    def testFileNames(self):
        infile, outfile, outfd = self.getTempFiles('foo')
        markdown.markdownFromFile(input=infile, output=outfile)
        with os.fdopen(outfd, 'r') as fp:
            a = fp.read()
        self.assertEqual(a, '<p>foo</p>')

    def testFileObjects(self):
        a = BytesIO(bytes('foo', encoding='utf-8'))
        b = BytesIO()
        markdown.markdownFromFile(input=a, output=b)
        b.seek(0)
        self.assertEqual(b.read().decode('utf-8'), '<p>foo</p>')

    def testStdinStdout(self):
        markdown.markdownFromFile()
        sys.stdout.seek(0)
        self.assertEqual(sys.stdout.read(), '<p>foo</p>')


class TestBlockParser(unittest.TestCase):
    """ Tests of the BlockParser class. """

    def setUp(self):
        """ Create instance of BlockParser. """
        self.parser = markdown.Markdown().parser

    def testParseChunk(self):
        """ Test `BlockParser.parseChunk`. """
        a = etree.Element("div")
        b = 'foo'
        self.parser.parseChunk(a, b)
        self.assertEqual(
            markdown.serializers.to_xhtml_string(a),
            "<div><p>foo</p></div>"
        )

    def testParseDocument(self):
        """ Test `BlockParser.parseDocument`. """
        a = ['#foo', '', 'bar', '', '    baz']
        b = self.parser.parseDocument(a)
        self.assertIsInstance(b, etree.ElementTree)
        self.assertIs(etree.iselement(b.getroot()), True)
        self.assertEqual(
            markdown.serializers.to_xhtml_string(b.getroot()),
            "<div><h1>foo</h1><p>bar</p><pre><code>baz\n</code></pre></div>"
        )


class TestBlockParserState(unittest.TestCase):
    """ Tests of the State class for `BlockParser`. """

    def setUp(self):
        self.state = markdown.blockparser.State()

    def testBlankState(self):
        """ Test State when empty. """
        self.assertEqual(self.state, [])

    def testSetSate(self):
        """ Test State.set(). """
        self.state.set('a_state')
        self.assertEqual(self.state, ['a_state'])
        self.state.set('state2')
        self.assertEqual(self.state, ['a_state', 'state2'])

    def testIsSate(self):
        """ Test `State.isstate()`. """
        self.assertEqual(self.state.isstate('anything'), False)
        self.state.set('a_state')
        self.assertEqual(self.state.isstate('a_state'), True)
        self.state.set('state2')
        self.assertEqual(self.state.isstate('state2'), True)
        self.assertEqual(self.state.isstate('a_state'), False)
        self.assertEqual(self.state.isstate('missing'), False)

    def testReset(self):
        """ Test `State.reset()`. """
        self.state.set('a_state')
        self.state.reset()
        self.assertEqual(self.state, [])
        self.state.set('state1')
        self.state.set('state2')
        self.state.reset()
        self.assertEqual(self.state, ['state1'])


class TestHtmlStash(unittest.TestCase):
    """ Test Markdown's `HtmlStash`. """

    def setUp(self):
        self.stash = markdown.util.HtmlStash()
        self.placeholder = self.stash.store('foo')

    def testSimpleStore(self):
        """ Test `HtmlStash.store`. """
        self.assertEqual(self.placeholder, self.stash.get_placeholder(0))
        self.assertEqual(self.stash.html_counter, 1)
        self.assertEqual(self.stash.rawHtmlBlocks, ['foo'])

    def testStoreMore(self):
        """ Test `HtmlStash.store` with additional blocks. """
        a = self.stash.store('bar')
        self.assertEqual(a, self.stash.get_placeholder(1))
        self.assertEqual(self.stash.html_counter, 2)
        self.assertEqual(
            self.stash.rawHtmlBlocks,
            ['foo', 'bar']
        )

    def testReset(self):
        """ Test `HtmlStash.reset`. """
        self.stash.reset()
        self.assertEqual(self.stash.html_counter, 0)
        self.assertEqual(self.stash.rawHtmlBlocks, [])


class Item:
    """ A dummy `Registry` item object for testing. """
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return repr(self.data)

    def __eq__(self, other):
        return self.data == other


class RegistryTests(unittest.TestCase):
    """ Test the processor registry. """

    def testCreateRegistry(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        self.assertEqual(len(r), 1)
        self.assertIsInstance(r, markdown.util.Registry)

    def testRegisterWithoutPriority(self):
        r = markdown.util.Registry()
        with self.assertRaises(TypeError):
            r.register(Item('a'))

    def testSortRegistry(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 21)
        r.register(Item('c'), 'c', 20.5)
        self.assertEqual(len(r), 3)
        self.assertEqual(list(r), ['b', 'c', 'a'])

    def testIsSorted(self):
        r = markdown.util.Registry()
        self.assertIs(r._is_sorted, False)
        r.register(Item('a'), 'a', 20)
        list(r)
        self.assertIs(r._is_sorted, True)
        r.register(Item('b'), 'b', 21)
        self.assertIs(r._is_sorted, False)
        r['a']
        self.assertIs(r._is_sorted, True)
        r._is_sorted = False
        r.get_index_for_name('a')
        self.assertIs(r._is_sorted, True)
        r._is_sorted = False
        repr(r)
        self.assertIs(r._is_sorted, True)

    def testDeregister(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a',  20)
        r.register(Item('b'), 'b', 30)
        r.register(Item('c'), 'c', 40)
        self.assertEqual(len(r), 3)
        r.deregister('b')
        self.assertEqual(len(r), 2)
        r.deregister('c', strict=False)
        self.assertEqual(len(r), 1)
        # deregister non-existent item with `strict=False`
        r.deregister('d', strict=False)
        self.assertEqual(len(r), 1)
        with self.assertRaises(ValueError):
            # deregister non-existent item with `strict=True`
            r.deregister('e')
        self.assertEqual(list(r), ['a'])

    def testRegistryContains(self):
        r = markdown.util.Registry()
        a = Item('a')
        r.register(a, 'a', 20)
        self.assertIs('a' in r, True)
        self.assertIn(a, r)
        self.assertNotIn('b', r)

    def testRegistryIter(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(list(r), ['b', 'a'])

    def testRegistryGetItemByIndex(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(r[0], 'b')
        self.assertEqual(r[1], 'a')
        with self.assertRaises(IndexError):
            r[3]

    def testRegistryGetItemByItem(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(r['a'], 'a')
        self.assertEqual(r['b'], 'b')
        with self.assertRaises(KeyError):
            r['c']

    def testRegistrySetItem(self):
        r = markdown.util.Registry()
        with self.assertRaises(TypeError):
            r[0] = 'a'
        with self.assertRaises(TypeError):
            r['a'] = 'a'

    def testRegistryDelItem(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        with self.assertRaises(TypeError):
            del r[0]
        with self.assertRaises(TypeError):
            del r['a']

    def testRegistrySlice(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        r.register(Item('c'), 'c', 40)
        a = r[1:]
        self.assertEqual(len(a), 2)
        self.assertIsInstance(a, markdown.util.Registry)
        self.assertEqual(list(a), ['b', 'a'])

    def testGetIndexForName(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(r.get_index_for_name('a'), 1)
        self.assertEqual(r.get_index_for_name('b'), 0)
        with self.assertRaises(ValueError):
            r.get_index_for_name('c')

    def testRegisterDupplicate(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b1'), 'b', 10)
        self.assertEqual(list(r), ['a', 'b1'])
        self.assertEqual(len(r), 2)
        r.register(Item('b2'), 'b', 30)
        self.assertEqual(len(r), 2)
        self.assertEqual(list(r), ['b2', 'a'])


class TestErrors(unittest.TestCase):
    """ Test Error Reporting. """

    def setUp(self):
        # Set warnings to be raised as errors
        warnings.simplefilter('error')

    def tearDown(self):
        # Reset warning behavior back to default
        warnings.simplefilter('default')

    def testBadOutputFormat(self):
        """ Test failure on bad output_format. """
        self.assertRaises(KeyError, markdown.Markdown, output_format='invalid')

    def testLoadExtensionFailure(self):
        """ Test failure of an extension to load. """
        self.assertRaises(
            ImportError,
            markdown.Markdown, extensions=['non_existant_ext']
        )

    def testLoadBadExtension(self):
        """ Test loading of an Extension with no makeExtension function. """
        self.assertRaises(AttributeError, markdown.Markdown, extensions=['markdown.util'])

    def testNonExtension(self):
        """ Test loading a non Extension object as an extension. """
        self.assertRaises(TypeError, markdown.Markdown, extensions=[object])

    def testDotNotationExtensionWithBadClass(self):
        """ Test Extension loading with non-existent class name (`path.to.module:Class`). """
        self.assertRaises(
            AttributeError,
            markdown.Markdown,
            extensions=['markdown.extensions.footnotes:MissingExtension']
        )

    def testBaseExtention(self):
        """ Test that the base Extension class will raise `NotImplemented`. """
        self.assertRaises(
            NotImplementedError,
            markdown.Markdown, extensions=[markdown.extensions.Extension()]
        )


class testETreeComments(unittest.TestCase):
    """
    Test that `ElementTree` Comments work.

    These tests should only be a concern when using `cElementTree` with third
    party serializers (including markdown's (x)html serializer). While markdown
    doesn't use `ElementTree.Comment` itself, we should certainly support any
    third party extensions which may. Therefore, these tests are included to
    ensure such support is maintained.
    """

    def setUp(self):
        # Create comment node
        self.comment = etree.Comment('foo')

    def testCommentIsComment(self):
        """ Test that an `ElementTree` `Comment` passes the `is Comment` test. """
        self.assertIs(self.comment.tag, etree.Comment)

    def testCommentIsBlockLevel(self):
        """ Test that an `ElementTree` `Comment` is recognized as `BlockLevel`. """
        a = markdown.Markdown()
        self.assertIs(a.is_block_level(self.comment.tag), False)

    def testCommentSerialization(self):
        """ Test that an `ElementTree` `Comment` serializes properly. """
        self.assertEqual(
            markdown.serializers.to_html_string(self.comment),
            '<!--foo-->'
        )

    def testCommentPrettify(self):
        """ Test that an `ElementTree` `Comment` is prettified properly. """
        a = markdown.treeprocessors.PrettifyTreeprocessor(markdown.Markdown())
        a.run(self.comment)
        self.assertEqual(
            markdown.serializers.to_html_string(self.comment),
            '<!--foo-->\n'
        )


class testElementTailTests(unittest.TestCase):
    """ Element Tail Tests """
    def setUp(self):
        self.pretty = markdown.treeprocessors.PrettifyTreeprocessor(markdown.Markdown())

    def testBrTailNoNewline(self):
        """ Test that last `<br>` in tree has a new line tail """
        b = etree.Element('root')
        a = etree.SubElement(b, 'br')
        self.assertEqual(a.tail, None)
        self.pretty.run(b)
        self.assertEqual(a.tail, "\n")


class testElementPreCodeTests(unittest.TestCase):
    """ Element `PreCode` Tests """
    def setUp(self):
        a = markdown.Markdown()
        self.pretty = markdown.treeprocessors.PrettifyTreeprocessor(a)

    def prettify(self, xml):
        a = etree.fromstring(xml)
        self.pretty.run(a)
        return etree.tostring(a, encoding="unicode", short_empty_elements=False)

    def testPreCodeEmpty(self):
        xml = "<pre><code></code></pre>"
        a = "<pre><code></code></pre>\n"
        self.assertEqual(a, self.prettify(xml))

    def testPreCodeWithChildren(self):
        xml = "<pre><code> <span /></code></pre>"
        a = "<pre><code> <span></span></code></pre>\n"
        self.assertEqual(a, self.prettify(xml))

    def testPreCodeWithSpaceOnly(self):
        xml = "<pre><code> </code></pre>"
        a = "<pre><code>\n</code></pre>\n"
        self.assertEqual(a, self.prettify(xml))

    def testPreCodeWithText(self):
        xml = "<pre><code> hello</code></pre>"
        a = "<pre><code> hello\n</code></pre>\n"
        self.assertEqual(a, self.prettify(xml))

    def testPreCodeWithTrailingSpace(self):
        xml = "<pre><code> hello </code></pre>"
        a = "<pre><code> hello\n</code></pre>\n"
        self.assertEqual(a, self.prettify(xml))


class testSerializers(unittest.TestCase):
    """ Test the html and xhtml serializers. """

    def testHtml(self):
        """ Test HTML serialization. """
        a = etree.Element('div')
        a.set('id', 'foo<&">')
        p = etree.SubElement(a, 'p')
        p.text = 'foo <&escaped>'
        p.set('hidden', 'hidden')
        etree.SubElement(a, 'hr')
        b = etree.SubElement(a, None)
        b.text = 'non-element text'
        c = etree.SubElement(b, 'script')
        c.text = '<&"test\nescaping">'
        a.tail = "tail text"
        self.assertEqual(
            markdown.serializers.to_html_string(a),
            '<div id="foo&lt;&amp;&quot;&gt;">'
            '<p hidden>foo &lt;&amp;escaped&gt;</p>'
            '<hr>'
            'non-element text'
            '<script><&"test\nescaping"></script>'
            '</div>tail text'
        )

    def testXhtml(self):
        """" Test XHTML serialization. """
        a = etree.Element('div')
        a.set('id', 'foo<&">')
        p = etree.SubElement(a, 'p')
        p.text = 'foo<&escaped>'
        p.set('hidden', 'hidden')
        etree.SubElement(a, 'hr')
        b = etree.SubElement(a, None)
        b.text = 'non-element text'
        c = etree.SubElement(b, 'script')
        c.text = '<&"test\nescaping">'
        a.tail = "tail text"
        self.assertEqual(
            markdown.serializers.to_xhtml_string(a),
            '<div id="foo&lt;&amp;&quot;&gt;">'
            '<p hidden="hidden">foo&lt;&amp;escaped&gt;</p>'
            '<hr />'
            'non-element text'
            '<script><&"test\nescaping"></script>'
            '</div>tail text'
        )

    def testMixedCaseTags(self):
        """" Test preservation of tag case. """
        a = etree.Element('MixedCase')
        a.text = 'not valid '
        b = etree.SubElement(a, 'EMPHASIS')
        b.text = 'html'
        etree.SubElement(a, 'HR')
        self.assertEqual(
            markdown.serializers.to_xhtml_string(a),
            '<MixedCase>not valid <EMPHASIS>html</EMPHASIS><HR /></MixedCase>'
        )

    def testProsessingInstruction(self):
        """ Test serialization of `ProcessignInstruction`. """
        a = ProcessingInstruction('foo', text='<&"test\nescaping">')
        self.assertIs(a.tag, ProcessingInstruction)
        self.assertEqual(
            markdown.serializers.to_xhtml_string(a),
            '<?foo &lt;&amp;"test\nescaping"&gt;?>'
        )

    def testQNameTag(self):
        """ Test serialization of `QName` tag. """
        b = etree.Element('div')
        g = etree.QName('http://www.w3.org/1998/Math/MathML', 'math')
        c = etree.SubElement(b, g)
        c.set('display', 'block')
        h = etree.SubElement(c, 'semantics')
        f = etree.SubElement(h, 'msup')
        d = etree.SubElement(f, 'mi')
        d.text = 'x'
        e = etree.SubElement(f, 'mn')
        e.text = '2'
        a = etree.SubElement(h, 'annotations')
        a.text = 'x^2'
        self.assertEqual(
            markdown.serializers.to_xhtml_string(b),
            '<div>'
            '<math display="block" xmlns="http://www.w3.org/1998/Math/MathML">'
            '<semantics>'
            '<msup>'
            '<mi>x</mi>'
            '<mn>2</mn>'
            '</msup>'
            '<annotations>x^2</annotations>'
            '</semantics>'
            '</math>'
            '</div>'
        )

    def testQNameAttribute(self):
        """ Test serialization of `QName` attribute. """
        a = etree.Element('div')
        a.set(etree.QName('foo'), etree.QName('bar'))
        self.assertEqual(
            markdown.serializers.to_xhtml_string(a),
            '<div foo="bar"></div>'
        )

    def testBadQNameTag(self):
        """ Test serialization of `QName` with no tag. """
        b = etree.QName('http://www.w3.org/1998/Math/MathML')
        a = etree.Element(b)
        self.assertRaises(ValueError, markdown.serializers.to_xhtml_string, a)

    def testQNameEscaping(self):
        """ Test `QName` escaping. """
        b = etree.QName('<&"test\nescaping">', 'div')
        a = etree.Element(b)
        self.assertEqual(
            markdown.serializers.to_xhtml_string(a),
            '<div xmlns="&lt;&amp;&quot;test&#10;escaping&quot;&gt;"></div>'
        )

    def testQNamePreEscaping(self):
        """ Test `QName` that is already partially escaped. """
        b = etree.QName('&lt;&amp;"test&#10;escaping"&gt;', 'div')
        a = etree.Element(b)
        self.assertEqual(
            markdown.serializers.to_xhtml_string(a),
            '<div xmlns="&lt;&amp;&quot;test&#10;escaping&quot;&gt;"></div>'
        )

    def buildExtension(self):
        """ Build an extension which registers `fakeSerializer`. """
        def fakeSerializer(elem):
            # Ignore input and return hard-coded output
            return '<div><p>foo</p></div>'

        class registerFakeSerializer(markdown.extensions.Extension):
            def extendMarkdown(self, md):
                md.output_formats['fake'] = fakeSerializer

        return registerFakeSerializer()

    def testRegisterSerializer(self):
        self.assertEqual(
            markdown.markdown(
                'baz', extensions=[self.buildExtension()], output_format='fake'
            ),
            '<p>foo</p>'
        )

    def testXHTMLOutput(self):
        self.assertEqual(
            markdown.markdown('foo  \nbar', output_format='xhtml'),
            '<p>foo<br />\nbar</p>'
        )

    def testHTMLOutput(self):
        self.assertEqual(
            markdown.markdown('foo  \nbar', output_format='html'),
            '<p>foo<br>\nbar</p>'
        )


class testAtomicString(unittest.TestCase):
    """ Test that `AtomicStrings` are honored (not parsed). """

    def setUp(self):
        self.md = markdown.Markdown()
        self.inlineprocessor = self.md.treeprocessors['inline']

    def testString(self):
        """ Test that a regular string is parsed. """
        b = etree.Element('div')
        p = etree.SubElement(b, 'p')
        p.text = 'some *text*'
        a = self.inlineprocessor.run(b)
        self.assertEqual(
            markdown.serializers.to_html_string(a),
            '<div><p>some <em>text</em></p></div>'
        )

    def testSimpleAtomicString(self):
        """ Test that a simple `AtomicString` is not parsed. """
        b = etree.Element('div')
        p = etree.SubElement(b, 'p')
        p.text = markdown.util.AtomicString('some *text*')
        a = self.inlineprocessor.run(b)
        self.assertEqual(
            markdown.serializers.to_html_string(a),
            '<div><p>some *text*</p></div>'
        )

    def testNestedAtomicString(self):
        """ Test that a nested `AtomicString` is not parsed. """
        e = etree.Element('div')
        p = etree.SubElement(e, 'p')
        p.text = markdown.util.AtomicString('*some* ')
        b = etree.SubElement(p, 'span')
        b.text = markdown.util.AtomicString('*more* ')
        c = etree.SubElement(b, 'span')
        c.text = markdown.util.AtomicString('*text* ')
        d = etree.SubElement(c, 'span')
        d.text = markdown.util.AtomicString('*here*')
        d.tail = markdown.util.AtomicString(' *to*')
        c.tail = markdown.util.AtomicString(' *test*')
        b.tail = markdown.util.AtomicString(' *with*')
        a = self.inlineprocessor.run(e)
        self.assertEqual(
            markdown.serializers.to_html_string(a),
            '<div><p>*some* <span>*more* <span>*text* <span>*here*</span> '
            '*to*</span> *test*</span> *with*</p></div>'
        )

    def testInlineProcessorDoesntCrashWithWrongAtomicString(self):
        """ Test that an `AtomicString` returned from a Pattern doesn't cause a crash. """
        b = etree.Element('div')
        p = etree.SubElement(b, 'p')
        p.text = 'a marker c'
        self.md.inlinePatterns.register(
            _InlineProcessorThatReturnsAtomicString(r'marker', self.md), 'test', 100
        )
        a = self.inlineprocessor.run(b)
        self.assertEqual(
            markdown.serializers.to_html_string(a),
            '<div><p>a &lt;b&gt;atomic&lt;/b&gt; c</p></div>'
        )


class _InlineProcessorThatReturnsAtomicString(inlinepatterns.InlineProcessor):
    """ Return a simple text of `group(1)` of a Pattern. """
    def handleMatch(self, m, data):
        return markdown.util.AtomicString('<b>atomic</b>'), m.start(0), m.end(0)


class TestConfigParsing(unittest.TestCase):
    def assertParses(self, value, result):
        self.assertIs(markdown.util.parseBoolValue(value, False), result)

    def testBooleansParsing(self):
        self.assertParses(True, True)
        self.assertParses('novalue', None)
        self.assertParses('yES', True)
        self.assertParses('FALSE', False)
        self.assertParses(0., False)
        self.assertParses('none', False)

    def testPreserveNone(self):
        self.assertIsNone(markdown.util.parseBoolValue('None', preserve_none=True))
        self.assertIsNone(markdown.util.parseBoolValue(None, preserve_none=True))

    def testInvalidBooleansParsing(self):
        self.assertRaises(ValueError, markdown.util.parseBoolValue, 'novalue')


class TestCliOptionParsing(unittest.TestCase):
    """ Test parsing of Command Line Interface Options. """

    def setUp(self):
        self.default_options = {
            'input': None,
            'output': None,
            'encoding': None,
            'output_format': 'xhtml',
            'lazy_ol': True,
            'extensions': [],
            'extension_configs': {},
        }
        self.tempfile = ''

    def tearDown(self):
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def testNoOptions(self):
        options, logging_level = parse_options([])
        self.assertEqual(options, self.default_options)
        self.assertEqual(logging_level, CRITICAL)

    def testQuietOption(self):
        options, logging_level = parse_options(['-q'])
        self.assertGreater(logging_level, CRITICAL)

    def testVerboseOption(self):
        options, logging_level = parse_options(['-v'])
        self.assertEqual(logging_level, WARNING)

    def testNoisyOption(self):
        options, logging_level = parse_options(['--noisy'])
        self.assertEqual(logging_level, DEBUG)

    def testInputFileOption(self):
        options, logging_level = parse_options(['foo.txt'])
        self.default_options['input'] = 'foo.txt'
        self.assertEqual(options, self.default_options)

    def testOutputFileOption(self):
        options, logging_level = parse_options(['-f', 'foo.html'])
        self.default_options['output'] = 'foo.html'
        self.assertEqual(options, self.default_options)

    def testInputAndOutputFileOptions(self):
        options, logging_level = parse_options(['-f', 'foo.html', 'foo.txt'])
        self.default_options['output'] = 'foo.html'
        self.default_options['input'] = 'foo.txt'
        self.assertEqual(options, self.default_options)

    def testEncodingOption(self):
        options, logging_level = parse_options(['-e', 'utf-8'])
        self.default_options['encoding'] = 'utf-8'
        self.assertEqual(options, self.default_options)

    def testOutputFormatOption(self):
        options, logging_level = parse_options(['-o', 'html'])
        self.default_options['output_format'] = 'html'
        self.assertEqual(options, self.default_options)

    def testNoLazyOlOption(self):
        options, logging_level = parse_options(['-n'])
        self.default_options['lazy_ol'] = False
        self.assertEqual(options, self.default_options)

    def testExtensionOption(self):
        options, logging_level = parse_options(['-x', 'markdown.extensions.footnotes'])
        self.default_options['extensions'] = ['markdown.extensions.footnotes']
        self.assertEqual(options, self.default_options)

    def testMultipleExtensionOptions(self):
        options, logging_level = parse_options([
            '-x', 'markdown.extensions.footnotes',
            '-x', 'markdown.extensions.smarty'
        ])
        self.default_options['extensions'] = [
            'markdown.extensions.footnotes',
            'markdown.extensions.smarty'
        ]
        self.assertEqual(options, self.default_options)

    def create_config_file(self, config):
        """ Helper to create temporary configuration files. """
        if not isinstance(config, str):
            # convert to string
            config = yaml.dump(config)
        fd, self.tempfile = tempfile.mkstemp('.yml')
        with os.fdopen(fd, 'w') as fp:
            fp.write(config)

    def testExtensionConfigOption(self):
        a = {
            'markdown.extensions.wikilinks': {
                'base_url': 'http://example.com/',
                'end_url': '.html',
                'html_class': 'test',
            },
            'markdown.extensions.footnotes:FootnotesExtension': {
                'PLACE_MARKER': '~~~footnotes~~~'
            }
        }
        self.create_config_file(a)
        options, logging_level = parse_options(['-c', self.tempfile])
        self.default_options['extension_configs'] = a
        self.assertEqual(options, self.default_options)

    def textBoolExtensionConfigOption(self):
        a = {
            'markdown.extensions.toc': {
                'title': 'Some Title',
                'anchorlink': True,
                'permalink': True
            }
        }
        self.create_config_file(a)
        options, logging_level = parse_options(['-c', self.tempfile])
        self.default_options['extension_configs'] = a
        self.assertEqual(options, self.default_options)

    def testExtensionConfigOptionAsJSON(self):
        a = {
            'markdown.extensions.wikilinks': {
                'base_url': 'http://example.com/',
                'end_url': '.html',
                'html_class': 'test',
            },
            'markdown.extensions.footnotes:FootnotesExtension': {
                'PLACE_MARKER': '~~~footnotes~~~'
            }
        }
        import json
        self.create_config_file(json.dumps(a))
        options, logging_level = parse_options(['-c', self.tempfile])
        self.default_options['extension_configs'] = a
        self.assertEqual(options, self.default_options)

    def testExtensionConfigOptionMissingFile(self):
        self.assertRaises(IOError, parse_options, ['-c', 'missing_file.yaml'])

    def testExtensionConfigOptionBadFormat(self):
        a = """
[footnotes]
PLACE_MARKER= ~~~footnotes~~~
"""
        self.create_config_file(a)
        self.assertRaises(yaml.YAMLError, parse_options, ['-c', self.tempfile])


class TestEscapeAppend(unittest.TestCase):
    """ Tests escape character append. """

    def testAppend(self):
        """ Test that appended escapes are only in the current instance. """
        a = markdown.Markdown()
        a.ESCAPED_CHARS.append('|')
        self.assertEqual('|' in a.ESCAPED_CHARS, True)
        b = markdown.Markdown()
        self.assertEqual('|' not in b.ESCAPED_CHARS, True)


class TestBlockAppend(unittest.TestCase):
    """ Tests block `kHTML` append. """

    def testBlockAppend(self):
        """ Test that appended escapes are only in the current instance. """
        a = markdown.Markdown()
        a.block_level_elements.append('test')
        self.assertEqual('test' in a.block_level_elements, True)
        b = markdown.Markdown()
        self.assertEqual('test' not in b.block_level_elements, True)


class TestAncestorExclusion(unittest.TestCase):
    """ Tests exclusion of tags in ancestor list. """

    class AncestorExample(markdown.inlinepatterns.SimpleTagInlineProcessor):
        """ Ancestor Test. """

        ANCESTOR_EXCLUDES = ('a',)

        def handleMatch(self, m, data):
            """ Handle match. """
            a = etree.Element(self.tag)
            a.text = m.group(2)
            return a, m.start(0), m.end(0)

    class AncestorExtension(markdown.Extension):

        def __init__(self, *args, **kwargs):
            """Initialize."""

            self.config = {}

        def extendMarkdown(self, md):
            """Modify inline patterns."""

            a = r'(\+)([^\+]+)\1'
            md.inlinePatterns.register(TestAncestorExclusion.AncestorExample(a, 'strong'), 'ancestor-test', 0)

    def setUp(self):
        """Setup markdown object."""
        self.md = markdown.Markdown(extensions=[TestAncestorExclusion.AncestorExtension()])

    def test_ancestors(self):
        """ Test that an extension can exclude parent tags. """
        b = """
Some +test+ and a [+link+](http://test.com)
"""
        a = """<p>Some <strong>test</strong> and a <a href="http://test.com">+link+</a></p>"""

        self.md.reset()
        self.assertEqual(self.md.convert(b), a)

    def test_ancestors_tail(self):
        """ Test that an extension can exclude parent tags when dealing with a tail. """
        b = """
[***+em+*+strong+**](http://test.com)
"""
        a = """<p><a href="http://test.com"><strong><em>+em+</em>+strong+</strong></a></p>"""

        self.md.reset()
        self.assertEqual(self.md.convert(b), a)
