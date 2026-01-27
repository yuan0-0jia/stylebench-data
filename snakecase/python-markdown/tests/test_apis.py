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

    def test_blank_input(self):
        """ Test blank input. """
        self.assertEqual(self.md.convert(''), '')

    def test_whitespace_only(self):
        """ Test input of only whitespace. """
        self.assertEqual(self.md.convert(' '), '')

    def test_simple_input(self):
        """ Test simple input. """
        self.assertEqual(self.md.convert('foo'), '<p>foo</p>')

    def test_instance_extension(self):
        """ Test Extension loading with a class instance. """
        from markdown.extensions.footnotes import FootnoteExtension
        markdown.Markdown(extensions=[FootnoteExtension()])

    def test_entry_point_extension(self):
        """ Test Extension loading with an entry point. """
        markdown.Markdown(extensions=['footnotes'])

    def test_dot_notation_extension(self):
        """ Test Extension loading with Name (`path.to.module`). """
        markdown.Markdown(extensions=['markdown.extensions.footnotes'])

    def test_dot_notation_extension_with_class(self):
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

    def get_temp_files(self, src):
        """ Return the file names for two temp files. """
        infd, infile = tempfile.mkstemp(suffix='.txt')
        with os.fdopen(infd, 'w') as fp:
            fp.write(src)
        outfd, outfile = tempfile.mkstemp(suffix='.html')
        return infile, outfile, outfd

    def test_file_names(self):
        infile, outfile, outfd = self.get_temp_files('foo')
        markdown.markdown_from_file(input=infile, output=outfile)
        with os.fdopen(outfd, 'r') as fp:
            output = fp.read()
        self.assertEqual(output, '<p>foo</p>')

    def test_file_objects(self):
        infile = BytesIO(bytes('foo', encoding='utf-8'))
        outfile = BytesIO()
        markdown.markdown_from_file(input=infile, output=outfile)
        outfile.seek(0)
        self.assertEqual(outfile.read().decode('utf-8'), '<p>foo</p>')

    def test_stdin_stdout(self):
        markdown.markdown_from_file()
        sys.stdout.seek(0)
        self.assertEqual(sys.stdout.read(), '<p>foo</p>')


class TestBlockParser(unittest.TestCase):
    """ Tests of the BlockParser class. """

    def setUp(self):
        """ Create instance of BlockParser. """
        self.parser = markdown.Markdown().parser

    def test_parse_chunk(self):
        """ Test `BlockParser.parseChunk`. """
        root = etree.Element("div")
        text = 'foo'
        self.parser.parse_chunk(root, text)
        self.assertEqual(
            markdown.serializers.to_xhtml_string(root),
            "<div><p>foo</p></div>"
        )

    def test_parse_document(self):
        """ Test `BlockParser.parseDocument`. """
        lines = ['#foo', '', 'bar', '', '    baz']
        tree = self.parser.parse_document(lines)
        self.assertIsInstance(tree, etree.ElementTree)
        self.assertIs(etree.iselement(tree.getroot()), True)
        self.assertEqual(
            markdown.serializers.to_xhtml_string(tree.getroot()),
            "<div><h1>foo</h1><p>bar</p><pre><code>baz\n</code></pre></div>"
        )


class TestBlockParserState(unittest.TestCase):
    """ Tests of the State class for `BlockParser`. """

    def setUp(self):
        self.state = markdown.blockparser.State()

    def test_blank_state(self):
        """ Test State when empty. """
        self.assertEqual(self.state, [])

    def test_set_sate(self):
        """ Test State.set(). """
        self.state.set('a_state')
        self.assertEqual(self.state, ['a_state'])
        self.state.set('state2')
        self.assertEqual(self.state, ['a_state', 'state2'])

    def test_is_sate(self):
        """ Test `State.isstate()`. """
        self.assertEqual(self.state.isstate('anything'), False)
        self.state.set('a_state')
        self.assertEqual(self.state.isstate('a_state'), True)
        self.state.set('state2')
        self.assertEqual(self.state.isstate('state2'), True)
        self.assertEqual(self.state.isstate('a_state'), False)
        self.assertEqual(self.state.isstate('missing'), False)

    def test_reset(self):
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

    def test_simple_store(self):
        """ Test `HtmlStash.store`. """
        self.assertEqual(self.placeholder, self.stash.get_placeholder(0))
        self.assertEqual(self.stash.html_counter, 1)
        self.assertEqual(self.stash.raw_html_blocks, ['foo'])

    def test_store_more(self):
        """ Test `HtmlStash.store` with additional blocks. """
        placeholder = self.stash.store('bar')
        self.assertEqual(placeholder, self.stash.get_placeholder(1))
        self.assertEqual(self.stash.html_counter, 2)
        self.assertEqual(
            self.stash.raw_html_blocks,
            ['foo', 'bar']
        )

    def test_reset(self):
        """ Test `HtmlStash.reset`. """
        self.stash.reset()
        self.assertEqual(self.stash.html_counter, 0)
        self.assertEqual(self.stash.raw_html_blocks, [])


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

    def test_create_registry(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        self.assertEqual(len(r), 1)
        self.assertIsInstance(r, markdown.util.Registry)

    def test_register_without_priority(self):
        r = markdown.util.Registry()
        with self.assertRaises(TypeError):
            r.register(Item('a'))

    def test_sort_registry(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 21)
        r.register(Item('c'), 'c', 20.5)
        self.assertEqual(len(r), 3)
        self.assertEqual(list(r), ['b', 'c', 'a'])

    def test_is_sorted(self):
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

    def test_deregister(self):
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

    def test_registry_contains(self):
        r = markdown.util.Registry()
        item = Item('a')
        r.register(item, 'a', 20)
        self.assertIs('a' in r, True)
        self.assertIn(item, r)
        self.assertNotIn('b', r)

    def test_registry_iter(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(list(r), ['b', 'a'])

    def test_registry_get_item_by_index(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(r[0], 'b')
        self.assertEqual(r[1], 'a')
        with self.assertRaises(IndexError):
            r[3]

    def test_registry_get_item_by_item(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(r['a'], 'a')
        self.assertEqual(r['b'], 'b')
        with self.assertRaises(KeyError):
            r['c']

    def test_registry_set_item(self):
        r = markdown.util.Registry()
        with self.assertRaises(TypeError):
            r[0] = 'a'
        with self.assertRaises(TypeError):
            r['a'] = 'a'

    def test_registry_del_item(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        with self.assertRaises(TypeError):
            del r[0]
        with self.assertRaises(TypeError):
            del r['a']

    def test_registry_slice(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        r.register(Item('c'), 'c', 40)
        slc = r[1:]
        self.assertEqual(len(slc), 2)
        self.assertIsInstance(slc, markdown.util.Registry)
        self.assertEqual(list(slc), ['b', 'a'])

    def test_get_index_for_name(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(r.get_index_for_name('a'), 1)
        self.assertEqual(r.get_index_for_name('b'), 0)
        with self.assertRaises(ValueError):
            r.get_index_for_name('c')

    def test_register_dupplicate(self):
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

    def test_bad_output_format(self):
        """ Test failure on bad output_format. """
        self.assertRaises(KeyError, markdown.Markdown, output_format='invalid')

    def test_load_extension_failure(self):
        """ Test failure of an extension to load. """
        self.assertRaises(
            ImportError,
            markdown.Markdown, extensions=['non_existant_ext']
        )

    def test_load_bad_extension(self):
        """ Test loading of an Extension with no makeExtension function. """
        self.assertRaises(AttributeError, markdown.Markdown, extensions=['markdown.util'])

    def test_non_extension(self):
        """ Test loading a non Extension object as an extension. """
        self.assertRaises(TypeError, markdown.Markdown, extensions=[object])

    def test_dot_notation_extension_with_bad_class(self):
        """ Test Extension loading with non-existent class name (`path.to.module:Class`). """
        self.assertRaises(
            AttributeError,
            markdown.Markdown,
            extensions=['markdown.extensions.footnotes:MissingExtension']
        )

    def test_base_extention(self):
        """ Test that the base Extension class will raise `NotImplemented`. """
        self.assertRaises(
            NotImplementedError,
            markdown.Markdown, extensions=[markdown.extensions.Extension()]
        )


class test_e_tree_comments(unittest.TestCase):
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

    def test_comment_is_comment(self):
        """ Test that an `ElementTree` `Comment` passes the `is Comment` test. """
        self.assertIs(self.comment.tag, etree.Comment)

    def test_comment_is_block_level(self):
        """ Test that an `ElementTree` `Comment` is recognized as `BlockLevel`. """
        md = markdown.Markdown()
        self.assertIs(md.is_block_level(self.comment.tag), False)

    def test_comment_serialization(self):
        """ Test that an `ElementTree` `Comment` serializes properly. """
        self.assertEqual(
            markdown.serializers.to_html_string(self.comment),
            '<!--foo-->'
        )

    def test_comment_prettify(self):
        """ Test that an `ElementTree` `Comment` is prettified properly. """
        pretty = markdown.treeprocessors.PrettifyTreeprocessor(markdown.Markdown())
        pretty.run(self.comment)
        self.assertEqual(
            markdown.serializers.to_html_string(self.comment),
            '<!--foo-->\n'
        )


class test_element_tail_tests(unittest.TestCase):
    """ Element Tail Tests """
    def setUp(self):
        self.pretty = markdown.treeprocessors.PrettifyTreeprocessor(markdown.Markdown())

    def test_br_tail_no_newline(self):
        """ Test that last `<br>` in tree has a new line tail """
        root = etree.Element('root')
        br = etree.SubElement(root, 'br')
        self.assertEqual(br.tail, None)
        self.pretty.run(root)
        self.assertEqual(br.tail, "\n")


class test_element_pre_code_tests(unittest.TestCase):
    """ Element `PreCode` Tests """
    def setUp(self):
        md = markdown.Markdown()
        self.pretty = markdown.treeprocessors.PrettifyTreeprocessor(md)

    def prettify(self, xml):
        root = etree.fromstring(xml)
        self.pretty.run(root)
        return etree.tostring(root, encoding="unicode", short_empty_elements=False)

    def test_pre_code_empty(self):
        xml = "<pre><code></code></pre>"
        expected = "<pre><code></code></pre>\n"
        self.assertEqual(expected, self.prettify(xml))

    def test_pre_code_with_children(self):
        xml = "<pre><code> <span /></code></pre>"
        expected = "<pre><code> <span></span></code></pre>\n"
        self.assertEqual(expected, self.prettify(xml))

    def test_pre_code_with_space_only(self):
        xml = "<pre><code> </code></pre>"
        expected = "<pre><code>\n</code></pre>\n"
        self.assertEqual(expected, self.prettify(xml))

    def test_pre_code_with_text(self):
        xml = "<pre><code> hello</code></pre>"
        expected = "<pre><code> hello\n</code></pre>\n"
        self.assertEqual(expected, self.prettify(xml))

    def test_pre_code_with_trailing_space(self):
        xml = "<pre><code> hello </code></pre>"
        expected = "<pre><code> hello\n</code></pre>\n"
        self.assertEqual(expected, self.prettify(xml))


class test_serializers(unittest.TestCase):
    """ Test the html and xhtml serializers. """

    def test_html(self):
        """ Test HTML serialization. """
        el = etree.Element('div')
        el.set('id', 'foo<&">')
        p = etree.SubElement(el, 'p')
        p.text = 'foo <&escaped>'
        p.set('hidden', 'hidden')
        etree.SubElement(el, 'hr')
        non_element = etree.SubElement(el, None)
        non_element.text = 'non-element text'
        script = etree.SubElement(non_element, 'script')
        script.text = '<&"test\nescaping">'
        el.tail = "tail text"
        self.assertEqual(
            markdown.serializers.to_html_string(el),
            '<div id="foo&lt;&amp;&quot;&gt;">'
            '<p hidden>foo &lt;&amp;escaped&gt;</p>'
            '<hr>'
            'non-element text'
            '<script><&"test\nescaping"></script>'
            '</div>tail text'
        )

    def test_xhtml(self):
        """" Test XHTML serialization. """
        el = etree.Element('div')
        el.set('id', 'foo<&">')
        p = etree.SubElement(el, 'p')
        p.text = 'foo<&escaped>'
        p.set('hidden', 'hidden')
        etree.SubElement(el, 'hr')
        non_element = etree.SubElement(el, None)
        non_element.text = 'non-element text'
        script = etree.SubElement(non_element, 'script')
        script.text = '<&"test\nescaping">'
        el.tail = "tail text"
        self.assertEqual(
            markdown.serializers.to_xhtml_string(el),
            '<div id="foo&lt;&amp;&quot;&gt;">'
            '<p hidden="hidden">foo&lt;&amp;escaped&gt;</p>'
            '<hr />'
            'non-element text'
            '<script><&"test\nescaping"></script>'
            '</div>tail text'
        )

    def test_mixed_case_tags(self):
        """" Test preservation of tag case. """
        el = etree.Element('MixedCase')
        el.text = 'not valid '
        em = etree.SubElement(el, 'EMPHASIS')
        em.text = 'html'
        etree.SubElement(el, 'HR')
        self.assertEqual(
            markdown.serializers.to_xhtml_string(el),
            '<MixedCase>not valid <EMPHASIS>html</EMPHASIS><HR /></MixedCase>'
        )

    def test_prosessing_instruction(self):
        """ Test serialization of `ProcessignInstruction`. """
        pi = ProcessingInstruction('foo', text='<&"test\nescaping">')
        self.assertIs(pi.tag, ProcessingInstruction)
        self.assertEqual(
            markdown.serializers.to_xhtml_string(pi),
            '<?foo &lt;&amp;"test\nescaping"&gt;?>'
        )

    def test_q_name_tag(self):
        """ Test serialization of `QName` tag. """
        div = etree.Element('div')
        qname = etree.QName('http://www.w3.org/1998/Math/MathML', 'math')
        math = etree.SubElement(div, qname)
        math.set('display', 'block')
        sem = etree.SubElement(math, 'semantics')
        msup = etree.SubElement(sem, 'msup')
        mi = etree.SubElement(msup, 'mi')
        mi.text = 'x'
        mn = etree.SubElement(msup, 'mn')
        mn.text = '2'
        ann = etree.SubElement(sem, 'annotations')
        ann.text = 'x^2'
        self.assertEqual(
            markdown.serializers.to_xhtml_string(div),
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

    def test_q_name_attribute(self):
        """ Test serialization of `QName` attribute. """
        div = etree.Element('div')
        div.set(etree.QName('foo'), etree.QName('bar'))
        self.assertEqual(
            markdown.serializers.to_xhtml_string(div),
            '<div foo="bar"></div>'
        )

    def test_bad_q_name_tag(self):
        """ Test serialization of `QName` with no tag. """
        qname = etree.QName('http://www.w3.org/1998/Math/MathML')
        el = etree.Element(qname)
        self.assertRaises(ValueError, markdown.serializers.to_xhtml_string, el)

    def test_q_name_escaping(self):
        """ Test `QName` escaping. """
        qname = etree.QName('<&"test\nescaping">', 'div')
        el = etree.Element(qname)
        self.assertEqual(
            markdown.serializers.to_xhtml_string(el),
            '<div xmlns="&lt;&amp;&quot;test&#10;escaping&quot;&gt;"></div>'
        )

    def test_q_name_pre_escaping(self):
        """ Test `QName` that is already partially escaped. """
        qname = etree.QName('&lt;&amp;"test&#10;escaping"&gt;', 'div')
        el = etree.Element(qname)
        self.assertEqual(
            markdown.serializers.to_xhtml_string(el),
            '<div xmlns="&lt;&amp;&quot;test&#10;escaping&quot;&gt;"></div>'
        )

    def build_extension(self):
        """ Build an extension which registers `fakeSerializer`. """
        def fake_serializer(elem):
            # Ignore input and return hard-coded output
            return '<div><p>foo</p></div>'

        class register_fake_serializer(markdown.extensions.Extension):
            def extend_markdown(self, md):
                md.output_formats['fake'] = fake_serializer

        return register_fake_serializer()

    def test_register_serializer(self):
        self.assertEqual(
            markdown.markdown(
                'baz', extensions=[self.build_extension()], output_format='fake'
            ),
            '<p>foo</p>'
        )

    def test_x_h_t_m_l_output(self):
        self.assertEqual(
            markdown.markdown('foo  \nbar', output_format='xhtml'),
            '<p>foo<br />\nbar</p>'
        )

    def test_h_t_m_l_output(self):
        self.assertEqual(
            markdown.markdown('foo  \nbar', output_format='html'),
            '<p>foo<br>\nbar</p>'
        )


class test_atomic_string(unittest.TestCase):
    """ Test that `AtomicStrings` are honored (not parsed). """

    def setUp(self):
        self.md = markdown.Markdown()
        self.inlineprocessor = self.md.treeprocessors['inline']

    def test_string(self):
        """ Test that a regular string is parsed. """
        tree = etree.Element('div')
        p = etree.SubElement(tree, 'p')
        p.text = 'some *text*'
        new = self.inlineprocessor.run(tree)
        self.assertEqual(
            markdown.serializers.to_html_string(new),
            '<div><p>some <em>text</em></p></div>'
        )

    def test_simple_atomic_string(self):
        """ Test that a simple `AtomicString` is not parsed. """
        tree = etree.Element('div')
        p = etree.SubElement(tree, 'p')
        p.text = markdown.util.AtomicString('some *text*')
        new = self.inlineprocessor.run(tree)
        self.assertEqual(
            markdown.serializers.to_html_string(new),
            '<div><p>some *text*</p></div>'
        )

    def test_nested_atomic_string(self):
        """ Test that a nested `AtomicString` is not parsed. """
        tree = etree.Element('div')
        p = etree.SubElement(tree, 'p')
        p.text = markdown.util.AtomicString('*some* ')
        span1 = etree.SubElement(p, 'span')
        span1.text = markdown.util.AtomicString('*more* ')
        span2 = etree.SubElement(span1, 'span')
        span2.text = markdown.util.AtomicString('*text* ')
        span3 = etree.SubElement(span2, 'span')
        span3.text = markdown.util.AtomicString('*here*')
        span3.tail = markdown.util.AtomicString(' *to*')
        span2.tail = markdown.util.AtomicString(' *test*')
        span1.tail = markdown.util.AtomicString(' *with*')
        new = self.inlineprocessor.run(tree)
        self.assertEqual(
            markdown.serializers.to_html_string(new),
            '<div><p>*some* <span>*more* <span>*text* <span>*here*</span> '
            '*to*</span> *test*</span> *with*</p></div>'
        )

    def test_inline_processor_doesnt_crash_with_wrong_atomic_string(self):
        """ Test that an `AtomicString` returned from a Pattern doesn't cause a crash. """
        tree = etree.Element('div')
        p = etree.SubElement(tree, 'p')
        p.text = 'a marker c'
        self.md.inline_patterns.register(
            _inlineprocessorthatreturnsatomicstring(r'marker', self.md), 'test', 100
        )
        new = self.inlineprocessor.run(tree)
        self.assertEqual(
            markdown.serializers.to_html_string(new),
            '<div><p>a &lt;b&gt;atomic&lt;/b&gt; c</p></div>'
        )


class _inlineprocessorthatreturnsatomicstring(inlinepatterns.InlineProcessor):
    """ Return a simple text of `group(1)` of a Pattern. """
    def handle_match(self, m, data):
        return markdown.util.AtomicString('<b>atomic</b>'), m.start(0), m.end(0)


class TestConfigParsing(unittest.TestCase):
    def assert_parses(self, value, result):
        self.assertIs(markdown.util.parse_bool_value(value, False), result)

    def test_booleans_parsing(self):
        self.assert_parses(True, True)
        self.assert_parses('novalue', None)
        self.assert_parses('yES', True)
        self.assert_parses('FALSE', False)
        self.assert_parses(0., False)
        self.assert_parses('none', False)

    def test_preserve_none(self):
        self.assertIsNone(markdown.util.parse_bool_value('None', preserve_none=True))
        self.assertIsNone(markdown.util.parse_bool_value(None, preserve_none=True))

    def test_invalid_booleans_parsing(self):
        self.assertRaises(ValueError, markdown.util.parse_bool_value, 'novalue')


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

    def test_no_options(self):
        options, logging_level = parse_options([])
        self.assertEqual(options, self.default_options)
        self.assertEqual(logging_level, CRITICAL)

    def test_quiet_option(self):
        options, logging_level = parse_options(['-q'])
        self.assertGreater(logging_level, CRITICAL)

    def test_verbose_option(self):
        options, logging_level = parse_options(['-v'])
        self.assertEqual(logging_level, WARNING)

    def test_noisy_option(self):
        options, logging_level = parse_options(['--noisy'])
        self.assertEqual(logging_level, DEBUG)

    def test_input_file_option(self):
        options, logging_level = parse_options(['foo.txt'])
        self.default_options['input'] = 'foo.txt'
        self.assertEqual(options, self.default_options)

    def test_output_file_option(self):
        options, logging_level = parse_options(['-f', 'foo.html'])
        self.default_options['output'] = 'foo.html'
        self.assertEqual(options, self.default_options)

    def test_input_and_output_file_options(self):
        options, logging_level = parse_options(['-f', 'foo.html', 'foo.txt'])
        self.default_options['output'] = 'foo.html'
        self.default_options['input'] = 'foo.txt'
        self.assertEqual(options, self.default_options)

    def test_encoding_option(self):
        options, logging_level = parse_options(['-e', 'utf-8'])
        self.default_options['encoding'] = 'utf-8'
        self.assertEqual(options, self.default_options)

    def test_output_format_option(self):
        options, logging_level = parse_options(['-o', 'html'])
        self.default_options['output_format'] = 'html'
        self.assertEqual(options, self.default_options)

    def test_no_lazy_ol_option(self):
        options, logging_level = parse_options(['-n'])
        self.default_options['lazy_ol'] = False
        self.assertEqual(options, self.default_options)

    def test_extension_option(self):
        options, logging_level = parse_options(['-x', 'markdown.extensions.footnotes'])
        self.default_options['extensions'] = ['markdown.extensions.footnotes']
        self.assertEqual(options, self.default_options)

    def test_multiple_extension_options(self):
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

    def test_extension_config_option(self):
        config = {
            'markdown.extensions.wikilinks': {
                'base_url': 'http://example.com/',
                'end_url': '.html',
                'html_class': 'test',
            },
            'markdown.extensions.footnotes:FootnotesExtension': {
                'PLACE_MARKER': '~~~footnotes~~~'
            }
        }
        self.create_config_file(config)
        options, logging_level = parse_options(['-c', self.tempfile])
        self.default_options['extension_configs'] = config
        self.assertEqual(options, self.default_options)

    def text_bool_extension_config_option(self):
        config = {
            'markdown.extensions.toc': {
                'title': 'Some Title',
                'anchorlink': True,
                'permalink': True
            }
        }
        self.create_config_file(config)
        options, logging_level = parse_options(['-c', self.tempfile])
        self.default_options['extension_configs'] = config
        self.assertEqual(options, self.default_options)

    def test_extension_config_option_as_j_s_o_n(self):
        config = {
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
        self.create_config_file(json.dumps(config))
        options, logging_level = parse_options(['-c', self.tempfile])
        self.default_options['extension_configs'] = config
        self.assertEqual(options, self.default_options)

    def test_extension_config_option_missing_file(self):
        self.assertRaises(IOError, parse_options, ['-c', 'missing_file.yaml'])

    def test_extension_config_option_bad_format(self):
        config = """
[footnotes]
PLACE_MARKER= ~~~footnotes~~~
"""
        self.create_config_file(config)
        self.assertRaises(yaml.YAMLError, parse_options, ['-c', self.tempfile])


class TestEscapeAppend(unittest.TestCase):
    """ Tests escape character append. """

    def test_append(self):
        """ Test that appended escapes are only in the current instance. """
        md = markdown.Markdown()
        md.ESCAPED_CHARS.append('|')
        self.assertEqual('|' in md.ESCAPED_CHARS, True)
        md2 = markdown.Markdown()
        self.assertEqual('|' not in md2.ESCAPED_CHARS, True)


class TestBlockAppend(unittest.TestCase):
    """ Tests block `kHTML` append. """

    def test_block_append(self):
        """ Test that appended escapes are only in the current instance. """
        md = markdown.Markdown()
        md.block_level_elements.append('test')
        self.assertEqual('test' in md.block_level_elements, True)
        md2 = markdown.Markdown()
        self.assertEqual('test' not in md2.block_level_elements, True)


class TestAncestorExclusion(unittest.TestCase):
    """ Tests exclusion of tags in ancestor list. """

    class AncestorExample(markdown.inlinepatterns.SimpleTagInlineProcessor):
        """ Ancestor Test. """

        ANCESTOR_EXCLUDES = ('a',)

        def handle_match(self, m, data):
            """ Handle match. """
            el = etree.Element(self.tag)
            el.text = m.group(2)
            return el, m.start(0), m.end(0)

    class AncestorExtension(markdown.Extension):

        def __init__(self, *args, **kwargs):
            """Initialize."""

            self.config = {}

        def extend_markdown(self, md):
            """Modify inline patterns."""

            pattern = r'(\+)([^\+]+)\1'
            md.inline_patterns.register(TestAncestorExclusion.AncestorExample(pattern, 'strong'), 'ancestor-test', 0)

    def setUp(self):
        """Setup markdown object."""
        self.md = markdown.Markdown(extensions=[TestAncestorExclusion.AncestorExtension()])

    def test_ancestors(self):
        """ Test that an extension can exclude parent tags. """
        test = """
Some +test+ and a [+link+](http://test.com)
"""
        result = """<p>Some <strong>test</strong> and a <a href="http://test.com">+link+</a></p>"""

        self.md.reset()
        self.assertEqual(self.md.convert(test), result)

    def test_ancestors_tail(self):
        """ Test that an extension can exclude parent tags when dealing with a tail. """
        test = """
[***+em+*+strong+**](http://test.com)
"""
        result = """<p><a href="http://test.com"><strong><em>+em+</em>+strong+</strong></a></p>"""

        self.md.reset()
        self.assertEqual(self.md.convert(test), result)
