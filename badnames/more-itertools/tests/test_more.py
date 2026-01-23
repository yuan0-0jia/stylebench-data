from __future__ import annotations

import cmath
import gc
import platform
import weakref

from collections import Counter, deque
from collections.abc import Set, Sequence, Iterable, Iterator, Hashable
from datetime import datetime, timedelta
from decimal import Decimal
from doctest import DocTestSuite
from fractions import Fraction
from functools import partial, reduce
from io import StringIO
from itertools import (
    accumulate,
    chain,
    combinations,
    combinations_with_replacement,
    count,
    cycle,
    groupby,
    islice,
    permutations,
    product,
    repeat,
)
from operator import add, mul, itemgetter, not_
from pickle import loads, dumps
from random import Random, random, randrange, seed
from statistics import mean
from string import ascii_letters
from threading import Thread, Lock
from time import sleep
from typing import NamedTuple
from unittest import TestCase, mock

import more_itertools as mi


def load_tests(loader, tests, ignore):
    # Add the doctests
    tests.addTests(DocTestSuite('more_itertools.more'))
    return tests


class ChunkedTests(TestCase):
    """Tests for ``chunked()``"""

    def test_even(self):
        """Test when ``n`` divides evenly into the length of the iterable."""
        self.assertEqual(
            list(mi.chunked('ABCDEF', 3)), [['A', 'B', 'C'], ['D', 'E', 'F']]
        )

    def test_odd(self):
        """Test when ``n`` does not divide evenly into the length of the
        iterable.

        """
        self.assertEqual(
            list(mi.chunked('ABCDE', 3)), [['A', 'B', 'C'], ['D', 'E']]
        )

    def test_none(self):
        """Test when ``n`` has the value ``None``."""
        self.assertEqual(
            list(mi.chunked('ABCDE', None)), [['A', 'B', 'C', 'D', 'E']]
        )

    def test_strict_false(self):
        """Test when ``n`` does not divide evenly into the length of the
        iterable and strict is false.

        """
        self.assertEqual(
            list(mi.chunked('ABCDE', 3, strict=False)),
            [['A', 'B', 'C'], ['D', 'E']],
        )

    def test_strict_being_true(self):
        """Test when ``n`` does not divide evenly into the length of the
        iterable and strict is True (raising an exception).

        """

        def f():
            return list(mi.chunked('ABCDE', 3, strict=True))

        self.assertRaisesRegex(ValueError, "iterable is not divisible by n", f)
        self.assertEqual(
            list(mi.chunked('ABCDEF', 3, strict=True)),
            [['A', 'B', 'C'], ['D', 'E', 'F']],
        )

    def test_strict_being_true_with_size_none(self):
        """Test when ``n`` has value ``None`` and the keyword strict is True
        (raising an exception).

        """

        def f():
            return list(mi.chunked('ABCDE', None, strict=True))

        self.assertRaisesRegex(
            ValueError, "n must not be None when using strict mode.", f
        )


class FirstTests(TestCase):
    def test_many(self):
        # Also try it on a generator expression to make sure it works on
        # whatever those return, across Python versions.
        self.assertEqual(mi.first(x for x in range(4)), 0)

    def test_one(self):
        self.assertEqual(mi.first([3]), 3)

    def test_empty(self):
        with self.assertRaises(ValueError):
            mi.first([])

    def test_default(self):
        self.assertEqual(mi.first([], 'boo'), 'boo')


class IterOnlyRange:
    """User-defined iterable class which only support __iter__.

    >>> r = IterOnlyRange(5)
    >>> r[0]
    AttributeError: IterOnlyRange instance has no attribute '__getitem__'

    Note: In Python 3, ``TypeError`` will be raised because ``object`` is
    inherited implicitly by default.

    >>> r[0]
    TypeError: 'IterOnlyRange' object does not support indexing
    """

    def __init__(self, n):
        """Set the length of the range."""
        self.n = n

    def __iter__(self):
        """Works same as range()."""
        return iter(range(self.n))


class LastTests(TestCase):
    def test_basic(self):
        g = [
            (range(4), 3),
            (iter(range(4)), 3),
            (range(1), 0),
            (iter(range(1)), 0),
            (IterOnlyRange(5), 4),
            ({n: str(n) for n in range(5)}, 4),
            ({0: '0', -1: '-1', 2: '-2'}, 2),
        ]

        for iterable, expected in g:
            with self.subTest(iterable=iterable):
                self.assertEqual(mi.last(iterable), expected)

    def test_default(self):
        for iterable, default, expected in [
            (range(1), None, 0),
            ([], None, None),
            ({}, None, None),
            (iter([]), None, None),
        ]:
            with self.subTest(args=(iterable, default)):
                self.assertEqual(mi.last(iterable, default=default), expected)

    def test_empty(self):
        for g in ([], iter(range(0))):
            with self.subTest(iterable=g):
                with self.assertRaises(ValueError):
                    mi.last(g)

    def test_reversed_is_none(self):
        # See https://github.com/more-itertools/more-itertools/issues/1001
        class ReversedIsNone:
            __reversed__ = None

            def __iter__(self):
                return iter([1])

        self.assertEqual(mi.last(ReversedIsNone()), 1)


class NthOrLastTests(TestCase):
    """Tests for ``nth_or_last()``"""

    def test_basic(self):
        self.assertEqual(mi.nth_or_last(range(3), 1), 1)
        self.assertEqual(mi.nth_or_last(range(3), 3), 2)

    def test_default_value(self):
        g = 42
        self.assertEqual(mi.nth_or_last(range(0), 3, g), g)

    def test_empty_iterable_no_default(self):
        self.assertRaises(ValueError, lambda: mi.nth_or_last(range(0), 0))


class PeekableMixinTests:
    """Common tests for ``peekable()`` and ``seekable()`` behavior"""

    cls = None

    def test_passthrough(self):
        """Iterating a peekable without using ``peek()`` or ``prepend()``
        should just give the underlying iterable's elements (a trivial test but
        useful to set a baseline in case something goes wrong)"""
        h = [1, 2, 3, 4, 5]
        g = list(self.cls(h))
        self.assertEqual(g, h)

    def test_peek_default(self):
        """Make sure passing a default into ``peek()`` works."""
        p = self.cls([])
        self.assertEqual(p.peek(7), 7)

    def test_truthiness(self):
        """Make sure a ``peekable`` tests true iff there are items remaining in
        the iterable.

        """
        p = self.cls([])
        self.assertFalse(p)

        p = self.cls(range(3))
        self.assertTrue(p)

    def test_simple_peeking(self):
        """Make sure ``next`` and ``peek`` advance and don't advance the
        iterator, respectively.

        """
        p = self.cls(range(10))
        self.assertEqual(next(p), 0)
        self.assertEqual(p.peek(), 1)
        self.assertEqual(p.peek(), 1)
        self.assertEqual(next(p), 1)


class PeekableTests(PeekableMixinTests, TestCase):
    cls = mi.peekable

    def test_indexing(self):
        """
        Indexing into the peekable shouldn't advance the iterator.
        """
        p = mi.peekable('abcdefghijkl')

        # The 0th index is what ``next()`` will return
        self.assertEqual(p[0], 'a')
        self.assertEqual(next(p), 'a')

        # Indexing further into the peekable shouldn't advance the iterator
        self.assertEqual(p[2], 'd')
        self.assertEqual(next(p), 'b')

        # The 0th index moves up with the iterator; the last index follows
        self.assertEqual(p[0], 'c')
        self.assertEqual(p[9], 'l')

        self.assertEqual(next(p), 'c')
        self.assertEqual(p[8], 'l')

        # Negative indexing should work too
        self.assertEqual(p[-2], 'k')
        self.assertEqual(p[-9], 'd')
        self.assertRaises(IndexError, lambda: p[-10])

    def test_slicing(self):
        """Slicing the peekable shouldn't advance the iterator."""
        g = list('abcdefghijkl')
        p = mi.peekable(g)

        # Slicing the peekable should just be like slicing a re-iterable
        self.assertEqual(p[1:4], g[1:4])

        # Advancing the iterator moves the slices up also
        self.assertEqual(next(p), 'a')
        self.assertEqual(p[1:4], g[1:][1:4])

        # Implicit starts and stop should work
        self.assertEqual(p[:5], g[1:][:5])
        self.assertEqual(p[:], g[1:][:])

        # Indexing past the end should work
        self.assertEqual(p[:100], g[1:][:100])

        # Steps should work, including negative
        self.assertEqual(p[::2], g[1:][::2])
        self.assertEqual(p[::-1], g[1:][::-1])

    def test_slicing_reset(self):
        """Test slicing on a fresh iterable each time"""
        q = ['0', '1', '2', '3', '4', '5']
        m = list(range(-4, len(q) + 4)) + [None]
        u = [1, 2, 3, 4, -1, -2, -3, 4]
        for t in product(m, m, u):
            o = iter(q)
            p = mi.peekable(o)
            next(p)
            j = slice(*t)
            g = p[j]
            h = q[1:][j]
            self.assertEqual(g, h, t)

    def test_slicing_error(self):
        g = '01234567'
        p = mi.peekable(iter(g))

        # Prime the cache
        p.peek()
        h = list(p._cache)

        # Illegal slice
        with self.assertRaises(ValueError):
            p[1:-1:0]

        # Neither the cache nor the iteration should be affected
        self.assertEqual(h, list(p._cache))
        self.assertEqual(list(p), list(g))

    # prepend() behavior tests

    def test_prepend(self):
        """Tests interspersed ``prepend()`` and ``next()`` calls"""
        j = mi.peekable(range(2))
        g = []

        # Test prepend() before next()
        j.prepend(10)
        g += [next(j), next(j)]

        # Test prepend() between next()s
        j.prepend(11)
        g += [next(j), next(j)]

        # Test prepend() after source iterable is consumed
        j.prepend(12)
        g += [next(j)]

        h = [10, 0, 11, 1, 12]
        self.assertEqual(g, h)

    def test_multi_prepend(self):
        """Tests prepending multiple items and getting them in proper order"""
        j = mi.peekable(range(5))
        g = [next(j), next(j)]
        j.prepend(10, 11, 12)
        j.prepend(20, 21)
        g += list(j)
        h = [0, 1, 20, 21, 10, 11, 12, 2, 3, 4]
        self.assertEqual(g, h)

    def test_empty(self):
        """Tests prepending in front of an empty iterable"""
        j = mi.peekable([])
        j.prepend(10)
        g = list(j)
        h = [10]
        self.assertEqual(g, h)

    def test_prepend_truthiness(self):
        """Tests that ``__bool__()`` or ``__nonzero__()`` works properly
        with ``prepend()``"""
        j = mi.peekable(range(5))
        self.assertTrue(j)
        g = list(j)
        self.assertFalse(j)
        j.prepend(10)
        self.assertTrue(j)
        g += [next(j)]
        self.assertFalse(j)
        h = [0, 1, 2, 3, 4, 10]
        self.assertEqual(g, h)

    def test_multi_prepend_peek(self):
        """Tests prepending multiple elements and getting them in reverse order
        while peeking"""
        j = mi.peekable(range(5))
        g = [next(j), next(j)]
        self.assertEqual(j.peek(), 2)
        j.prepend(10, 11, 12)
        self.assertEqual(j.peek(), 10)
        j.prepend(20, 21)
        self.assertEqual(j.peek(), 20)
        g += list(j)
        self.assertFalse(j)
        h = [0, 1, 20, 21, 10, 11, 12, 2, 3, 4]
        self.assertEqual(g, h)

    def test_prepend_after_stop(self):
        """Test resuming iteration after a previous exhaustion"""
        g = mi.peekable(range(3))
        self.assertEqual(list(g), [0, 1, 2])
        self.assertRaises(StopIteration, lambda: next(g))
        g.prepend(10)
        self.assertEqual(next(g), 10)
        self.assertRaises(StopIteration, lambda: next(g))

    def test_prepend_slicing(self):
        """Tests interaction between prepending and slicing"""
        h = list(range(20))
        p = mi.peekable(h)

        p.prepend(30, 40, 50)
        g = [30, 40, 50] + h  # pseq for prepended_seq

        # adapt the specific tests from test_slicing
        self.assertEqual(p[0], 30)
        self.assertEqual(p[1:8], g[1:8])
        self.assertEqual(p[1:], g[1:])
        self.assertEqual(p[:5], g[:5])
        self.assertEqual(p[:], g[:])
        self.assertEqual(p[:100], g[:100])
        self.assertEqual(p[::2], g[::2])
        self.assertEqual(p[::-1], g[::-1])

    def test_prepend_indexing(self):
        """Tests interaction between prepending and indexing"""
        g = list(range(20))
        p = mi.peekable(g)

        p.prepend(30, 40, 50)

        self.assertEqual(p[0], 30)
        self.assertEqual(next(p), 30)
        self.assertEqual(p[2], 0)
        self.assertEqual(next(p), 40)
        self.assertEqual(p[0], 50)
        self.assertEqual(p[9], 8)
        self.assertEqual(next(p), 50)
        self.assertEqual(p[8], 8)
        self.assertEqual(p[-2], 18)
        self.assertEqual(p[-9], 11)
        self.assertRaises(IndexError, lambda: p[-21])

    def test_prepend_iterable(self):
        """Tests prepending from an iterable"""
        j = mi.peekable(range(5))
        # Don't directly use the range() object to avoid any range-specific
        # optimizations
        j.prepend(*(x for x in range(5)))
        g = list(j)
        h = list(chain(range(5), range(5)))
        self.assertEqual(g, h)

    def test_prepend_many(self):
        """Tests that prepending a huge number of elements works"""
        j = mi.peekable(range(5))
        # Don't directly use the range() object to avoid any range-specific
        # optimizations
        j.prepend(*(x for x in range(20000)))
        g = list(j)
        h = list(chain(range(20000), range(5)))
        self.assertEqual(g, h)

    def test_prepend_reversed(self):
        """Tests prepending from a reversed iterable"""
        j = mi.peekable(range(3))
        j.prepend(*reversed((10, 11, 12)))
        g = list(j)
        h = [12, 11, 10, 0, 1, 2]
        self.assertEqual(g, h)


class ConsumerTests(TestCase):
    """Tests for ``consumer()``"""

    def test_consumer(self):
        @mi.consumer
        def eater():
            while True:
                x = yield  # noqa

        e = eater()
        e.send('hi')  # without @consumer, would raise TypeError


class DistinctPermutationsTests(TestCase):
    def test_basic(self):
        j = ['z', 'a', 'a', 'q', 'q', 'q', 'y']
        g = list(mi.distinct_permutations(j))
        h = set(permutations(j))
        self.assertCountEqual(g, h)

    def test_r(self):
        for iterable, r in (
            ('mississippi', 0),
            ('mississippi', 1),
            ('mississippi', 6),
            ('mississippi', 7),
            ('mississippi', 12),
            ([0, 1, 1, 0], 0),
            ([0, 1, 1, 0], 1),
            ([0, 1, 1, 0], 2),
            ([0, 1, 1, 0], 3),
            ([0, 1, 1, 0], 4),
            (['a'], 0),
            (['a'], 1),
            (['a'], 5),
            ([], 0),
            ([], 1),
            ([], 4),
        ):
            with self.subTest(iterable=iterable, r=r):
                h = set(permutations(iterable, r))
                g = list(mi.distinct_permutations(iter(iterable), r))
                self.assertCountEqual(g, h)

    def test_unsortable(self):
        j = ['1', 2, 2, 3, 3, 3]
        g = list(mi.distinct_permutations(j))
        h = set(permutations(j))
        self.assertCountEqual(g, h)

    def test_unsortable_r(self):
        j = ['1', 2, 2, 3, 3, 3]
        for r in range(len(j) + 1):
            with self.subTest(iterable=j, r=r):
                g = list(mi.distinct_permutations(j, r=r))
                h = set(permutations(j, r=r))
                self.assertCountEqual(g, h)

    def test_unsorted_equivalent(self):
        j = [1, True, '3']
        g = list(mi.distinct_permutations(j))
        h = set(permutations(j))
        self.assertCountEqual(g, h)

    def test_unhashable(self):
        j = ([1], [1], 2)
        g = list(mi.distinct_permutations(j))
        h = list(mi.unique_everseen(permutations(j)))
        self.assertCountEqual(g, h)


class DerangementsTests(TestCase):
    def test_unique_values(self):
        n = 8
        h = set(
            x
            for x in permutations(range(n))
            if not any(x[i] == i for i in range(n))
        )
        for i, iterable in enumerate(
            [
                range(n),
                list(range(n)),
                set(range(n)),
            ]
        ):
            g = set(mi.derangements(iterable))
            self.assertEqual(g, h)

    def test_repeated_values(self):
        self.assertEqual(
            [''.join(x) for x in mi.derangements('AACD')],
            [
                'AADC',
                'ACDA',
                'ADAC',
                'CADA',
                'CDAA',
                'CDAA',
                'DAAC',
                'DCAA',
                'DCAA',
            ],
        )

    def test_unsortable_unhashable(self):
        j = (0, True, ['Carol'])
        g = list(mi.derangements(j))
        h = [(True, ['Carol'], 0), (['Carol'], 0, True)]
        self.assertListEqual(g, h)

    def test_r(self):
        s = 'ABCD'
        for r, expected in [
            (0, ['']),
            (1, ['B', 'C', 'D']),
            (2, ['BA', 'BC', 'BD', 'CA', 'CD', 'DA', 'DC']),
            (
                3,
                [
                    'BAD',
                    'BCA',
                    'BCD',
                    'BDA',
                    'CAB',
                    'CAD',
                    'CDA',
                    'CDB',
                    'DAB',
                    'DCA',
                    'DCB',
                ],
            ),
            (
                4,
                [
                    'BADC',
                    'BCDA',
                    'BDAC',
                    'CADB',
                    'CDAB',
                    'CDBA',
                    'DABC',
                    'DCAB',
                    'DCBA',
                ],
            ),
        ]:
            with self.subTest(r=r):
                g = [''.join(x) for x in mi.derangements(s, r=r)]
                self.assertEqual(g, expected)


class IlenTests(TestCase):
    def test_ilen(self):
        """Sanity-checks for ``ilen()``."""
        # Non-empty
        self.assertEqual(
            mi.ilen(filter(lambda x: x % 10 == 0, range(101))), 11
        )

        # Empty
        self.assertEqual(mi.ilen(x for x in range(0)), 0)

        # Iterable with __len__
        self.assertEqual(mi.ilen(list(range(6))), 6)


class MinMaxTests(TestCase):
    def test_basic(self):
        for iterable, expected in (
            # easy case
            ([0, 1, 2, 3], (0, 3)),
            # min and max are not in the extremes + we have `int`s and `float`s
            ([3, 5.5, -1, 2], (-1, 5.5)),
            # unordered collection
            ({3, 5.5, -1, 2}, (-1, 5.5)),
            # with repetitions
            ([3, 5.5, float('-Inf'), 5.5], (float('-Inf'), 5.5)),
            # other collections
            ('banana', ('a', 'n')),
            ({0: 1, 2: 100, 1: 10}, (0, 2)),
            (range(3, 14), (3, 13)),
        ):
            with self.subTest(iterable=iterable, expected=expected):
                # check for expected results
                self.assertTupleEqual(mi.minmax(iterable), expected)
                # check for equality with built-in `min` and `max`
                self.assertTupleEqual(
                    mi.minmax(iterable), (min(iterable), max(iterable))
                )

    def test_unpacked(self):
        self.assertTupleEqual(mi.minmax(2, 3, 1), (1, 3))
        self.assertTupleEqual(mi.minmax(12, 3, 4, key=str), (12, 4))

    def test_iterables(self):
        self.assertTupleEqual(mi.minmax(x for x in [0, 1, 2, 3]), (0, 3))
        self.assertTupleEqual(
            mi.minmax(map(str, [3, 5.5, 'a', 2])), ('2', 'a')
        )
        self.assertTupleEqual(
            mi.minmax(filter(None, [0, 3, '', None, 10])), (3, 10)
        )

    def test_key(self):
        self.assertTupleEqual(
            mi.minmax({(), (1, 4, 2), 'abcde', range(4)}, key=len),
            ((), 'abcde'),
        )
        self.assertTupleEqual(
            mi.minmax((x for x in [10, 3, 25]), key=str), (10, 3)
        )

    def test_default(self):
        with self.assertRaises(ValueError):
            mi.minmax([])

        self.assertIs(mi.minmax([], default=None), None)
        self.assertListEqual(mi.minmax([], default=[1, 'a']), [1, 'a'])


class WithIterTests(TestCase):
    def test_with_iter(self):
        s = StringIO('One fish\nTwo fish')
        g = [line.split()[0] for line in mi.with_iter(s)]

        # Iterable's items should be faithfully represented
        self.assertEqual(g, ['One', 'Two'])
        # The file object should be closed
        self.assertTrue(s.closed)


class OneTests(TestCase):
    def test_basic(self):
        g = iter(['item'])
        self.assertEqual(mi.one(g), 'item')

    def test_too_short_new(self):
        g = iter([])
        self.assertRaises(ValueError, lambda: mi.one(g))
        self.assertRaises(
            OverflowError, lambda: mi.one(g, too_short=OverflowError)
        )

    def test_too_long(self):
        g = count()
        self.assertRaises(ValueError, lambda: mi.one(g))  # burn 0 and 1
        self.assertEqual(next(g), 2)
        self.assertRaises(
            OverflowError, lambda: mi.one(g, too_long=OverflowError)
        )

    def test_too_long_default_message(self):
        g = count()
        self.assertRaisesRegex(
            ValueError,
            "Expected exactly one item in "
            "iterable, but got 0, 1, and "
            "perhaps more.",
            lambda: mi.one(g),
        )


class IntersperseTest(TestCase):
    """Tests for intersperse()"""

    def test_even(self):
        g = (x for x in '01')
        self.assertEqual(
            list(mi.intersperse(None, g)), ['0', None, '1']
        )

    def test_odd(self):
        g = (x for x in '012')
        self.assertEqual(
            list(mi.intersperse(None, g)), ['0', None, '1', None, '2']
        )

    def test_nested(self):
        h = ('a', 'b')
        m = (x for x in '012')
        g = list(mi.intersperse(h, m))
        j = ['0', ('a', 'b'), '1', ('a', 'b'), '2']
        self.assertEqual(g, j)

    def test_not_iterable(self):
        self.assertRaises(TypeError, lambda: mi.intersperse('x', 1))

    def test_n(self):
        for n, element, expected in [
            (1, '_', ['0', '_', '1', '_', '2', '_', '3', '_', '4', '_', '5']),
            (2, '_', ['0', '1', '_', '2', '3', '_', '4', '5']),
            (3, '_', ['0', '1', '2', '_', '3', '4', '5']),
            (4, '_', ['0', '1', '2', '3', '_', '4', '5']),
            (5, '_', ['0', '1', '2', '3', '4', '_', '5']),
            (6, '_', ['0', '1', '2', '3', '4', '5']),
            (7, '_', ['0', '1', '2', '3', '4', '5']),
            (3, ['a', 'b'], ['0', '1', '2', ['a', 'b'], '3', '4', '5']),
        ]:
            h = (x for x in '012345')
            g = list(mi.intersperse(element, h, n=n))
            self.assertEqual(g, expected)

    def test_n_zero(self):
        self.assertRaises(
            ValueError, lambda: list(mi.intersperse('x', '012', n=0))
        )


class UniqueToEachTests(TestCase):
    """Tests for ``unique_to_each()``"""

    def test_all_unique(self):
        """When all the input iterables are unique the output should match
        the input."""
        g = [[1, 2], [3, 4, 5], [6, 7, 8]]
        self.assertEqual(mi.unique_to_each(*g), g)

    def test_duplicates(self):
        """When there are duplicates in any of the input iterables that aren't
        in the rest, those duplicates should be emitted."""
        g = ["mississippi", "missouri"]
        self.assertEqual(
            mi.unique_to_each(*g), [['p', 'p'], ['o', 'u', 'r']]
        )

    def test_mixed(self):
        """When the input iterables contain different types the function should
        still behave properly"""
        g = ['x', (i for i in range(3)), [1, 2, 3], tuple()]
        self.assertEqual(mi.unique_to_each(*g), [['x'], [0], [3], []])


class WindowedTests(TestCase):
    def test_basic(self):
        h = [1, 2, 3, 4, 5]

        for n, expected in (
            (6, [(1, 2, 3, 4, 5, None)]),
            (5, [(1, 2, 3, 4, 5)]),
            (4, [(1, 2, 3, 4), (2, 3, 4, 5)]),
            (3, [(1, 2, 3), (2, 3, 4), (3, 4, 5)]),
            (2, [(1, 2), (2, 3), (3, 4), (4, 5)]),
            (1, [(1,), (2,), (3,), (4,), (5,)]),
            (0, [()]),
        ):
            with self.subTest(n=n):
                g = list(mi.windowed(h, n))
                self.assertEqual(g, expected)

    def test_fillvalue(self):
        g = list(mi.windowed([1, 2, 3, 4, 5], 6, fillvalue='!'))
        h = [(1, 2, 3, 4, 5, '!')]
        self.assertEqual(g, h)

    def test_step(self):
        h = [1, 2, 3, 4, 5, 6, 7]
        for n, step, expected in [
            (3, 2, [(1, 2, 3), (3, 4, 5), (5, 6, 7)]),  # n > step
            (3, 3, [(1, 2, 3), (4, 5, 6), (7, None, None)]),  # n == step
            (3, 4, [(1, 2, 3), (5, 6, 7)]),  # lines up nicely
            (3, 5, [(1, 2, 3), (6, 7, None)]),  # off by one
            (3, 6, [(1, 2, 3), (7, None, None)]),  # off by two
            (3, 7, [(1, 2, 3)]),  # step past the end
            (7, 8, [(1, 2, 3, 4, 5, 6, 7)]),  # step > len(iterable)
        ]:
            with self.subTest(n=n, step=step):
                g = list(mi.windowed(h, n, step=step))
                self.assertEqual(g, expected)

    def test_invalid_step(self):
        # Step must be greater than or equal to 1
        with self.assertRaises(ValueError):
            list(mi.windowed([1, 2, 3, 4, 5], 3, step=0))

    def test_fillvalue_step(self):
        g = list(mi.windowed([1, 2, 3, 4, 5], 3, fillvalue='!', step=3))
        h = [(1, 2, 3), (4, 5, '!')]
        self.assertEqual(g, h)

    def test_negative(self):
        with self.assertRaises(ValueError):
            list(mi.windowed([1, 2, 3, 4, 5], -1))

    def test_empty_seq(self):
        g = list(mi.windowed([], 3))
        h = []
        self.assertEqual(g, h)


class SubstringsTests(TestCase):
    def test_basic(self):
        j = (x for x in range(4))
        g = list(mi.substrings(j))
        h = [
            (0,),
            (1,),
            (2,),
            (3,),
            (0, 1),
            (1, 2),
            (2, 3),
            (0, 1, 2),
            (1, 2, 3),
            (0, 1, 2, 3),
        ]
        self.assertEqual(g, h)

    def test_strings(self):
        j = 'abc'
        g = list(mi.substrings(j))
        h = [
            ('a',),
            ('b',),
            ('c',),
            ('a', 'b'),
            ('b', 'c'),
            ('a', 'b', 'c'),
        ]
        self.assertEqual(g, h)

    def test_empty(self):
        j = iter([])
        g = list(mi.substrings(j))
        h = []
        self.assertEqual(g, h)

    def test_order(self):
        j = [2, 0, 1]
        g = list(mi.substrings(j))
        h = [(2,), (0,), (1,), (2, 0), (0, 1), (2, 0, 1)]
        self.assertEqual(g, h)


class SubstringsIndexesTests(TestCase):
    def test_basic(self):
        j = [x for x in range(4)]
        g = list(mi.substrings_indexes(j))
        h = [
            ([0], 0, 1),
            ([1], 1, 2),
            ([2], 2, 3),
            ([3], 3, 4),
            ([0, 1], 0, 2),
            ([1, 2], 1, 3),
            ([2, 3], 2, 4),
            ([0, 1, 2], 0, 3),
            ([1, 2, 3], 1, 4),
            ([0, 1, 2, 3], 0, 4),
        ]
        self.assertEqual(g, h)

    def test_strings(self):
        j = 'abc'
        g = list(mi.substrings_indexes(j))
        h = [
            ('a', 0, 1),
            ('b', 1, 2),
            ('c', 2, 3),
            ('ab', 0, 2),
            ('bc', 1, 3),
            ('abc', 0, 3),
        ]
        self.assertEqual(g, h)

    def test_empty(self):
        j = []
        g = list(mi.substrings_indexes(j))
        h = []
        self.assertEqual(g, h)

    def test_order(self):
        j = [2, 0, 1]
        g = list(mi.substrings_indexes(j))
        h = [
            ([2], 0, 1),
            ([0], 1, 2),
            ([1], 2, 3),
            ([2, 0], 0, 2),
            ([0, 1], 1, 3),
            ([2, 0, 1], 0, 3),
        ]
        self.assertEqual(g, h)

    def test_reverse(self):
        j = [2, 0, 1]
        g = list(mi.substrings_indexes(j, reverse=True))
        h = [
            ([2, 0, 1], 0, 3),
            ([2, 0], 0, 2),
            ([0, 1], 1, 3),
            ([2], 0, 1),
            ([0], 1, 2),
            ([1], 2, 3),
        ]
        self.assertEqual(g, h)


class BucketTests(TestCase):
    def test_basic(self):
        g = [10, 20, 30, 11, 21, 31, 12, 22, 23, 33]
        D = mi.bucket(g, key=lambda x: 10 * (x // 10))

        # In-order access
        self.assertEqual(list(D[10]), [10, 11, 12])

        # Out of order access
        self.assertEqual(list(D[30]), [30, 31, 33])
        self.assertEqual(list(D[20]), [20, 21, 22, 23])

        self.assertEqual(list(D[40]), [])  # Nothing in here!

    def test_in(self):
        g = [10, 20, 30, 11, 21, 31, 12, 22, 23, 33]
        D = mi.bucket(g, key=lambda x: 10 * (x // 10))

        self.assertIn(10, D)
        self.assertNotIn(40, D)
        self.assertIn(20, D)
        self.assertNotIn(21, D)

        # Checking in-ness shouldn't advance the iterator
        self.assertEqual(next(D[10]), 10)

    def test_validator(self):
        g = count(0)
        h = lambda x: int(str(x)[0])  # First digit of each number
        j = lambda x: 0 < x < 10  # No leading zeros
        D = mi.bucket(g, h, validator=j)
        self.assertEqual(mi.take(3, D[1]), [1, 10, 11])
        self.assertNotIn(0, D)  # Non-valid entries don't return True
        self.assertNotIn(0, D._cache)  # Don't store non-valid entries
        self.assertEqual(list(D[0]), [])

    def test_list(self):
        g = [10, 20, 30, 11, 21, 31, 12, 22, 23, 33]
        D = mi.bucket(g, key=lambda x: 10 * (x // 10))
        self.assertEqual(list(D[10]), [10, 11, 12])
        self.assertEqual(list(D[20]), [20, 21, 22, 23])
        self.assertEqual(list(D[30]), [30, 31, 33])
        self.assertEqual(set(D), {10, 20, 30})

    def test_list_validator(self):
        g = [10, 20, 30, 11, 21, 31, 12, 22, 23, 33]
        h = lambda x: 10 * (x // 10)
        j = lambda x: x != 20
        D = mi.bucket(g, h, validator=j)
        self.assertEqual(set(D), {10, 30})
        self.assertEqual(list(D[10]), [10, 11, 12])
        self.assertEqual(list(D[20]), [])
        self.assertEqual(list(D[30]), [30, 31, 33])


class SpyTests(TestCase):
    """Tests for ``spy()``"""

    def test_basic(self):
        g = iter('abcdefg')
        head, new_iterable = mi.spy(g)
        self.assertEqual(head, ['a'])
        self.assertEqual(
            list(new_iterable), ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        )

    def test_unpacking(self):
        g = iter('abcdefg')
        (first, second, third), new_iterable = mi.spy(g, 3)
        self.assertEqual(first, 'a')
        self.assertEqual(second, 'b')
        self.assertEqual(third, 'c')
        self.assertEqual(
            list(new_iterable), ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        )

    def test_too_many(self):
        g = iter('abc')
        head, new_iterable = mi.spy(g, 4)
        self.assertEqual(head, ['a', 'b', 'c'])
        self.assertEqual(list(new_iterable), ['a', 'b', 'c'])

    def test_zero(self):
        g = iter('abc')
        head, new_iterable = mi.spy(g, 0)
        self.assertEqual(head, [])
        self.assertEqual(list(new_iterable), ['a', 'b', 'c'])

    def test_immutable(self):
        g = iter('abcdefg')
        head, new_iterable = mi.spy(g, 3)
        head[0] = 'A'
        self.assertEqual(head, ['A', 'b', 'c'])
        self.assertEqual(
            list(new_iterable), ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        )


class InterleaveTests(TestCase):
    def test_even(self):
        g = list(mi.interleave([1, 4, 7], [2, 5, 8], [3, 6, 9]))
        h = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(g, h)

    def test_short(self):
        g = list(mi.interleave([1, 4], [2, 5, 7], [3, 6, 8]))
        h = [1, 2, 3, 4, 5, 6]
        self.assertEqual(g, h)

    def test_mixed_types(self):
        m = ['a', 'b', 'c', 'd']
        o = '12345'
        j = count()
        g = list(mi.interleave(m, o, j))
        h = ['a', '1', 0, 'b', '2', 1, 'c', '3', 2, 'd', '4', 3]
        self.assertEqual(g, h)


class InterleaveLongestTests(TestCase):
    def test_even(self):
        g = list(mi.interleave_longest([1, 4, 7], [2, 5, 8], [3, 6, 9]))
        h = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(g, h)

    def test_short(self):
        g = list(mi.interleave_longest([1, 4], [2, 5, 7], [3, 6, 8]))
        h = [1, 2, 3, 4, 5, 6, 7, 8]
        self.assertEqual(g, h)

    def test_mixed_types(self):
        m = ['a', 'b', 'c', 'd']
        o = '12345'
        j = (x for x in range(3))
        g = list(mi.interleave_longest(m, o, j))
        h = ['a', '1', 0, 'b', '2', 1, 'c', '3', 2, 'd', '4', '5']
        self.assertEqual(g, h)


class InterleaveEvenlyTests(TestCase):
    def test_equal_lengths(self):
        # when lengths are equal, the relative order shouldn't change
        a = [1, 2, 3]
        b = [5, 6, 7]
        g = list(mi.interleave_evenly([a, b]))
        h = [1, 5, 2, 6, 3, 7]
        self.assertEqual(g, h)

    def test_proportional(self):
        # easy case where the iterables have proportional length
        a = [1, 2, 3, 4]
        b = [5, 6]
        g = list(mi.interleave_evenly([a, b]))
        j = [1, 2, 5, 3, 4, 6]
        self.assertEqual(g, j)

        # swapping a and b should yield the same result
        h = list(mi.interleave_evenly([b, a]))
        self.assertEqual(h, j)

    def test_not_proportional(self):
        a = [1, 2, 3, 4, 5, 6, 7]
        b = [8, 9, 10]
        h = [1, 2, 8, 3, 4, 9, 5, 6, 10, 7]
        g = list(mi.interleave_evenly([a, b]))
        self.assertEqual(g, h)

    def test_degenerate_one(self):
        a = [0, 1, 2, 3, 4]
        b = [5]
        h = [0, 1, 2, 5, 3, 4]
        g = list(mi.interleave_evenly([a, b]))
        self.assertEqual(g, h)

    def test_degenerate_empty(self):
        a = [1, 2, 3]
        b = []
        h = [1, 2, 3]
        g = list(mi.interleave_evenly([a, b]))
        self.assertEqual(g, h)

    def test_three_iters(self):
        a = ["a1", "a2", "a3", "a4", "a5"]
        b = ["b1", "b2", "b3"]
        c = ["c1"]
        g = list(mi.interleave_evenly([a, b, c]))
        h = ["a1", "b1", "a2", "c1", "a3", "b2", "a4", "b3", "a5"]
        self.assertEqual(g, h)

    def test_many_iters(self):
        # smoke test with many iterables: create iterables with a random
        # number of elements starting with a character ("a0", "a1", ...)
        t = Random(0)
        o = []
        for g in ascii_letters:
            q = t.randint(0, 100)
            m = [f"{g}{i}" for i in range(q)]
            o.append(m)

        h = list(mi.interleave_evenly(o))

        # for each iterable, check that the result contains all its items
        for m, ch_expect in zip(o, ascii_letters):
            j = [
                e for e in h if e.startswith(ch_expect)
            ]
            assert len(set(j)) == len(m)

    def test_manual_lengths(self):
        a = combinations(range(4), 2)
        j = 4 * (4 - 1) // 2  # == 6
        b = combinations(range(4), 3)
        m = 4

        h = [
            (0, 1),
            (0, 1, 2),
            (0, 2),
            (0, 3),
            (0, 1, 3),
            (1, 2),
            (0, 2, 3),
            (1, 3),
            (2, 3),
            (1, 2, 3),
        ]
        g = list(mi.interleave_evenly([a, b], lengths=[j, m]))
        self.assertEqual(h, g)

    def test_no_length_raises(self):
        # combinations doesn't have __len__, should trigger ValueError
        g = [range(5), combinations(range(5), 2)]
        with self.assertRaises(ValueError):
            list(mi.interleave_evenly(g))

    def test_argument_mismatch_raises(self):
        # pass mismatching number of iterables and lengths
        g = [range(3)]
        h = [3, 4]
        with self.assertRaises(ValueError):
            list(mi.interleave_evenly(g, lengths=h))


class InterleaveRandomlyTests(TestCase):
    def test_basic(self):
        seed(0)  # For reproducibility
        g = [1, 2, 3], 'abc', (True, False, None)
        self.assertEqual(
            list(mi.interleave_randomly(*g)),
            ['a', 'b', 1, 'c', True, False, None, 2, 3],
        )

    def test_some_empty(self):
        self.assertEqual(
            list(mi.interleave_randomly([1, 2, 3], [], [])),
            [1, 2, 3],
        )
        self.assertEqual(
            list(mi.interleave_randomly([], [1, 2, 3], [])),
            [1, 2, 3],
        )
        self.assertEqual(
            list(mi.interleave_randomly([], [], [1, 2, 3])),
            [1, 2, 3],
        )

    def test_all_empty(self):
        g = [], [], []
        self.assertEqual(list(mi.interleave_randomly(*g)), [])

    def test_no_args(self):
        self.assertEqual(list(mi.interleave_randomly()), [])

    def test_bad_type(self):
        # Should raise TypeError if not all arguments are iterable
        with self.assertRaises(TypeError):
            list(mi.interleave_randomly(1, [2, 3], 'abc'))


class TestCollapse(TestCase):
    """Tests for ``collapse()``"""

    def test_collapse(self):
        l = [[1], 2, [[3], 4], [[[5]]]]
        self.assertEqual(list(mi.collapse(l)), [1, 2, 3, 4, 5])

    def test_collapse_to_string(self):
        l = [["s1"], "s2", [["s3"], "s4"], [[["s5"]]]]
        self.assertEqual(list(mi.collapse(l)), ["s1", "s2", "s3", "s4", "s5"])

    def test_collapse_to_bytes(self):
        l = [[b"s1"], b"s2", [[b"s3"], b"s4"], [[[b"s5"]]]]
        self.assertEqual(
            list(mi.collapse(l)), [b"s1", b"s2", b"s3", b"s4", b"s5"]
        )

    def test_collapse_flatten(self):
        l = [[1], [2], [[3], 4], [[[5]]]]
        self.assertEqual(list(mi.collapse(l, levels=1)), list(mi.flatten(l)))

    def test_collapse_to_level(self):
        l = [[1], 2, [[3], 4], [[[5]]]]
        self.assertEqual(list(mi.collapse(l, levels=2)), [1, 2, 3, 4, [5]])
        self.assertEqual(
            list(mi.collapse(mi.collapse(l, levels=1), levels=1)),
            list(mi.collapse(l, levels=2)),
        )

    def test_collapse_to_list(self):
        l = (1, [2], (3, [4, (5,)], 'ab'))
        g = list(mi.collapse(l, base_type=list))
        h = [1, [2], 3, [4, (5,)], 'ab']
        self.assertEqual(g, h)


class SideEffectTests(TestCase):
    """Tests for ``side_effect()``"""

    def test_individual(self):
        # The function increments the counter for each call
        g = [0]

        def func(arg):
            g[0] += 1

        h = list(mi.side_effect(func, range(10)))
        self.assertEqual(h, list(range(10)))
        self.assertEqual(g[0], 10)

    def test_chunked(self):
        # The function increments the counter for each call
        g = [0]

        def func(arg):
            g[0] += 1

        h = list(mi.side_effect(func, range(10), 2))
        self.assertEqual(h, list(range(10)))
        self.assertEqual(g[0], 5)

    def test_before_after(self):
        f = StringIO()
        j = []

        def func(item):
            print(item, file=f)
            j.append(f.getvalue())

        def it():
            yield 'a'
            yield 'b'
            raise RuntimeError('kaboom')

        h = lambda: print('HEADER', file=f)
        g = f.close

        try:
            mi.consume(mi.side_effect(func, it(), before=h, after=g))
        except RuntimeError:
            pass

        # The iterable should have been written to the file
        self.assertEqual(j, ['HEADER\na\n', 'HEADER\na\nb\n'])

        # The file should be closed even though something bad happened
        self.assertTrue(f.closed)

    def test_before_fails(self):
        f = StringIO()
        g = lambda x: print(x, file=f)

        def before():
            raise RuntimeError('ouch')

        try:
            mi.consume(
                mi.side_effect(g, 'abc', before=before, after=f.close)
            )
        except RuntimeError:
            pass

        # The file should be closed even though something bad happened in the
        # before function
        self.assertTrue(f.closed)


class SlicedTests(TestCase):
    """Tests for ``sliced()``"""

    def test_even(self):
        """Test when the length of the sequence is divisible by *n*"""
        g = 'ABCDEFGHI'
        self.assertEqual(list(mi.sliced(g, 3)), ['ABC', 'DEF', 'GHI'])

    def test_odd(self):
        """Test when the length of the sequence is not divisible by *n*"""
        g = 'ABCDEFGHI'
        self.assertEqual(list(mi.sliced(g, 4)), ['ABCD', 'EFGH', 'I'])

    def test_not_sliceable(self):
        g = (x for x in 'ABCDEFGHI')

        with self.assertRaises(TypeError):
            list(mi.sliced(g, 3))

    def test_odd_and_strict(self):
        g = [x for x in 'ABCDEFGHI']

        with self.assertRaises(ValueError):
            list(mi.sliced(g, 4, strict=True))

    def test_numpy_like_array(self):
        # Numpy arrays don't behave like Python lists - calling bool()
        # on them doesn't return False for empty lists and True for non-empty
        # ones. Emulate that behavior.
        class FalseList(list):
            def __getitem__(self, key):
                m = super().__getitem__(key)
                if isinstance(key, slice):
                    return FalseList(m)

                return m

            def __bool__(self):
                return False

        j = FalseList(range(9))
        g = list(mi.sliced(j, 3))
        h = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
        self.assertEqual(g, h)


class SplitAtTests(TestCase):
    def test_basic(self):
        for iterable, separator in [
            ('a,bb,ccc,dddd', ','),
            (',a,bb,ccc,dddd', ','),
            ('a,bb,ccc,dddd,', ','),
            ('a,bb,ccc,,dddd', ','),
            ('', ','),
            (',', ','),
            ('a,bb,ccc,dddd', ';'),
        ]:
            with self.subTest(iterable=iterable, separator=separator):
                j = iter(iterable)
                m = lambda x: x == separator
                g = [''.join(x) for x in mi.split_at(j, m)]
                h = iterable.split(separator)
                self.assertEqual(g, h)

    def test_maxsplit(self):
        m = 'a,bb,ccc,dddd'
        u = ','
        q = lambda x: x == u

        for o in range(-1, 4):
            with self.subTest(maxsplit=o):
                j = iter(m)
                t = mi.split_at(j, q, maxsplit=o)
                g = [''.join(x) for x in t]
                h = m.split(u, o)
                self.assertEqual(g, h)

    def test_keep_separator(self):
        o = ','
        j = lambda x: x == o

        for iterable, expected in [
            ('a,bb,ccc', ['a', ',', 'bb', ',', 'ccc']),
            (',a,bb,ccc', ['', ',', 'a', ',', 'bb', ',', 'ccc']),
            ('a,bb,ccc,', ['a', ',', 'bb', ',', 'ccc', ',', '']),
        ]:
            with self.subTest(iterable=iterable):
                h = iter(iterable)
                m = mi.split_at(h, j, keep_separator=True)
                g = [''.join(x) for x in m]
                self.assertEqual(g, expected)

    def test_combination(self):
        j = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        m = lambda x: x % 3 == 0
        g = list(
            mi.split_at(j, m, maxsplit=2, keep_separator=True)
        )
        h = [[1, 2], [3], [4, 5], [6], [7, 8, 9, 10]]
        self.assertEqual(g, h)


class SplitBeforeTest(TestCase):
    """Tests for ``split_before()``"""

    def test_starts_with_sep(self):
        g = list(mi.split_before('xooxoo', lambda c: c == 'x'))
        h = [['x', 'o', 'o'], ['x', 'o', 'o']]
        self.assertEqual(g, h)

    def test_ends_with_sep(self):
        g = list(mi.split_before('ooxoox', lambda c: c == 'x'))
        h = [['o', 'o'], ['x', 'o', 'o'], ['x']]
        self.assertEqual(g, h)

    def test_no_sep(self):
        g = list(mi.split_before('ooo', lambda c: c == 'x'))
        h = [['o', 'o', 'o']]
        self.assertEqual(g, h)

    def test_empty_collection(self):
        g = list(mi.split_before([], lambda c: bool(c)))
        h = []
        self.assertEqual(g, h)

    def test_max_split(self):
        for args, expected in [
            (
                ('a,b,c,d', lambda c: c == ',', -1),
                [['a'], [',', 'b'], [',', 'c'], [',', 'd']],
            ),
            (
                ('a,b,c,d', lambda c: c == ',', 0),
                [['a', ',', 'b', ',', 'c', ',', 'd']],
            ),
            (
                ('a,b,c,d', lambda c: c == ',', 1),
                [['a'], [',', 'b', ',', 'c', ',', 'd']],
            ),
            (
                ('a,b,c,d', lambda c: c == ',', 2),
                [['a'], [',', 'b'], [',', 'c', ',', 'd']],
            ),
            (
                ('a,b,c,d', lambda c: c == ',', 10),
                [['a'], [',', 'b'], [',', 'c'], [',', 'd']],
            ),
            (
                ('a,b,c,d', lambda c: c == '@', 2),
                [['a', ',', 'b', ',', 'c', ',', 'd']],
            ),
            (
                ('a,b,c,d', lambda c: c != ',', 2),
                [['a', ','], ['b', ','], ['c', ',', 'd']],
            ),
        ]:
            g = list(mi.split_before(*args))
            self.assertEqual(g, expected)


class SplitAfterTest(TestCase):
    """Tests for ``split_after()``"""

    def test_starts_with_sep(self):
        g = list(mi.split_after('xooxoo', lambda c: c == 'x'))
        h = [['x'], ['o', 'o', 'x'], ['o', 'o']]
        self.assertEqual(g, h)

    def test_ends_with_sep(self):
        g = list(mi.split_after('ooxoox', lambda c: c == 'x'))
        h = [['o', 'o', 'x'], ['o', 'o', 'x']]
        self.assertEqual(g, h)

    def test_no_sep(self):
        g = list(mi.split_after('ooo', lambda c: c == 'x'))
        h = [['o', 'o', 'o']]
        self.assertEqual(g, h)

    def test_max_split(self):
        for args, expected in [
            (
                ('a,b,c,d', lambda c: c == ',', -1),
                [['a', ','], ['b', ','], ['c', ','], ['d']],
            ),
            (
                ('a,b,c,d', lambda c: c == ',', 0),
                [['a', ',', 'b', ',', 'c', ',', 'd']],
            ),
            (
                ('a,b,c,d', lambda c: c == ',', 1),
                [['a', ','], ['b', ',', 'c', ',', 'd']],
            ),
            (
                ('a,b,c,d', lambda c: c == ',', 2),
                [['a', ','], ['b', ','], ['c', ',', 'd']],
            ),
            (
                ('a,b,c,d', lambda c: c == ',', 10),
                [['a', ','], ['b', ','], ['c', ','], ['d']],
            ),
            (
                ('a,b,c,d', lambda c: c == '@', 2),
                [['a', ',', 'b', ',', 'c', ',', 'd']],
            ),
            (
                ('a,b,c,d', lambda c: c != ',', 2),
                [['a'], [',', 'b'], [',', 'c', ',', 'd']],
            ),
            (
                ([1], lambda x: x == 1, 1),
                [[1]],
            ),
        ]:
            g = list(mi.split_after(*args))
            self.assertEqual(g, expected)


class SplitWhenTests(TestCase):
    """Tests for ``split_when()``"""

    @staticmethod
    def _split_when_before(iterable, pred):
        return mi.split_when(iterable, lambda _, c: pred(c))

    @staticmethod
    def _split_when_after(iterable, pred):
        return mi.split_when(iterable, lambda c, _: pred(c))

    # split_before emulation
    def test_before_emulation_starts_with_sep(self):
        g = list(self._split_when_before('xooxoo', lambda c: c == 'x'))
        h = [['x', 'o', 'o'], ['x', 'o', 'o']]
        self.assertEqual(g, h)

    def test_before_emulation_ends_with_sep(self):
        g = list(self._split_when_before('ooxoox', lambda c: c == 'x'))
        h = [['o', 'o'], ['x', 'o', 'o'], ['x']]
        self.assertEqual(g, h)

    def test_before_emulation_no_sep(self):
        g = list(self._split_when_before('ooo', lambda c: c == 'x'))
        h = [['o', 'o', 'o']]
        self.assertEqual(g, h)

    # split_after emulation
    def test_after_emulation_starts_with_sep(self):
        g = list(self._split_when_after('xooxoo', lambda c: c == 'x'))
        h = [['x'], ['o', 'o', 'x'], ['o', 'o']]
        self.assertEqual(g, h)

    def test_after_emulation_ends_with_sep(self):
        g = list(self._split_when_after('ooxoox', lambda c: c == 'x'))
        h = [['o', 'o', 'x'], ['o', 'o', 'x']]
        self.assertEqual(g, h)

    def test_after_emulation_no_sep(self):
        g = list(self._split_when_after('ooo', lambda c: c == 'x'))
        h = [['o', 'o', 'o']]
        self.assertEqual(g, h)

    # edge cases
    def test_empty_iterable(self):
        g = list(mi.split_when('', lambda a, b: a != b))
        h = []
        self.assertEqual(g, h)

    def test_one_element(self):
        g = list(mi.split_when('o', lambda a, b: a == b))
        h = [['o']]
        self.assertEqual(g, h)

    def test_one_element_is_second_item(self):
        g = list(self._split_when_before('x', lambda c: c == 'x'))
        h = [['x']]
        self.assertEqual(g, h)

    def test_one_element_is_first_item(self):
        g = list(self._split_when_after('x', lambda c: c == 'x'))
        h = [['x']]
        self.assertEqual(g, h)

    def test_max_split(self):
        for args, expected in [
            (
                ('a,b,c,d', lambda a, _: a == ',', -1),
                [['a', ','], ['b', ','], ['c', ','], ['d']],
            ),
            (
                ('a,b,c,d', lambda a, _: a == ',', 0),
                [['a', ',', 'b', ',', 'c', ',', 'd']],
            ),
            (
                ('a,b,c,d', lambda _, b: b == ',', 1),
                [['a'], [',', 'b', ',', 'c', ',', 'd']],
            ),
            (
                ('a,b,c,d', lambda a, _: a == ',', 2),
                [['a', ','], ['b', ','], ['c', ',', 'd']],
            ),
            (
                ('0124376', lambda a, b: a > b, -1),
                [['0', '1', '2', '4'], ['3', '7'], ['6']],
            ),
            (
                ('0124376', lambda a, b: a > b, 0),
                [['0', '1', '2', '4', '3', '7', '6']],
            ),
            (
                ('0124376', lambda a, b: a > b, 1),
                [['0', '1', '2', '4'], ['3', '7', '6']],
            ),
            (
                ('0124376', lambda a, b: a > b, 2),
                [['0', '1', '2', '4'], ['3', '7'], ['6']],
            ),
        ]:
            g = list(mi.split_when(*args))
            self.assertEqual(g, expected, str(args))


class SplitIntoTests(TestCase):
    """Tests for ``split_into()``"""

    def test_iterable_just_right(self):
        """Size of ``iterable`` equals the sum of ``sizes``."""
        j = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = [2, 3, 4]
        h = [[1, 2], [3, 4, 5], [6, 7, 8, 9]]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_iterable_too_small(self):
        """Size of ``iterable`` is smaller than sum of ``sizes``. Last return
        list is shorter as a result."""
        j = [1, 2, 3, 4, 5, 6, 7]
        m = [2, 3, 4]
        h = [[1, 2], [3, 4, 5], [6, 7]]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_iterable_too_small_extra(self):
        """Size of ``iterable`` is smaller than sum of ``sizes``. Second last
        return list is shorter and last return list is empty as a result."""
        j = [1, 2, 3, 4, 5, 6, 7]
        m = [2, 3, 4, 5]
        h = [[1, 2], [3, 4, 5], [6, 7], []]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_iterable_too_large(self):
        """Size of ``iterable`` is larger than sum of ``sizes``. Not all
        items of iterable are returned."""
        j = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = [2, 3, 2]
        h = [[1, 2], [3, 4, 5], [6, 7]]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_using_none_with_leftover(self):
        """Last item of ``sizes`` is None when items still remain in
        ``iterable``. Last list returned stretches to fit all remaining items
        of ``iterable``."""
        j = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = [2, 3, None]
        h = [[1, 2], [3, 4, 5], [6, 7, 8, 9]]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_using_none_without_leftover(self):
        """Last item of ``sizes`` is None when no items remain in
        ``iterable``. Last list returned is empty."""
        j = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = [2, 3, 4, None]
        h = [[1, 2], [3, 4, 5], [6, 7, 8, 9], []]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_using_none_mid_sizes(self):
        """None is present in ``sizes`` but is not the last item. Last list
        returned stretches to fit all remaining items of ``iterable`` but
        all items in ``sizes`` after None are ignored."""
        j = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = [2, 3, None, 4]
        h = [[1, 2], [3, 4, 5], [6, 7, 8, 9]]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_iterable_empty(self):
        """``iterable`` argument is empty but ``sizes`` is not. An empty
        list is returned for each item in ``sizes``."""
        j = []
        m = [2, 4, 2]
        h = [[], [], []]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_iterable_empty_using_none(self):
        """``iterable`` argument is empty but ``sizes`` is not. An empty
        list is returned for each item in ``sizes`` that is not after a
        None item."""
        j = []
        m = [2, 4, None, 2]
        h = [[], [], []]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_sizes_empty(self):
        """``sizes`` argument is empty but ``iterable`` is not. An empty
        generator is returned."""
        j = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = []
        h = []
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_both_empty(self):
        """Both ``sizes`` and ``iterable`` arguments are empty. An empty
        generator is returned."""
        j = []
        m = []
        h = []
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_bool_in_sizes(self):
        """A bool object is present in ``sizes`` is treated as a 1 or 0 for
        ``True`` or ``False`` due to bool being an instance of int."""
        j = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = [3, True, 2, False]
        h = [[1, 2, 3], [4], [5, 6], []]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_invalid_in_sizes(self):
        """A ValueError is raised if an object in ``sizes`` is neither ``None``
        or an integer."""
        g = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        h = [1, [], 3]
        with self.assertRaises(ValueError):
            list(mi.split_into(g, h))

    def test_invalid_in_sizes_after_none(self):
        """A item in ``sizes`` that is invalid will not raise a TypeError if it
        comes after a ``None`` item."""
        j = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = [3, 4, None, []]
        h = [[1, 2, 3], [4, 5, 6, 7], [8, 9]]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

    def test_generator_iterable_integrity(self):
        """Check that if ``iterable`` is an iterator, it is consumed only by as
        many items as the sum of ``sizes``."""
        j = (i for i in range(10))
        q = [2, 3]

        h = [[0, 1], [2, 3, 4]]
        g = list(mi.split_into(j, q))
        self.assertEqual(g, h)

        o = [5, 6, 7, 8, 9]
        m = list(j)
        self.assertEqual(m, o)

    def test_generator_sizes_integrity(self):
        """Check that if ``sizes`` is an iterator, it is consumed only until a
        ``None`` item is reached"""
        j = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = (i for i in [1, 2, None, 3, 4])

        h = [[1], [2, 3], [4, 5, 6, 7, 8, 9]]
        g = list(mi.split_into(j, m))
        self.assertEqual(g, h)

        q = [3, 4]
        o = list(m)
        self.assertEqual(o, q)


class PaddedTest(TestCase):
    """Tests for ``padded()``"""

    def test_no_n(self):
        g = [1, 2, 3]

        # No fillvalue
        self.assertEqual(mi.take(5, mi.padded(g)), [1, 2, 3, None, None])

        # With fillvalue
        self.assertEqual(
            mi.take(5, mi.padded(g, fillvalue='')), [1, 2, 3, '', '']
        )

    def test_invalid_n(self):
        self.assertRaises(ValueError, lambda: list(mi.padded([1, 2, 3], n=-1)))
        self.assertRaises(ValueError, lambda: list(mi.padded([1, 2, 3], n=0)))

    def test_valid_n(self):
        g = [1, 2, 3, 4, 5]

        # No need for padding: len(seq) <= n
        self.assertEqual(list(mi.padded(g, n=4)), [1, 2, 3, 4, 5])
        self.assertEqual(list(mi.padded(g, n=5)), [1, 2, 3, 4, 5])

        # No fillvalue
        self.assertEqual(
            list(mi.padded(g, n=7)), [1, 2, 3, 4, 5, None, None]
        )

        # With fillvalue
        self.assertEqual(
            list(mi.padded(g, fillvalue='', n=7)), [1, 2, 3, 4, 5, '', '']
        )

    def test_next_multiple(self):
        g = [1, 2, 3, 4, 5, 6]

        # No need for padding: len(seq) % n == 0
        self.assertEqual(
            list(mi.padded(g, n=3, next_multiple=True)), [1, 2, 3, 4, 5, 6]
        )

        # Padding needed: len(seq) < n
        self.assertEqual(
            list(mi.padded(g, n=8, next_multiple=True)),
            [1, 2, 3, 4, 5, 6, None, None],
        )

        # No padding needed: len(seq) == n
        self.assertEqual(
            list(mi.padded(g, n=6, next_multiple=True)), [1, 2, 3, 4, 5, 6]
        )

        # Padding needed: len(seq) > n
        self.assertEqual(
            list(mi.padded(g, n=4, next_multiple=True)),
            [1, 2, 3, 4, 5, 6, None, None],
        )

        # With fillvalue
        self.assertEqual(
            list(mi.padded(g, fillvalue='', n=4, next_multiple=True)),
            [1, 2, 3, 4, 5, 6, '', ''],
        )


class RepeatEachTests(TestCase):
    """Tests for repeat_each()"""

    def test_default(self):
        g = list(mi.repeat_each('ABC'))
        h = ['A', 'A', 'B', 'B', 'C', 'C']
        self.assertEqual(g, h)

    def test_basic(self):
        g = list(mi.repeat_each('ABC', 3))
        h = ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C']
        self.assertEqual(g, h)

    def test_empty(self):
        g = list(mi.repeat_each(''))
        h = []
        self.assertEqual(g, h)

    def test_no_repeat(self):
        g = list(mi.repeat_each('ABC', 0))
        h = []
        self.assertEqual(g, h)

    def test_negative_repeat(self):
        g = list(mi.repeat_each('ABC', -1))
        h = []
        self.assertEqual(g, h)

    def test_infinite_input(self):
        j = mi.repeat_each(cycle('AB'))
        g = mi.take(6, j)
        h = ['A', 'A', 'B', 'B', 'A', 'A']
        self.assertEqual(g, h)


class RepeatLastTests(TestCase):
    def test_empty_iterable(self):
        m = 3
        j = iter([])
        g = mi.take(m, mi.repeat_last(j))
        h = [None] * m
        self.assertEqual(g, h)

    def test_default_value(self):
        o = 3
        m = iter([])
        h = '3'
        g = mi.take(o, mi.repeat_last(m, h))
        j = ['3'] * o
        self.assertEqual(g, j)

    def test_basic(self):
        m = 10
        j = (str(x) for x in range(5))
        g = mi.take(m, mi.repeat_last(j))
        h = ['0', '1', '2', '3', '4', '4', '4', '4', '4', '4']
        self.assertEqual(g, h)


class DistributeTest(TestCase):
    """Tests for distribute()"""

    def test_invalid_n(self):
        self.assertRaises(ValueError, lambda: mi.distribute(-1, [1, 2, 3]))
        self.assertRaises(ValueError, lambda: mi.distribute(0, [1, 2, 3]))

    def test_basic(self):
        g = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        for n, expected in [
            (1, [g]),
            (2, [[1, 3, 5, 7, 9], [2, 4, 6, 8, 10]]),
            (3, [[1, 4, 7, 10], [2, 5, 8], [3, 6, 9]]),
            (10, [[n] for n in range(1, 10 + 1)]),
        ]:
            self.assertEqual(
                [list(x) for x in mi.distribute(n, g)], expected
            )

    def test_large_n(self):
        g = [1, 2, 3, 4]
        self.assertEqual(
            [list(x) for x in mi.distribute(6, g)],
            [[1], [2], [3], [4], [], []],
        )


class StaggerTest(TestCase):
    """Tests for ``stagger()``"""

    def test_default(self):
        j = [0, 1, 2, 3]
        g = list(mi.stagger(j))
        h = [(None, 0, 1), (0, 1, 2), (1, 2, 3)]
        self.assertEqual(g, h)

    def test_offsets(self):
        h = [0, 1, 2, 3]
        for offsets, expected in [
            ((-2, 0, 2), [('', 0, 2), ('', 1, 3)]),
            ((-2, -1), [('', ''), ('', 0), (0, 1), (1, 2), (2, 3)]),
            ((1, 2), [(1, 2), (2, 3)]),
        ]:
            g = mi.stagger(h, offsets=offsets, fillvalue='')
            self.assertEqual(list(g), expected)

    def test_longest(self):
        h = [0, 1, 2, 3]
        for offsets, expected in [
            (
                (-1, 0, 1),
                [('', 0, 1), (0, 1, 2), (1, 2, 3), (2, 3, ''), (3, '', '')],
            ),
            ((-2, -1), [('', ''), ('', 0), (0, 1), (1, 2), (2, 3), (3, '')]),
            ((1, 2), [(1, 2), (2, 3), (3, '')]),
        ]:
            g = mi.stagger(
                h, offsets=offsets, fillvalue='', longest=True
            )
            self.assertEqual(list(g), expected)


class ZipOffsetTest(TestCase):
    """Tests for ``zip_offset()``"""

    def test_shortest(self):
        g = [0, 1, 2, 3]
        h = [0, 1, 2, 3, 4, 5]
        j = [0, 1, 2, 3, 4, 5, 6, 7]
        m = list(
            mi.zip_offset(g, h, j, offsets=(-1, 0, 1), fillvalue='')
        )
        o = [('', 0, 1), (0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]
        self.assertEqual(m, o)

    def test_longest(self):
        g = [0, 1, 2, 3]
        h = [0, 1, 2, 3, 4, 5]
        j = [0, 1, 2, 3, 4, 5, 6, 7]
        m = list(
            mi.zip_offset(g, h, j, offsets=(-1, 0, 1), longest=True)
        )
        o = [
            (None, 0, 1),
            (0, 1, 2),
            (1, 2, 3),
            (2, 3, 4),
            (3, 4, 5),
            (None, 5, 6),
            (None, None, 7),
        ]
        self.assertEqual(m, o)

    def test_mismatch(self):
        g = [0, 1, 2], [2, 3, 4]
        h = (-1, 0, 1)
        self.assertRaises(
            ValueError,
            lambda: list(mi.zip_offset(*g, offsets=h)),
        )


class UnzipTests(TestCase):
    """Tests for unzip()"""

    def test_empty_iterable(self):
        self.assertEqual(list(mi.unzip([])), [])
        # in reality zip([], [], []) is equivalent to iter([])
        # but it doesn't hurt to test both
        self.assertEqual(list(mi.unzip(zip([], [], []))), [])

    def test_length_one_iterable(self):
        xs, ys, zs = mi.unzip(zip([1], [2], [3]))
        self.assertEqual(list(xs), [1])
        self.assertEqual(list(ys), [2])
        self.assertEqual(list(zs), [3])

    def test_normal_case(self):
        xs, ys, zs = range(10), range(1, 11), range(2, 12)
        g = zip(xs, ys, zs)
        xs, ys, zs = mi.unzip(g)
        self.assertEqual(list(xs), list(range(10)))
        self.assertEqual(list(ys), list(range(1, 11)))
        self.assertEqual(list(zs), list(range(2, 12)))

    def test_improperly_zipped(self):
        g = iter([(1, 2, 3), (4, 5), (6,)])
        xs, ys, zs = mi.unzip(g)
        self.assertEqual(list(xs), [1, 4, 6])
        self.assertEqual(list(ys), [2, 5])
        self.assertEqual(list(zs), [3])

    def test_increasingly_zipped(self):
        h = iter([(1, 2), (3, 4, 5), (6, 7, 8, 9)])
        g = mi.unzip(h)
        # from the docstring:
        # len(first tuple) is the number of iterables zipped
        self.assertEqual(len(g), 2)
        xs, ys = g
        self.assertEqual(list(xs), [1, 3, 6])
        self.assertEqual(list(ys), [2, 4, 7])


class SortTogetherTest(TestCase):
    """Tests for sort_together()"""

    def test_key_list(self):
        """tests `key_list` including default, iterables include duplicates"""
        g = [
            ['GA', 'GA', 'GA', 'CT', 'CT', 'CT'],
            ['May', 'Aug.', 'May', 'June', 'July', 'July'],
            [97, 20, 100, 70, 100, 20],
        ]

        self.assertEqual(
            mi.sort_together(g),
            [
                ('CT', 'CT', 'CT', 'GA', 'GA', 'GA'),
                ('June', 'July', 'July', 'May', 'Aug.', 'May'),
                (70, 100, 20, 97, 20, 100),
            ],
        )

        self.assertEqual(
            mi.sort_together(g, key_list=(0, 1)),
            [
                ('CT', 'CT', 'CT', 'GA', 'GA', 'GA'),
                ('July', 'July', 'June', 'Aug.', 'May', 'May'),
                (100, 20, 70, 20, 97, 100),
            ],
        )

        self.assertEqual(
            mi.sort_together(g, key_list=(0, 1, 2)),
            [
                ('CT', 'CT', 'CT', 'GA', 'GA', 'GA'),
                ('July', 'July', 'June', 'Aug.', 'May', 'May'),
                (20, 100, 70, 20, 97, 100),
            ],
        )

        self.assertEqual(
            mi.sort_together(g, key_list=(2,)),
            [
                ('GA', 'CT', 'CT', 'GA', 'GA', 'CT'),
                ('Aug.', 'July', 'June', 'May', 'May', 'July'),
                (20, 20, 70, 97, 100, 100),
            ],
        )

    def test_invalid_key_list(self):
        """tests `key_list` for indexes not available in `iterables`"""
        g = [
            ['GA', 'GA', 'GA', 'CT', 'CT', 'CT'],
            ['May', 'Aug.', 'May', 'June', 'July', 'July'],
            [97, 20, 100, 70, 100, 20],
        ]

        self.assertRaises(
            IndexError, lambda: mi.sort_together(g, key_list=(5,))
        )

    def test_key_function(self):
        """tests `key` function, including interaction with `key_list`"""
        g = [
            ['GA', 'GA', 'GA', 'CT', 'CT', 'CT'],
            ['May', 'Aug.', 'May', 'June', 'July', 'July'],
            [97, 20, 100, 70, 100, 20],
        ]
        self.assertEqual(
            mi.sort_together(g, key=lambda x: x),
            [
                ('CT', 'CT', 'CT', 'GA', 'GA', 'GA'),
                ('June', 'July', 'July', 'May', 'Aug.', 'May'),
                (70, 100, 20, 97, 20, 100),
            ],
        )
        self.assertEqual(
            mi.sort_together(g, key=lambda x: x[::-1]),
            [
                ('GA', 'GA', 'GA', 'CT', 'CT', 'CT'),
                ('May', 'Aug.', 'May', 'June', 'July', 'July'),
                (97, 20, 100, 70, 100, 20),
            ],
        )
        self.assertEqual(
            mi.sort_together(
                g,
                key_list=(0, 2),
                key=lambda state, number: (
                    number if state == 'CT' else 2 * number
                ),
            ),
            [
                ('CT', 'GA', 'CT', 'CT', 'GA', 'GA'),
                ('July', 'Aug.', 'June', 'July', 'May', 'May'),
                (20, 20, 70, 100, 97, 100),
            ],
        )

    def test_reverse(self):
        """tests `reverse` to ensure a reverse sort for `key_list` iterables"""
        g = [
            ['GA', 'GA', 'GA', 'CT', 'CT', 'CT'],
            ['May', 'Aug.', 'May', 'June', 'July', 'July'],
            [97, 20, 100, 70, 100, 20],
        ]

        self.assertEqual(
            mi.sort_together(g, key_list=(0, 1, 2), reverse=True),
            [
                ('GA', 'GA', 'GA', 'CT', 'CT', 'CT'),
                ('May', 'May', 'Aug.', 'June', 'July', 'July'),
                (100, 97, 20, 70, 100, 20),
            ],
        )

    def test_uneven_iterables(self):
        """tests trimming of iterables to the shortest length before sorting"""
        g = [
            ['GA', 'GA', 'GA', 'CT', 'CT', 'CT', 'MA'],
            ['May', 'Aug.', 'May', 'June', 'July', 'July'],
            [97, 20, 100, 70, 100, 20, 0],
        ]

        self.assertEqual(
            mi.sort_together(g),
            [
                ('CT', 'CT', 'CT', 'GA', 'GA', 'GA'),
                ('June', 'July', 'July', 'May', 'Aug.', 'May'),
                (70, 100, 20, 97, 20, 100),
            ],
        )

    def test_strict(self):
        # Test for list of lists or tuples
        self.assertRaises(
            ValueError,
            lambda: mi.sort_together(
                [(4, 3, 2, 1), ('a', 'b', 'c')], strict=True
            ),
        )

        # Test for list of iterables
        self.assertRaises(
            ValueError,
            lambda: mi.sort_together([range(4), range(5)], strict=True),
        )

        # Test for iterable of iterables
        self.assertRaises(
            ValueError,
            lambda: mi.sort_together(
                (range(i) for i in range(4)), strict=True
            ),
        )


class DivideTest(TestCase):
    """Tests for divide()"""

    def test_invalid_n(self):
        self.assertRaises(ValueError, lambda: mi.divide(-1, [1, 2, 3]))
        self.assertRaises(ValueError, lambda: mi.divide(0, [1, 2, 3]))

    def test_basic(self):
        g = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        for n, expected in [
            (1, [g]),
            (2, [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]),
            (3, [[1, 2, 3, 4], [5, 6, 7], [8, 9, 10]]),
            (10, [[n] for n in range(1, 10 + 1)]),
        ]:
            self.assertEqual(
                [list(x) for x in mi.divide(n, g)], expected
            )

    def test_large_n(self):
        self.assertEqual(
            [list(x) for x in mi.divide(6, iter(range(1, 4 + 1)))],
            [[1], [2], [3], [4], [], []],
        )


class TestAlwaysIterable(TestCase):
    """Tests for always_iterable()"""

    def test_single(self):
        self.assertEqual(list(mi.always_iterable(1)), [1])

    def test_strings(self):
        for j in ['foo', b'bar', 'baz']:
            g = list(mi.always_iterable(j))
            h = [j]
            self.assertEqual(g, h)

    def test_base_type(self):
        q = {'a': 1, 'b': 2}
        w = '123'

        # Default: dicts are iterable like they normally are
        m = list(mi.always_iterable(q))
        o = list(q)
        self.assertEqual(m, o)

        # Unitary types set: dicts are not iterable
        h = list(mi.always_iterable(q, base_type=dict))
        j = [q]
        self.assertEqual(h, j)

        # With unitary types set, strings are iterable
        t = list(mi.always_iterable(w, base_type=None))
        u = list(w)
        self.assertEqual(t, u)

        # base_type handles nested tuple (via isinstance).
        g = ((dict,),)
        h = list(mi.always_iterable(q, base_type=g))
        j = [q]
        self.assertEqual(h, j)

    def test_iterables(self):
        self.assertEqual(list(mi.always_iterable([0, 1])), [0, 1])
        self.assertEqual(
            list(mi.always_iterable([0, 1], base_type=list)), [[0, 1]]
        )
        self.assertEqual(
            list(mi.always_iterable(iter('foo'))), ['f', 'o', 'o']
        )
        self.assertEqual(list(mi.always_iterable([])), [])

    def test_none(self):
        self.assertEqual(list(mi.always_iterable(None)), [])

    def test_generator(self):
        def _gen():
            yield 0
            yield 1

        self.assertEqual(list(mi.always_iterable(_gen())), [0, 1])


class AdjacentTests(TestCase):
    def test_typical(self):
        g = list(mi.adjacent(lambda x: x % 5 == 0, range(10)))
        h = [
            (True, 0),
            (True, 1),
            (False, 2),
            (False, 3),
            (True, 4),
            (True, 5),
            (True, 6),
            (False, 7),
            (False, 8),
            (False, 9),
        ]
        self.assertEqual(g, h)

    def test_empty_iterable(self):
        g = list(mi.adjacent(lambda x: x % 5 == 0, []))
        h = []
        self.assertEqual(g, h)

    def test_length_one(self):
        g = list(mi.adjacent(lambda x: x % 5 == 0, [0]))
        h = [(True, 0)]
        self.assertEqual(g, h)

        g = list(mi.adjacent(lambda x: x % 5 == 0, [1]))
        h = [(False, 1)]
        self.assertEqual(g, h)

    def test_consecutive_true(self):
        """Test that when the predicate matches multiple consecutive elements
        it doesn't repeat elements in the output"""
        g = list(mi.adjacent(lambda x: x % 5 < 2, range(10)))
        h = [
            (True, 0),
            (True, 1),
            (True, 2),
            (False, 3),
            (True, 4),
            (True, 5),
            (True, 6),
            (True, 7),
            (False, 8),
            (False, 9),
        ]
        self.assertEqual(g, h)

    def test_distance(self):
        g = list(mi.adjacent(lambda x: x % 5 == 0, range(10), distance=2))
        h = [
            (True, 0),
            (True, 1),
            (True, 2),
            (True, 3),
            (True, 4),
            (True, 5),
            (True, 6),
            (True, 7),
            (False, 8),
            (False, 9),
        ]
        self.assertEqual(g, h)

        g = list(mi.adjacent(lambda x: x % 5 == 0, range(10), distance=3))
        h = [
            (True, 0),
            (True, 1),
            (True, 2),
            (True, 3),
            (True, 4),
            (True, 5),
            (True, 6),
            (True, 7),
            (True, 8),
            (False, 9),
        ]
        self.assertEqual(g, h)

    def test_large_distance(self):
        """Test distance larger than the length of the iterable"""
        j = range(10)
        g = list(mi.adjacent(lambda x: x % 5 == 4, j, distance=20))
        h = list(zip(repeat(True), j))
        self.assertEqual(g, h)

        g = list(mi.adjacent(lambda x: False, j, distance=20))
        h = list(zip(repeat(False), j))
        self.assertEqual(g, h)

    def test_zero_distance(self):
        """Test that adjacent() reduces to zip+map when distance is 0"""
        j = range(1000)
        m = lambda x: x % 4 == 2
        g = mi.adjacent(m, j, 0)
        h = zip(map(m, j), j)
        self.assertTrue(all(a == e for a, e in zip(g, h)))

    def test_negative_distance(self):
        """Test that adjacent() raises an error with negative distance"""
        g = lambda x: x
        self.assertRaises(
            ValueError, lambda: mi.adjacent(g, range(1000), -1)
        )
        self.assertRaises(
            ValueError, lambda: mi.adjacent(g, range(10), -10)
        )

    def test_grouping(self):
        """Test interaction of adjacent() with groupby_transform()"""
        m = mi.adjacent(lambda x: x % 5 == 0, range(10))
        j = mi.groupby_transform(m, itemgetter(0), itemgetter(1))
        g = [(k, list(g)) for k, g in j]
        h = [
            (True, [0, 1]),
            (False, [2, 3]),
            (True, [4, 5, 6]),
            (False, [7, 8, 9]),
        ]
        self.assertEqual(g, h)

    def test_call_once(self):
        """Test that the predicate is only called once per item."""
        h = set()
        m = range(10)

        def predicate(item):
            self.assertNotIn(item, h)
            h.add(item)
            return True

        g = list(mi.adjacent(predicate, m))
        j = [(True, x) for x in m]
        self.assertEqual(g, j)


class GroupByTransformTests(TestCase):
    def assertAllGroupsEqual(self, groupby1, groupby2):
        for a, b in zip(groupby1, groupby2):
            key1, group1 = a
            key2, group2 = b
            self.assertEqual(key1, key2)
            self.assertListEqual(list(group1), list(group2))
        self.assertRaises(StopIteration, lambda: next(groupby1))
        self.assertRaises(StopIteration, lambda: next(groupby2))

    def test_default_funcs(self):
        j = [(x // 5, x) for x in range(1000)]
        g = mi.groupby_transform(j)
        h = groupby(j)
        self.assertAllGroupsEqual(g, h)

    def test_valuefunc(self):
        m = [(int(x / 5), int(x / 3), x) for x in range(10)]

        # Test the standard usage of grouping one iterable using another's keys
        j = mi.groupby_transform(
            m, keyfunc=itemgetter(0), valuefunc=itemgetter(-1)
        )
        g = [(k, list(g)) for k, g in j]
        h = [(0, [0, 1, 2, 3, 4]), (1, [5, 6, 7, 8, 9])]
        self.assertEqual(g, h)

        j = mi.groupby_transform(
            m, keyfunc=itemgetter(1), valuefunc=itemgetter(-1)
        )
        g = [(k, list(g)) for k, g in j]
        h = [(0, [0, 1, 2]), (1, [3, 4, 5]), (2, [6, 7, 8]), (3, [9])]
        self.assertEqual(g, h)

        # and now for something a little different
        d = dict(zip(range(10), 'abcdefghij'))
        j = mi.groupby_transform(
            range(10), keyfunc=lambda x: x // 5, valuefunc=d.get
        )
        g = [(k, ''.join(g)) for k, g in j]
        h = [(0, 'abcde'), (1, 'fghij')]
        self.assertEqual(g, h)

    def test_no_valuefunc(self):
        j = range(1000)

        def key(x):
            return x // 5

        g = mi.groupby_transform(j, key, valuefunc=None)
        h = groupby(j, key)
        self.assertAllGroupsEqual(g, h)

        g = mi.groupby_transform(j, key)  # default valuefunc
        h = groupby(j, key)
        self.assertAllGroupsEqual(g, h)

    def test_reducefunc(self):
        j = range(50)
        m = lambda k: 10 * (k // 10)
        q = lambda v: v + 1
        o = sum
        g = list(
            mi.groupby_transform(
                j,
                keyfunc=m,
                valuefunc=q,
                reducefunc=o,
            )
        )
        h = [(0, 55), (10, 155), (20, 255), (30, 355), (40, 455)]
        self.assertEqual(g, h)


class NumericRangeTests(TestCase):
    def test_basic(self):
        for args, expected in [
            ((4,), [0, 1, 2, 3]),
            ((4.0,), [0.0, 1.0, 2.0, 3.0]),
            ((1.0, 4), [1.0, 2.0, 3.0]),
            ((1, 4.0), [1.0, 2.0, 3.0]),
            ((1.0, 5), [1.0, 2.0, 3.0, 4.0]),
            ((0, 20, 5), [0, 5, 10, 15]),
            ((0, 20, 5.0), [0.0, 5.0, 10.0, 15.0]),
            ((0, 10, 3), [0, 3, 6, 9]),
            ((0, 10, 3.0), [0.0, 3.0, 6.0, 9.0]),
            ((0, -5, -1), [0, -1, -2, -3, -4]),
            ((0.0, -5, -1), [0.0, -1.0, -2.0, -3.0, -4.0]),
            ((1, 2, Fraction(1, 2)), [Fraction(1, 1), Fraction(3, 2)]),
            ((0,), []),
            ((0.0,), []),
            ((1, 0), []),
            ((1.0, 0.0), []),
            ((0.1, 0.30000000000000001, 0.2), [0.1]),  # IEE 754 !
            (
                (
                    Decimal("0.1"),
                    Decimal("0.30000000000000001"),
                    Decimal("0.2"),
                ),
                [Decimal("0.1"), Decimal("0.3")],
            ),  # okay with Decimal
            (
                (
                    Fraction(1, 10),
                    Fraction(30000000000000001, 100000000000000000),
                    Fraction(2, 10),
                ),
                [Fraction(1, 10), Fraction(3, 10)],
            ),  # okay with Fraction
            ((Fraction(2, 1),), [Fraction(0, 1), Fraction(1, 1)]),
            ((Decimal('2.0'),), [Decimal('0.0'), Decimal('1.0')]),
            (
                (
                    datetime(2019, 3, 29, 12, 34, 56),
                    datetime(2019, 3, 29, 12, 37, 55),
                    timedelta(minutes=1),
                ),
                [
                    datetime(2019, 3, 29, 12, 34, 56),
                    datetime(2019, 3, 29, 12, 35, 56),
                    datetime(2019, 3, 29, 12, 36, 56),
                ],
            ),
        ]:
            g = list(mi.numeric_range(*args))
            self.assertEqual(expected, g)
            self.assertTrue(
                all(type(a) is type(e) for a, e in zip(g, expected))
            )

    def test_arg_count(self):
        for args, message in [
            ((), 'numeric_range expected at least 1 argument, got 0'),
            (
                (0, 1, 2, 3),
                'numeric_range expected at most 3 arguments, got 4',
            ),
        ]:
            with self.assertRaisesRegex(TypeError, message):
                mi.numeric_range(*args)

    def test_zero_step(self):
        for g in [
            (1, 2, 0),
            (
                datetime(2019, 3, 29, 12, 34, 56),
                datetime(2019, 3, 29, 12, 37, 55),
                timedelta(minutes=0),
            ),
            (1.0, 2.0, 0.0),
            (Decimal("1.0"), Decimal("2.0"), Decimal("0.0")),
            (Fraction(2, 2), Fraction(4, 2), Fraction(0, 2)),
        ]:
            with self.assertRaises(ValueError):
                list(mi.numeric_range(*g))

    def test_bool(self):
        for args, expected in [
            ((1.0, 3.0, 1.5), True),
            ((1.0, 2.0, 1.5), True),
            ((1.0, 1.0, 1.5), False),
            ((1.0, 0.0, 1.5), False),
            ((3.0, 1.0, -1.5), True),
            ((2.0, 1.0, -1.5), True),
            ((1.0, 1.0, -1.5), False),
            ((0.0, 1.0, -1.5), False),
            ((Decimal("1.0"), Decimal("2.0"), Decimal("1.5")), True),
            ((Decimal("1.0"), Decimal("0.0"), Decimal("1.5")), False),
            ((Fraction(2, 2), Fraction(4, 2), Fraction(3, 2)), True),
            ((Fraction(2, 2), Fraction(0, 2), Fraction(3, 2)), False),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=1),
                ),
                True,
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 28),
                    timedelta(hours=1),
                ),
                False,
            ),
        ]:
            self.assertEqual(expected, bool(mi.numeric_range(*args)))

    def test_contains(self):
        for args, expected_in, expected_not_in in [
            ((10,), range(10), (0.5,)),
            ((1.0, 9.9, 1.5), (1.0, 2.5, 4.0, 5.5, 7.0, 8.5), (0.9,)),
            ((9.0, 1.0, -1.5), (1.5, 3.0, 4.5, 6.0, 7.5, 9.0), (0.0, 0.9)),
            (
                (Decimal("1.0"), Decimal("9.9"), Decimal("1.5")),
                (
                    Decimal("1.0"),
                    Decimal("2.5"),
                    Decimal("4.0"),
                    Decimal("5.5"),
                    Decimal("7.0"),
                    Decimal("8.5"),
                ),
                (Decimal("0.9"),),
            ),
            (
                (Fraction(0, 1), Fraction(5, 1), Fraction(1, 2)),
                (Fraction(0, 1), Fraction(1, 2), Fraction(9, 2)),
                (Fraction(10, 2),),
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=1),
                ),
                (datetime(2019, 3, 29, 15),),
                (datetime(2019, 3, 29, 15, 30),),
            ),
        ]:
            r = mi.numeric_range(*args)
            for v in expected_in:
                self.assertTrue(v in r)
                self.assertFalse(v not in r)

            for v in expected_not_in:
                self.assertFalse(v in r)
                self.assertTrue(v not in r)

    def test_eq(self):
        for args1, args2 in [
            ((0, 5, 2), (0, 6, 2)),
            ((1.0, 9.9, 1.5), (1.0, 8.6, 1.5)),
            ((8.5, 0.0, -1.5), (8.5, 0.7, -1.5)),
            ((7.0, 0.0, 1.0), (17.0, 7.0, 0.5)),
            (
                (Decimal("1.0"), Decimal("9.9"), Decimal("1.5")),
                (Decimal("1.0"), Decimal("8.6"), Decimal("1.5")),
            ),
            (
                (Fraction(1, 1), Fraction(10, 1), Fraction(3, 2)),
                (Fraction(1, 1), Fraction(9, 1), Fraction(3, 2)),
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30, 1),
                    timedelta(hours=10),
                ),
            ),
        ]:
            self.assertEqual(
                mi.numeric_range(*args1), mi.numeric_range(*args2)
            )

        for args1, args2 in [
            ((0, 5, 2), (0, 7, 2)),
            ((1.0, 9.9, 1.5), (1.2, 9.9, 1.5)),
            ((1.0, 9.9, 1.5), (1.0, 10.3, 1.5)),
            ((1.0, 9.9, 1.5), (1.0, 9.9, 1.4)),
            ((8.5, 0.0, -1.5), (8.4, 0.0, -1.5)),
            ((8.5, 0.0, -1.5), (8.5, -0.7, -1.5)),
            ((8.5, 0.0, -1.5), (8.5, 0.0, -1.4)),
            ((0.0, 7.0, 1.0), (7.0, 0.0, 1.0)),
            (
                (Decimal("1.0"), Decimal("10.0"), Decimal("1.5")),
                (Decimal("1.0"), Decimal("10.5"), Decimal("1.5")),
            ),
            (
                (Fraction(1, 1), Fraction(10, 1), Fraction(3, 2)),
                (Fraction(1, 1), Fraction(21, 2), Fraction(3, 2)),
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30, 15),
                    timedelta(hours=10),
                ),
            ),
        ]:
            self.assertNotEqual(
                mi.numeric_range(*args1), mi.numeric_range(*args2)
            )

        self.assertNotEqual(mi.numeric_range(7.0), 1)
        self.assertNotEqual(mi.numeric_range(7.0), "abc")

    def test_get_item_by_index(self):
        for args, index, expected in [
            ((1, 6), 2, 3),
            ((1.0, 6.0, 1.5), 0, 1.0),
            ((1.0, 6.0, 1.5), 1, 2.5),
            ((1.0, 6.0, 1.5), 2, 4.0),
            ((1.0, 6.0, 1.5), 3, 5.5),
            ((1.0, 6.0, 1.5), -1, 5.5),
            ((1.0, 6.0, 1.5), -2, 4.0),
            (
                (Decimal("1.0"), Decimal("9.0"), Decimal("1.5")),
                -1,
                Decimal("8.5"),
            ),
            (
                (Fraction(1, 1), Fraction(10, 1), Fraction(3, 2)),
                2,
                Fraction(4, 1),
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                1,
                datetime(2019, 3, 29, 10),
            ),
        ]:
            self.assertEqual(expected, mi.numeric_range(*args)[index])

        for args, index in [
            ((1.0, 6.0, 1.5), 4),
            ((1.0, 6.0, 1.5), -5),
            ((6.0, 1.0, 1.5), 0),
            ((6.0, 1.0, 1.5), -1),
            ((Decimal("1.0"), Decimal("9.0"), Decimal("-1.5")), -1),
            ((Fraction(1, 1), Fraction(2, 1), Fraction(3, 2)), 2),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                8,
            ),
        ]:
            with self.assertRaises(IndexError):
                mi.numeric_range(*args)[index]

    def test_get_item_by_slice(self):
        for args, sl, expected_args in [
            ((1.0, 9.0, 1.5), slice(None, None, None), (1.0, 9.0, 1.5)),
            ((1.0, 9.0, 1.5), slice(None, 1, None), (1.0, 2.5, 1.5)),
            ((1.0, 9.0, 1.5), slice(None, None, 2), (1.0, 9.0, 3.0)),
            ((1.0, 9.0, 1.5), slice(None, 2, None), (1.0, 4.0, 1.5)),
            ((1.0, 9.0, 1.5), slice(1, 2, None), (2.5, 4.0, 1.5)),
            ((1.0, 9.0, 1.5), slice(1, -1, None), (2.5, 8.5, 1.5)),
            ((1.0, 9.0, 1.5), slice(10, None, 3), (9.0, 9.0, 4.5)),
            ((1.0, 9.0, 1.5), slice(-10, None, 3), (1.0, 9.0, 4.5)),
            ((1.0, 9.0, 1.5), slice(None, -10, 3), (1.0, 1.0, 4.5)),
            ((1.0, 9.0, 1.5), slice(None, 10, 3), (1.0, 9.0, 4.5)),
            (
                (Decimal("1.0"), Decimal("9.0"), Decimal("1.5")),
                slice(1, -1, None),
                (Decimal("2.5"), Decimal("8.5"), Decimal("1.5")),
            ),
            (
                (Fraction(1, 1), Fraction(5, 1), Fraction(3, 2)),
                slice(1, -1, None),
                (Fraction(5, 2), Fraction(4, 1), Fraction(3, 2)),
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                slice(1, -1, None),
                (
                    datetime(2019, 3, 29, 10),
                    datetime(2019, 3, 29, 20),
                    timedelta(hours=10),
                ),
            ),
        ]:
            self.assertEqual(
                mi.numeric_range(*expected_args), mi.numeric_range(*args)[sl]
            )

    def test_hash(self):
        for args, expected in [
            ((1.0, 6.0, 1.5), hash((1.0, 5.5, 1.5))),
            ((1.0, 7.0, 1.5), hash((1.0, 5.5, 1.5))),
            ((1.0, 7.5, 1.5), hash((1.0, 7.0, 1.5))),
            ((1.0, 1.5, 1.5), hash((1.0, 1.0, 1.5))),
            ((1.5, 1.0, 1.5), hash(range(0, 0))),
            ((1.5, 1.5, 1.5), hash(range(0, 0))),
            (
                (Decimal("1.0"), Decimal("9.0"), Decimal("1.5")),
                hash((Decimal("1.0"), Decimal("8.5"), Decimal("1.5"))),
            ),
            (
                (Fraction(1, 1), Fraction(5, 1), Fraction(3, 2)),
                hash((Fraction(1, 1), Fraction(4, 1), Fraction(3, 2))),
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                hash(
                    (
                        datetime(2019, 3, 29),
                        datetime(2019, 3, 29, 20),
                        timedelta(hours=10),
                    )
                ),
            ),
        ]:
            self.assertEqual(expected, hash(mi.numeric_range(*args)))

    def test_iter_twice(self):
        g = mi.numeric_range(1.0, 9.9, 1.5)
        h = mi.numeric_range(8.5, 0.0, -1.5)
        self.assertEqual([1.0, 2.5, 4.0, 5.5, 7.0, 8.5], list(g))
        self.assertEqual([1.0, 2.5, 4.0, 5.5, 7.0, 8.5], list(g))
        self.assertEqual([8.5, 7.0, 5.5, 4.0, 2.5, 1.0], list(h))
        self.assertEqual([8.5, 7.0, 5.5, 4.0, 2.5, 1.0], list(h))

    def test_len(self):
        for args, expected in [
            ((1.0, 7.0, 1.5), 4),
            ((1.0, 7.01, 1.5), 5),
            ((7.0, 1.0, -1.5), 4),
            ((7.01, 1.0, -1.5), 5),
            ((0.1, 0.30000000000000001, 0.2), 1),  # IEE 754 !
            (
                (
                    Decimal("0.1"),
                    Decimal("0.30000000000000001"),
                    Decimal("0.2"),
                ),
                2,
            ),  # works with Decimal
            ((Decimal("1.0"), Decimal("9.0"), Decimal("1.5")), 6),
            ((Fraction(1, 1), Fraction(5, 1), Fraction(3, 2)), 3),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                3,
            ),
        ]:
            self.assertEqual(expected, len(mi.numeric_range(*args)))

    def test_repr(self):
        for args, *expected in [
            ((7.0,), "numeric_range(0.0, 7.0)"),
            ((1.0, 7.0), "numeric_range(1.0, 7.0)"),
            ((7.0, 1.0, -1.5), "numeric_range(7.0, 1.0, -1.5)"),
            (
                (Decimal("1.0"), Decimal("9.0"), Decimal("1.5")),
                (
                    "numeric_range(Decimal('1.0'), Decimal('9.0'), "
                    "Decimal('1.5'))"
                ),
            ),
            (
                (Fraction(7, 7), Fraction(10, 2), Fraction(3, 2)),
                (
                    "numeric_range(Fraction(1, 1), Fraction(5, 1), "
                    "Fraction(3, 2))"
                ),
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                "numeric_range(datetime.datetime(2019, 3, 29, 0, 0), "
                "datetime.datetime(2019, 3, 30, 0, 0), "
                "datetime.timedelta(seconds=36000))",
                "numeric_range(datetime.datetime(2019, 3, 29, 0, 0), "
                "datetime.datetime(2019, 3, 30, 0, 0), "
                "datetime.timedelta(0, 36000))",
            ),
        ]:
            with self.subTest(args=args):
                self.assertIn(repr(mi.numeric_range(*args)), expected)

    def test_reversed(self):
        for args, expected in [
            ((7.0,), [6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0]),
            ((1.0, 7.0), [6.0, 5.0, 4.0, 3.0, 2.0, 1.0]),
            ((7.0, 1.0, -1.5), [2.5, 4.0, 5.5, 7.0]),
            ((7.0, 0.9, -1.5), [1.0, 2.5, 4.0, 5.5, 7.0]),
            (
                (Decimal("1.0"), Decimal("5.0"), Decimal("1.5")),
                [Decimal('4.0'), Decimal('2.5'), Decimal('1.0')],
            ),
            (
                (Fraction(1, 1), Fraction(5, 1), Fraction(3, 2)),
                [Fraction(4, 1), Fraction(5, 2), Fraction(1, 1)],
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                [
                    datetime(2019, 3, 29, 20),
                    datetime(2019, 3, 29, 10),
                    datetime(2019, 3, 29),
                ],
            ),
        ]:
            self.assertEqual(expected, list(reversed(mi.numeric_range(*args))))

    def test_count(self):
        for args, v, c in [
            ((7.0,), 0.0, 1),
            ((7.0,), 0.5, 0),
            ((7.0,), 6.0, 1),
            ((7.0,), 7.0, 0),
            ((7.0,), 10.0, 0),
            (
                (Decimal("1.0"), Decimal("5.0"), Decimal("1.5")),
                Decimal('4.0'),
                1,
            ),
            (
                (Fraction(1, 1), Fraction(5, 1), Fraction(3, 2)),
                Fraction(5, 2),
                1,
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                datetime(2019, 3, 29, 20),
                1,
            ),
        ]:
            self.assertEqual(c, mi.numeric_range(*args).count(v))

    def test_index(self):
        for args, v, i in [
            ((7.0,), 0.0, 0),
            ((7.0,), 6.0, 6),
            ((7.0, 0.0, -1.0), 7.0, 0),
            ((7.0, 0.0, -1.0), 1.0, 6),
            (
                (Decimal("1.0"), Decimal("5.0"), Decimal("1.5")),
                Decimal('4.0'),
                2,
            ),
            (
                (Fraction(1, 1), Fraction(5, 1), Fraction(3, 2)),
                Fraction(5, 2),
                1,
            ),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                datetime(2019, 3, 29, 20),
                2,
            ),
        ]:
            self.assertEqual(i, mi.numeric_range(*args).index(v))

        for args, v in [
            ((0.7,), 0.5),
            ((0.7,), 7.0),
            ((0.7,), 10.0),
            ((7.0, 0.0, -1.0), 0.5),
            ((7.0, 0.0, -1.0), 0.0),
            ((7.0, 0.0, -1.0), 10.0),
            ((7.0, 0.0), 5.0),
            ((Decimal("1.0"), Decimal("5.0"), Decimal("1.5")), Decimal('4.5')),
            ((Fraction(1, 1), Fraction(5, 1), Fraction(3, 2)), Fraction(5, 3)),
            (
                (
                    datetime(2019, 3, 29),
                    datetime(2019, 3, 30),
                    timedelta(hours=10),
                ),
                datetime(2019, 3, 30),
            ),
        ]:
            with self.assertRaises(ValueError):
                mi.numeric_range(*args).index(v)

    def test_parent_classes(self):
        r = mi.numeric_range(7.0)
        self.assertTrue(isinstance(r, Iterable))
        self.assertFalse(isinstance(r, Iterator))
        self.assertTrue(isinstance(r, Sequence))
        self.assertTrue(isinstance(r, Hashable))

    def test_bad_key(self):
        r = mi.numeric_range(7.0)
        for arg, message in [
            ('a', 'numeric range indices must be integers or slices, not str'),
            (
                (),
                'numeric range indices must be integers or slices, not tuple',
            ),
        ]:
            with self.assertRaisesRegex(TypeError, message):
                r[arg]

    def test_pickle(self):
        for g in [
            (7.0,),
            (5.0, 7.0),
            (5.0, 7.0, 3.0),
            (7.0, 5.0),
            (7.0, 5.0, 4.0),
            (7.0, 5.0, -1.0),
            (Decimal("1.0"), Decimal("5.0"), Decimal("1.5")),
            (Fraction(1, 1), Fraction(5, 1), Fraction(3, 2)),
            (datetime(2019, 3, 29), datetime(2019, 3, 30)),
        ]:
            r = mi.numeric_range(*g)
            self.assertTrue(dumps(r))  # assert not empty
            self.assertEqual(r, loads(dumps(r)))


class CountCycleTests(TestCase):
    def test_basic(self):
        h = [
            (0, 'a'),
            (0, 'b'),
            (0, 'c'),
            (1, 'a'),
            (1, 'b'),
            (1, 'c'),
            (2, 'a'),
            (2, 'b'),
            (2, 'c'),
        ]
        for g in [
            mi.take(9, mi.count_cycle('abc')),  # n=None
            list(mi.count_cycle('abc', 3)),  # n=3
        ]:
            self.assertEqual(g, h)

    def test_empty(self):
        self.assertEqual(list(mi.count_cycle('')), [])
        self.assertEqual(list(mi.count_cycle('', 2)), [])

    def test_negative(self):
        self.assertEqual(list(mi.count_cycle('abc', -3)), [])


class MarkEndsTests(TestCase):
    def test_basic(self):
        for size, expected in [
            (0, []),
            (1, [(True, True, '0')]),
            (2, [(True, False, '0'), (False, True, '1')]),
            (3, [(True, False, '0'), (False, False, '1'), (False, True, '2')]),
            (
                4,
                [
                    (True, False, '0'),
                    (False, False, '1'),
                    (False, False, '2'),
                    (False, True, '3'),
                ],
            ),
        ]:
            with self.subTest(size=size):
                h = map(str, range(size))
                g = list(mi.mark_ends(h))
                self.assertEqual(g, expected)


class LocateTests(TestCase):
    def test_default_pred(self):
        j = [0, 1, 1, 0, 1, 0, 0]
        g = list(mi.locate(j))
        h = [1, 2, 4]
        self.assertEqual(g, h)

    def test_no_matches(self):
        j = [0, 0, 0]
        g = list(mi.locate(j))
        h = []
        self.assertEqual(g, h)

    def test_custom_pred(self):
        j = ['0', 1, 1, '0', 1, '0', '0']
        m = lambda x: x == '0'
        g = list(mi.locate(j, m))
        h = [0, 3, 5, 6]
        self.assertEqual(g, h)

    def test_window_size(self):
        j = ['0', 1, 1, '0', 1, '0', '0']
        m = lambda *args: args == ('0', 1)
        g = list(mi.locate(j, m, window_size=2))
        h = [0, 3]
        self.assertEqual(g, h)

    def test_window_size_large(self):
        j = [1, 2, 3, 4]
        m = lambda a, b, c, d, e: True
        g = list(mi.locate(j, m, window_size=5))
        h = [0]
        self.assertEqual(g, h)

    def test_window_size_zero(self):
        g = [1, 2, 3, 4]
        h = lambda: True
        with self.assertRaises(ValueError):
            list(mi.locate(g, h, window_size=0))


class StripFunctionTests(TestCase):
    def test_hashable(self):
        g = list('www.example.com')
        h = lambda x: x in set('cmowz.')

        self.assertEqual(list(mi.lstrip(g, h)), list('example.com'))
        self.assertEqual(list(mi.rstrip(g, h)), list('www.example'))
        self.assertEqual(list(mi.strip(g, h)), list('example'))

    def test_not_hashable(self):
        g = [
            list('http://'),
            list('www'),
            list('.example'),
            list('.com'),
        ]
        h = lambda x: x in [list('http://'), list('www'), list('.com')]

        self.assertEqual(list(mi.lstrip(g, h)), g[2:])
        self.assertEqual(list(mi.rstrip(g, h)), g[:3])
        self.assertEqual(list(mi.strip(g, h)), g[2:3])

    def test_math(self):
        g = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2]
        h = lambda x: x <= 2

        self.assertEqual(list(mi.lstrip(g, h)), g[3:])
        self.assertEqual(list(mi.rstrip(g, h)), g[:-3])
        self.assertEqual(list(mi.strip(g, h)), g[3:-3])


class IteratorWithWeakReferences:
    class _AnObj:
        pass

    @classmethod
    def FROM_SIZE(cls, size: int) -> IteratorWithWeakReferences:
        return cls([IteratorWithWeakReferences._AnObj() for _ in range(size)])

    def __init__(self, iterable: Iterable):
        self._data = deque(element for element in iterable)
        self._weakReferences = [weakref.ref(a) for a in self._data]

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> object:
        if len(self._data) == 0:
            raise StopIteration
        return self._data.popleft()

    def weakReferencesState(self) -> list[bool]:
        return [wr() is not None for wr in self._weakReferences]


class IsliceExtendedTests(TestCase):
    def test_all(self):
        m = ['0', '1', '2', '3', '4', '5']
        j = [*range(-4, 10), None]
        q = [1, 2, 3, 4, -1, -2, -3, -4]
        for o in product(j, j, q):
            with self.subTest(slice_args=o):
                g = list(mi.islice_extended(m, *o))
                h = m[slice(*o)]
                self.assertEqual(g, h, o)

    def test_zero_step(self):
        with self.assertRaises(ValueError):
            list(mi.islice_extended([1, 2, 3], 0, 1, 0))

    def test_slicing(self):
        h = map(str, count())
        g = mi.islice_extended(h)[10:]
        j = mi.islice_extended(g)[:10]
        m = mi.islice_extended(j)[::2]
        self.assertEqual(list(m), ['10', '12', '14', '16', '18'])

    def test_slicing_extensive(self):
        g = range(10)
        h = (None, 1, 2, 7, -1)
        for start, stop, step in product(h, h, h):
            with self.subTest(slice_args=(start, stop, step)):
                m = tuple(
                    mi.islice_extended(g)[start:stop:step]
                )
                o = tuple(
                    mi.islice_extended(g, start, stop, step)
                )
                j = tuple(g[start:stop:step])
                self.assertEqual(m, j)
                self.assertEqual(o, j)

    def test_invalid_slice(self):
        with self.assertRaises(TypeError):
            mi.islice_extended(count())[13]

    def test_elements_lifecycle(self):
        # CPython does reference counting.
        # GC is not required when ref counting is supported.
        m = platform.python_implementation() == 'CPython'

        class TestCase(NamedTuple):
            initialSize: int
            slice: int
            # list of expected intermediate elements states (alive or not)
            # during a complete iteration
            expectedAliveStates: list[list[int]]

        # fmt: off
        o = [
            # testcases for: start>0, stop>0, step>0
            TestCase(initialSize=3, slice=(None, None, 1), expectedAliveStates=[  # noqa: E501
                [1, 1, 1], [0, 1, 1], [0, 0, 1], [0, 0, 0], [0, 0, 0]]),
            TestCase(initialSize=3, slice=(0, None, 1), expectedAliveStates=[
                [1, 1, 1], [0, 1, 1], [0, 0, 1], [0, 0, 0], [0, 0, 0]]),
            TestCase(initialSize=3, slice=(1, 2, 1), expectedAliveStates=[
                [1, 1, 1], [0, 0, 1], [0, 0, 1]]),
            TestCase(initialSize=4, slice=(0, None, 2), expectedAliveStates=[
                [1, 1, 1, 1], [0, 1, 1, 1], [0, 0, 0, 1], [0, 0, 0, 0]]),
            TestCase(initialSize=5, slice=(1, 4, 2), expectedAliveStates=[
                [1, 1, 1, 1, 1], [0, 0, 1, 1, 1], [0, 0, 0, 0, 1], [0, 0, 0, 0, 1]]),  # noqa: E501
            TestCase(initialSize=5, slice=(4, 1, 1), expectedAliveStates=[
                [1, 1, 1, 1, 1], [0, 0, 0, 0, 1]]),

            # FYI: to process a negative start/stop index, we need to iterate
            # on the whole iterator. All the elements will be consumed
            # and will ALWAYS be released on full iteration completion.

            # testcases for: start<0, stop>0, step>0
            TestCase(initialSize=3, slice=(-3, None, 1), expectedAliveStates=[
                [1, 1, 1], [0, 1, 1], [0, 0, 1], [0, 0, 0], [0, 0, 0]]),
            TestCase(initialSize=3, slice=(-2, 2, 1), expectedAliveStates=[
                [1, 1, 1], [0, 0, 1], [0, 0, 0]]),
            TestCase(initialSize=4, slice=(-4, None, 2), expectedAliveStates=[
                [1, 1, 1, 1], [0, 1, 1, 1], [0, 0, 0, 1], [0, 0, 0, 0]]),
            TestCase(initialSize=5, slice=(-4, 4, 2), expectedAliveStates=[
                [1, 1, 1, 1, 1], [0, 0, 1, 1, 1], [0, 0, 0, 0, 1], [0, 0, 0, 0, 0]]),  # noqa: E501
            TestCase(initialSize=3, slice=(-2, 0, 1), expectedAliveStates=[
                [1, 1, 1], [0, 0, 0]]),

            # testcases for: start>0, stop<0, step>0
            TestCase(initialSize=3, slice=(None, -1, 1), expectedAliveStates=[
                [1, 1, 1], [0, 1, 1], [0, 0, 1], [0, 0, 0]]),
            TestCase(initialSize=4, slice=(1, -1, 1), expectedAliveStates=[
                [1, 1, 1, 1], [0, 0, 1, 1], [0, 0, 0, 1], [0, 0, 0, 0]]),
            TestCase(initialSize=5, slice=(None, -2, 2), expectedAliveStates=[
                [1, 1, 1, 1, 1], [0, 1, 1, 1, 1], [0, 0, 0, 1, 1], [0, 0, 0, 0, 0]]),  # noqa: E501
            TestCase(initialSize=5, slice=(1, -1, 2), expectedAliveStates=[
                [1, 1, 1, 1, 1], [0, 0, 1, 1, 1], [0, 0, 0, 0, 1], [0, 0, 0, 0, 0]]),  # noqa: E501
            TestCase(initialSize=5, slice=(4, -5, 2), expectedAliveStates=[
                [1, 1, 1, 1, 1], [0, 0, 0, 0, 0]]),

            # testcases for: start>0, stop>0, step<0
            TestCase(initialSize=3, slice=(None, None, -1), expectedAliveStates=[  # noqa: E501
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [0, 0, 0]]),
            TestCase(initialSize=3, slice=(2, None, -1), expectedAliveStates=[
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [0, 0, 0]]),
            TestCase(initialSize=3, slice=(None, 0, -1), expectedAliveStates=[
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1], [0, 1, 1], [0, 1, 1], [0, 0, 0]]),
            TestCase(initialSize=6, slice=(3, 1, -1), expectedAliveStates=[
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1, 1, 1, 1], [0, 0, 1, 1, 1, 1], [0, 0, 1, 1, 1, 1], [0, 0, 0, 0, 1, 1]]),  # noqa: E501
            TestCase(initialSize=5, slice=(1, 3, -1), expectedAliveStates=[
                # ⚠️could be improved. Final state could be [0, 0, 1, 1, 1]
                [1, 1, 1, 1, 1], [0, 0, 0, 0, 1]]),

            # testcases for: start<0, stop>0, step<0
            TestCase(initialSize=3, slice=(-1, None, -1), expectedAliveStates=[
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [0, 0, 0]]),
            TestCase(initialSize=3, slice=(-1, 0, -1), expectedAliveStates=[
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1], [0, 1, 1], [0, 1, 1], [0, 0, 0]]),
            TestCase(initialSize=6, slice=(-2, None, -2), expectedAliveStates=[
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [0, 0, 0, 0, 0, 0]]),  # noqa: E501
            TestCase(initialSize=6, slice=(-2, 1, -2), expectedAliveStates=[
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1, 1, 1, 1], [0, 0, 1, 1, 1, 1], [0, 0, 1, 1, 1, 1], [0, 0, 0, 0, 0, 0]]),  # noqa: E501
            TestCase(initialSize=6, slice=(-4, 4, -2), expectedAliveStates=[
                [1, 1, 1, 1, 1, 1], [0, 0, 0, 0, 0, 0]]),

            # testcases for: start>0, stop<0, step<0
            TestCase(initialSize=3, slice=(None, -3, -1), expectedAliveStates=[
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1], [0, 1, 1], [0, 1, 1], [0, 0, 0]]),
            TestCase(initialSize=3, slice=(None, -4, -1), expectedAliveStates=[
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [0, 0, 0]]),
            TestCase(initialSize=5, slice=(3, -4, -1), expectedAliveStates=[
                # ⚠️could be improved, elements are only released on final step
                [1, 1, 1, 1, 1], [0, 0, 1, 1, 1], [0, 0, 1, 1, 1], [0, 0, 0, 0, 0]]),   # noqa: E501
            TestCase(initialSize=5, slice=(1, -1, -1), expectedAliveStates=[
                [1, 1, 1, 1, 1], [0, 0, 0, 0, 0]]),
        ]
        # fmt: on

        for index, testCase in enumerate(o):
            with self.subTest(f"{index:02d}", testCase=testCase):
                j = IteratorWithWeakReferences.FROM_SIZE(
                    testCase.initialSize
                )
                h = mi.islice_extended(j, *testCase.slice)

                g = []
                m or gc.collect()
                # initial alive states
                g.append(j.weakReferencesState())
                while True:
                    try:
                        next(h)
                        m or gc.collect()
                        # intermediate alive states
                        g.append(j.weakReferencesState())
                    except StopIteration:
                        m or gc.collect()
                        # final alive states
                        g.append(j.weakReferencesState())
                        break
                self.assertEqual(g, testCase.expectedAliveStates)


class ConsecutiveGroupsTest(TestCase):
    def test_numbers(self):
        j = [-10, -8, -7, -6, 1, 2, 4, 5, -1, 7]
        g = [list(g) for g in mi.consecutive_groups(j)]
        h = [[-10], [-8, -7, -6], [1, 2], [4, 5], [-1], [7]]
        self.assertEqual(g, h)

    def test_custom_ordering(self):
        j = ['1', '10', '11', '20', '21', '22', '30', '31']
        m = lambda x: int(x)
        g = [list(g) for g in mi.consecutive_groups(j, m)]
        h = [['1'], ['10', '11'], ['20', '21', '22'], ['30', '31']]
        self.assertEqual(g, h)

    def test_exotic_ordering(self):
        j = [
            ('a', 'b', 'c', 'd'),
            ('a', 'c', 'b', 'd'),
            ('a', 'c', 'd', 'b'),
            ('a', 'd', 'b', 'c'),
            ('d', 'b', 'c', 'a'),
            ('d', 'c', 'a', 'b'),
        ]
        m = list(permutations('abcd')).index
        g = [list(g) for g in mi.consecutive_groups(j, m)]
        h = [
            [('a', 'b', 'c', 'd')],
            [('a', 'c', 'b', 'd'), ('a', 'c', 'd', 'b'), ('a', 'd', 'b', 'c')],
            [('d', 'b', 'c', 'a'), ('d', 'c', 'a', 'b')],
        ]
        self.assertEqual(g, h)


class DifferenceTest(TestCase):
    def test_normal(self):
        j = [10, 20, 30, 40, 50]
        g = list(mi.difference(j))
        h = [10, 10, 10, 10, 10]
        self.assertEqual(g, h)

    def test_custom(self):
        j = [10, 20, 30, 40, 50]
        g = list(mi.difference(j, add))
        h = [10, 30, 50, 70, 90]
        self.assertEqual(g, h)

    def test_roundtrip(self):
        j = list(range(100))
        g = accumulate(j)
        h = list(mi.difference(g))
        self.assertEqual(h, j)

    def test_one(self):
        self.assertEqual(list(mi.difference([0])), [0])

    def test_empty(self):
        self.assertEqual(list(mi.difference([])), [])

    def test_initial(self):
        j = list(range(100))
        g = accumulate(j, initial=100)
        h = list(mi.difference(g, initial=100))
        self.assertEqual(h, j)


class SeekableTest(PeekableMixinTests, TestCase):
    cls = mi.seekable

    def test_exhaustion_reset(self):
        g = [str(n) for n in range(10)]

        s = mi.seekable(g)
        self.assertEqual(list(s), g)  # Normal iteration
        self.assertEqual(list(s), [])  # Iterable is exhausted

        s.seek(0)
        self.assertEqual(list(s), g)  # Back in action

    def test_partial_reset(self):
        g = [str(n) for n in range(10)]

        s = mi.seekable(g)
        self.assertEqual(mi.take(5, s), g[:5])  # Normal iteration

        s.seek(1)
        self.assertEqual(list(s), g[1:])  # Get the rest of the iterable

    def test_forward(self):
        g = [str(n) for n in range(10)]

        s = mi.seekable(g)
        self.assertEqual(mi.take(1, s), g[:1])  # Normal iteration

        s.seek(3)  # Skip over index 2
        self.assertEqual(list(s), g[3:])  # Result is similar to slicing

        s.seek(0)  # Back to 0
        self.assertEqual(list(s), g)  # No difference in result

    def test_past_end(self):
        g = [str(n) for n in range(10)]

        s = mi.seekable(g)
        self.assertEqual(mi.take(1, s), g[:1])  # Normal iteration

        s.seek(20)
        self.assertEqual(list(s), [])  # Iterable is exhausted

        s.seek(0)  # Back to 0
        self.assertEqual(list(s), g)  # No difference in result

    def test_elements(self):
        h = map(str, count())

        s = mi.seekable(h)
        mi.take(10, s)

        g = s.elements()
        self.assertEqual(
            [g[i] for i in range(10)], [str(n) for n in range(10)]
        )
        self.assertEqual(len(g), 10)

        mi.take(10, s)
        self.assertEqual(list(g), [str(n) for n in range(20)])

    def test_maxlen(self):
        g = map(str, count())

        s = mi.seekable(g, maxlen=4)
        self.assertEqual(mi.take(10, s), [str(n) for n in range(10)])
        self.assertEqual(list(s.elements()), ['6', '7', '8', '9'])

        s.seek(0)
        self.assertEqual(mi.take(14, s), [str(n) for n in range(6, 20)])
        self.assertEqual(list(s.elements()), ['16', '17', '18', '19'])

    def test_maxlen_zero(self):
        g = [str(x) for x in range(5)]
        s = mi.seekable(g, maxlen=0)
        self.assertEqual(list(s), g)
        self.assertEqual(list(s.elements()), [])

    def test_relative_seek(self):
        g = [str(x) for x in range(5)]
        s = mi.seekable(g)
        s.relative_seek(2)
        self.assertEqual(next(s), '2')
        s.relative_seek(-2)
        self.assertEqual(next(s), '1')
        s.relative_seek(-2)
        self.assertEqual(
            next(s), '0'
        )  # Seek relative to current position within the cache
        s.relative_seek(-10)  # Lower bound
        self.assertEqual(next(s), '0')
        s.relative_seek(10)  # Lower bound
        self.assertEqual(list(s.elements()), [str(x) for x in range(5)])


class SequenceViewTests(TestCase):
    def test_init(self):
        g = mi.SequenceView((1, 2, 3))
        self.assertEqual(repr(g), "SequenceView((1, 2, 3))")
        self.assertRaises(TypeError, lambda: mi.SequenceView({}))

    def test_update(self):
        g = [1, 2, 3]
        h = mi.SequenceView(g)
        self.assertEqual(len(h), 3)
        self.assertEqual(repr(h), "SequenceView([1, 2, 3])")

        g.pop()
        self.assertEqual(len(h), 2)
        self.assertEqual(repr(h), "SequenceView([1, 2])")

    def test_indexing(self):
        g = ('a', 'b', 'c', 'd', 'e', 'f')
        h = mi.SequenceView(g)
        for i in range(-len(g), len(g)):
            self.assertEqual(h[i], g[i])

    def test_slicing(self):
        h = ('a', 'b', 'c', 'd', 'e', 'f')
        o = mi.SequenceView(h)
        n = len(h)
        g = list(range(-n - 1, n + 1)) + [None]
        m = list(range(-n, n + 1))
        m.remove(0)
        for j in product(g, g, m):
            i = slice(*j)
            self.assertEqual(o[i], h[i])

    def test_abc_methods(self):
        # collections.Sequence should provide all of this functionality
        g = ('a', 'b', 'c', 'd', 'e', 'f', 'f')
        h = mi.SequenceView(g)

        # __contains__
        self.assertIn('b', h)
        self.assertNotIn('g', h)

        # __iter__
        self.assertEqual(list(iter(h)), list(g))

        # __reversed__
        self.assertEqual(list(reversed(h)), list(reversed(g)))

        # index
        self.assertEqual(h.index('b'), 1)

        # count
        self.assertEqual(g.count('f'), 2)


class RunLengthTest(TestCase):
    def test_encode(self):
        j = (int(str(n)[0]) for n in count(800))
        g = mi.take(4, mi.run_length.encode(j))
        h = [(8, 100), (9, 100), (1, 1000), (2, 1000)]
        self.assertEqual(g, h)

    def test_decode(self):
        j = [('d', 4), ('c', 3), ('b', 2), ('a', 1)]
        g = ''.join(mi.run_length.decode(j))
        h = 'ddddcccbba'
        self.assertEqual(g, h)


class ExactlyNTests(TestCase):
    """Tests for ``exactly_n()``"""

    def test_true(self):
        """Iterable has ``n`` ``True`` elements"""
        self.assertTrue(mi.exactly_n([True, False, True], 2))
        self.assertTrue(mi.exactly_n([1, 1, 1, 0], 3))
        self.assertTrue(mi.exactly_n([False, False], 0))
        self.assertTrue(mi.exactly_n(range(100), 10, lambda x: x < 10))
        self.assertTrue(mi.exactly_n(repeat(True, 100), 100))
        self.assertTrue(mi.exactly_n(repeat(False, 100), 100, predicate=not_))

    def test_false(self):
        """Iterable does not have ``n`` ``True`` elements"""
        self.assertFalse(mi.exactly_n([True, False, False], 2))
        self.assertFalse(mi.exactly_n([True, True, False], 1))
        self.assertFalse(mi.exactly_n([False], 1))
        self.assertFalse(mi.exactly_n([True], -1))
        self.assertFalse(mi.exactly_n([True], -10))
        self.assertFalse(mi.exactly_n([], -1))
        self.assertFalse(mi.exactly_n([], -10))
        self.assertFalse(mi.exactly_n([True], 0))
        self.assertFalse(mi.exactly_n(repeat(True), 100))

    def test_empty(self):
        """Return ``True`` if the iterable is empty and ``n`` is 0"""
        self.assertTrue(mi.exactly_n([], 0))
        self.assertFalse(mi.exactly_n([], 1))


class AlwaysReversibleTests(TestCase):
    """Tests for ``always_reversible()``"""

    def test_regular_reversed(self):
        self.assertEqual(
            list(reversed(range(10))), list(mi.always_reversible(range(10)))
        )
        self.assertEqual(
            list(reversed([1, 2, 3])), list(mi.always_reversible([1, 2, 3]))
        )
        self.assertEqual(
            reversed([1, 2, 3]).__class__,
            mi.always_reversible([1, 2, 3]).__class__,
        )

    def test_nonseq_reversed(self):
        # Create a non-reversible generator from a sequence
        with self.assertRaises(TypeError):
            reversed(x for x in range(10))

        self.assertEqual(
            list(reversed(range(10))),
            list(mi.always_reversible(x for x in range(10))),
        )
        self.assertEqual(
            list(reversed([1, 2, 3])),
            list(mi.always_reversible(x for x in [1, 2, 3])),
        )
        self.assertNotEqual(
            reversed((1, 2)).__class__,
            mi.always_reversible(x for x in (1, 2)).__class__,
        )


class CircularShiftsTests(TestCase):
    def test_empty(self):
        # empty iterable -> empty list
        self.assertEqual(list(mi.circular_shifts([])), [])

    def test_simple_circular_shifts(self):
        # test the a simple iterator case
        self.assertEqual(
            list(mi.circular_shifts(range(4))),
            [(0, 1, 2, 3), (1, 2, 3, 0), (2, 3, 0, 1), (3, 0, 1, 2)],
        )

    def test_duplicates(self):
        # test non-distinct entries
        self.assertEqual(
            list(mi.circular_shifts([0, 1, 0, 1])),
            [(0, 1, 0, 1), (1, 0, 1, 0), (0, 1, 0, 1), (1, 0, 1, 0)],
        )

    def test_steps_positive(self):
        g = list(mi.circular_shifts(range(5), steps=2))
        h = [
            (0, 1, 2, 3, 4),
            (2, 3, 4, 0, 1),
            (4, 0, 1, 2, 3),
            (1, 2, 3, 4, 0),
            (3, 4, 0, 1, 2),
        ]
        self.assertEqual(g, h)

    def test_steps_negative(self):
        g = list(mi.circular_shifts(range(5), steps=-2))
        h = [
            (0, 1, 2, 3, 4),
            (3, 4, 0, 1, 2),
            (1, 2, 3, 4, 0),
            (4, 0, 1, 2, 3),
            (2, 3, 4, 0, 1),
        ]
        self.assertEqual(g, h)

    def test_steps_zero(self):
        with self.assertRaises(ValueError):
            list(mi.circular_shifts(range(5), steps=0))


class MakeDecoratorTests(TestCase):
    def test_basic(self):
        m = mi.make_decorator(islice)

        @m(1, 10, 2)
        def user_function(arg_1, arg_2, kwarg_1=None):
            self.assertEqual(arg_1, 'arg_1')
            self.assertEqual(arg_2, 'arg_2')
            self.assertEqual(kwarg_1, 'kwarg_1')
            return map(str, count())

        j = user_function('arg_1', 'arg_2', kwarg_1='kwarg_1')
        g = list(j)
        h = ['1', '3', '5', '7', '9']
        self.assertEqual(g, h)

    def test_result_index(self):
        def stringify(*args, **kwargs):
            self.assertEqual(args[0], 'arg_0')
            q = args[1]
            self.assertEqual(args[2], 'arg_2')
            self.assertEqual(kwargs['kwarg_1'], 'kwarg_1')
            return map(str, q)

        o = mi.make_decorator(stringify, result_index=1)

        @o('arg_0', 'arg_2', kwarg_1='kwarg_1')
        def user_function(n):
            return count(n)

        j = user_function(1)
        g = mi.take(5, j)
        h = ['1', '2', '3', '4', '5']
        self.assertEqual(g, h)

    def test_wrap_class(self):
        h = mi.make_decorator(mi.seekable)

        @h()
        def user_function(n):
            return map(str, range(n))

        g = user_function(5)
        self.assertEqual(list(g), ['0', '1', '2', '3', '4'])

        g.seek(0)
        self.assertEqual(list(g), ['0', '1', '2', '3', '4'])


class MapReduceTests(TestCase):
    def test_default(self):
        j = (str(x) for x in range(5))
        m = lambda x: int(x) // 2
        g = sorted(mi.map_reduce(j, m).items())
        h = [(0, ['0', '1']), (1, ['2', '3']), (2, ['4'])]
        self.assertEqual(g, h)

    def test_valuefunc(self):
        j = (str(x) for x in range(5))
        m = lambda x: int(x) // 2
        o = int
        g = sorted(mi.map_reduce(j, m, o).items())
        h = [(0, [0, 1]), (1, [2, 3]), (2, [4])]
        self.assertEqual(g, h)

    def test_reducefunc(self):
        j = (str(x) for x in range(5))
        m = lambda x: int(x) // 2
        q = int
        o = lambda value_list: reduce(mul, value_list, 1)
        g = sorted(
            mi.map_reduce(j, m, q, o).items()
        )
        h = [(0, 0), (1, 6), (2, 4)]
        self.assertEqual(g, h)

    def test_ret(self):
        d = mi.map_reduce([1, 0, 2, 0, 1, 0], bool)
        self.assertEqual(d, {False: [0, 0, 0], True: [1, 2, 1]})
        self.assertRaises(KeyError, lambda: d[None].append(1))


class RlocateTests(TestCase):
    def test_default_pred(self):
        m = [0, 1, 1, 0, 1, 0, 0]
        for j in (m[:], iter(m)):
            g = list(mi.rlocate(j))
            h = [4, 2, 1]
            self.assertEqual(g, h)

    def test_no_matches(self):
        m = [0, 0, 0]
        for j in (m[:], iter(m)):
            g = list(mi.rlocate(j))
            h = []
            self.assertEqual(g, h)

    def test_custom_pred(self):
        m = ['0', 1, 1, '0', 1, '0', '0']
        o = lambda x: x == '0'
        for j in (m[:], iter(m)):
            g = list(mi.rlocate(j, o))
            h = [6, 5, 3, 0]
            self.assertEqual(g, h)

    def test_efficient_reversal(self):
        h = range(9**9)  # Is efficiently reversible
        m = 9**9 - 2
        j = lambda x: x == m  # Find-able from the right
        g = next(mi.rlocate(h, j))
        self.assertEqual(g, m)

    def test_window_size(self):
        m = ['0', 1, 1, '0', 1, '0', '0']
        o = lambda *args: args == ('0', 1)
        for j in (m, iter(m)):
            g = list(mi.rlocate(j, o, window_size=2))
            h = [3, 0]
            self.assertEqual(g, h)

    def test_window_size_large(self):
        m = [1, 2, 3, 4]
        o = lambda a, b, c, d, e: True
        for j in (m, iter(m)):
            g = list(mi.rlocate(m, o, window_size=5))
            h = [0]
            self.assertEqual(g, h)

    def test_window_size_zero(self):
        h = [1, 2, 3, 4]
        j = lambda: True
        for g in (h, iter(h)):
            with self.assertRaises(ValueError):
                list(mi.locate(h, j, window_size=0))


class ReplaceTests(TestCase):
    def test_basic(self):
        j = range(10)
        m = lambda x: x % 2 == 0
        o = []
        g = list(mi.replace(j, m, o))
        h = [1, 3, 5, 7, 9]
        self.assertEqual(g, h)

    def test_count(self):
        j = range(10)
        m = lambda x: x % 2 == 0
        o = []
        g = list(mi.replace(j, m, o, count=4))
        h = [1, 3, 5, 7, 8, 9]
        self.assertEqual(g, h)

    def test_window_size(self):
        j = range(10)
        m = lambda *args: args == (0, 1, 2)
        o = []
        g = list(mi.replace(j, m, o, window_size=3))
        h = [3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(g, h)

    def test_window_size_end(self):
        j = range(10)
        m = lambda *args: args == (7, 8, 9)
        o = []
        g = list(mi.replace(j, m, o, window_size=3))
        h = [0, 1, 2, 3, 4, 5, 6]
        self.assertEqual(g, h)

    def test_window_size_count(self):
        j = range(10)
        m = lambda *args: (args == (0, 1, 2)) or (args == (7, 8, 9))
        o = []
        g = list(
            mi.replace(j, m, o, count=1, window_size=3)
        )
        h = [3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(g, h)

    def test_window_size_large(self):
        j = range(4)
        m = lambda a, b, c, d, e: True
        o = [5, 6, 7]
        g = list(mi.replace(j, m, o, window_size=5))
        h = [5, 6, 7]
        self.assertEqual(g, h)

    def test_window_size_zero(self):
        g = range(10)
        h = lambda *args: True
        j = []
        with self.assertRaises(ValueError):
            list(mi.replace(g, h, j, window_size=0))

    def test_iterable_substitutes(self):
        j = range(5)
        m = lambda x: x % 2 == 0
        o = iter('__')
        g = list(mi.replace(j, m, o))
        h = ['_', '_', 1, '_', '_', 3, '_', '_']
        self.assertEqual(g, h)


class PartitionsTest(TestCase):
    def test_types(self):
        for j in ['abcd', ['a', 'b', 'c', 'd'], ('a', 'b', 'c', 'd')]:
            with self.subTest(iterable=j):
                g = list(mi.partitions(j))
                h = [
                    [['a', 'b', 'c', 'd']],
                    [['a'], ['b', 'c', 'd']],
                    [['a', 'b'], ['c', 'd']],
                    [['a', 'b', 'c'], ['d']],
                    [['a'], ['b'], ['c', 'd']],
                    [['a'], ['b', 'c'], ['d']],
                    [['a', 'b'], ['c'], ['d']],
                    [['a'], ['b'], ['c'], ['d']],
                ]
                self.assertEqual(g, h)

    def test_empty(self):
        j = []
        g = list(mi.partitions(j))
        h = [[[]]]
        self.assertEqual(g, h)

    def test_order(self):
        j = iter([3, 2, 1])
        g = list(mi.partitions(j))
        h = [[[3, 2, 1]], [[3], [2, 1]], [[3, 2], [1]], [[3], [2], [1]]]
        self.assertEqual(g, h)

    def test_duplicates(self):
        j = [1, 1, 1]
        g = list(mi.partitions(j))
        h = [[[1, 1, 1]], [[1], [1, 1]], [[1, 1], [1]], [[1], [1], [1]]]
        self.assertEqual(g, h)


class _FrozenMultiset(Set):
    """
    A helper class, useful to compare two lists without reference to the order
    of elements.

    FrozenMultiset represents a hashable set that allows duplicate elements.
    """

    def __init__(self, iterable):
        self._collection = frozenset(Counter(iterable).items())

    def __contains__(self, y):
        """
        >>> (0, 1) in _FrozenMultiset([(0, 1), (2,), (0, 1)])
        True
        """
        return any(y == x for x, _ in self._collection)

    def __iter__(self):
        """
        >>> sorted(_FrozenMultiset([(0, 1), (2,), (0, 1)]))
        [(0, 1), (0, 1), (2,)]
        """
        return (x for x, c in self._collection for _ in range(c))

    def __len__(self):
        """
        >>> len(_FrozenMultiset([(0, 1), (2,), (0, 1)]))
        3
        """
        return sum(c for x, c in self._collection)

    def has_duplicates(self):
        """
        >>> _FrozenMultiset([(0, 1), (2,), (0, 1)]).has_duplicates()
        True
        """
        return any(c != 1 for _, c in self._collection)

    def __hash__(self):
        return hash(self._collection)

    def __repr__(self):
        return f'FrozenSet([{", ".join(repr(x) for x in iter(self))}]'


class SetPartitionsTests(TestCase):
    @staticmethod
    def _normalize_partition(p):
        """
        Return a normalized, hashable, version of a partition using
        _FrozenMultiset
        """
        return _FrozenMultiset(_FrozenMultiset(g) for g in p)

    @staticmethod
    def _normalize_partitions(ps):
        """
        Return a normalized set of all normalized partitions using
        _FrozenMultiset
        """
        return _FrozenMultiset(
            SetPartitionsTests._normalize_partition(p) for p in ps
        )

    def test_repeated(self):
        j = 'aaa'
        g = mi.set_partitions(j, 2)
        h = [['a', 'aa'], ['a', 'aa'], ['a', 'aa']]
        self.assertEqual(
            self._normalize_partitions(h),
            self._normalize_partitions(g),
        )

    def test_each_correct(self):
        a = set(range(6))
        for p in mi.set_partitions(a):
            g = {e for g in p for e in g}
            self.assertEqual(a, g)

    def test_duplicates(self):
        a = set(range(6))
        for p in mi.set_partitions(a):
            self.assertFalse(self._normalize_partition(p).has_duplicates())

    def test_found_all(self):
        """small example, hand-checked"""
        h = [
            [[0], [1], [2, 3, 4]],
            [[0], [1, 2], [3, 4]],
            [[0], [2], [1, 3, 4]],
            [[0], [3], [1, 2, 4]],
            [[0], [4], [1, 2, 3]],
            [[0], [1, 3], [2, 4]],
            [[0], [1, 4], [2, 3]],
            [[1], [2], [0, 3, 4]],
            [[1], [3], [0, 2, 4]],
            [[1], [4], [0, 2, 3]],
            [[1], [0, 2], [3, 4]],
            [[1], [0, 3], [2, 4]],
            [[1], [0, 4], [2, 3]],
            [[2], [3], [0, 1, 4]],
            [[2], [4], [0, 1, 3]],
            [[2], [0, 1], [3, 4]],
            [[2], [0, 3], [1, 4]],
            [[2], [0, 4], [1, 3]],
            [[3], [4], [0, 1, 2]],
            [[3], [0, 1], [2, 4]],
            [[3], [0, 2], [1, 4]],
            [[3], [0, 4], [1, 2]],
            [[4], [0, 1], [2, 3]],
            [[4], [0, 2], [1, 3]],
            [[4], [0, 3], [1, 2]],
        ]
        g = mi.set_partitions(range(5), 3)
        self.assertEqual(
            self._normalize_partitions(h),
            self._normalize_partitions(g),
        )

    def test_stirling_numbers(self):
        """Check against https://en.wikipedia.org/wiki/
        Stirling_numbers_of_the_second_kind#Table_of_values"""
        g = [
            [1],
            [1, 1],
            [1, 3, 1],
            [1, 7, 6, 1],
            [1, 15, 25, 10, 1],
            [1, 31, 90, 65, 15, 1],
        ]
        for n, cardinality_by_k in enumerate(g, 1):
            for k, cardinality in enumerate(cardinality_by_k, 1):
                self.assertEqual(
                    cardinality, len(list(mi.set_partitions(range(n), k)))
                )

    def test_no_group(self):
        def helper():
            list(mi.set_partitions(range(4), -1))

        self.assertRaises(ValueError, helper)

    def test_to_many_groups(self):
        self.assertEqual([], list(mi.set_partitions(range(4), 5)))

    def test_min_size(self):
        j = 'abc'
        g = mi.set_partitions(j, min_size=2)
        h = [['abc']]
        self.assertEqual(
            self._normalize_partitions(h),
            self._normalize_partitions(g),
        )

    def test_max_size(self):
        j = 'abc'
        g = mi.set_partitions(j, max_size=2)
        h = [['a', 'bc'], ['ab', 'c'], ['b', 'ac'], ['a', 'b', 'c']]
        self.assertEqual(
            self._normalize_partitions(h),
            self._normalize_partitions(g),
        )

    def test_min_max(self):
        g = 'abcdefg'
        self.assertEqual(
            list(mi.set_partitions(g, min_size=4, max_size=3)), []
        )


class TimeLimitedTests(TestCase):
    def test_basic(self):
        def generator():
            yield 1
            yield 2
            sleep(0.2)
            yield 3

        j = mi.time_limited(0.1, generator())
        g = list(j)
        h = [1, 2]
        self.assertEqual(g, h)
        self.assertTrue(j.timed_out)

    def test_complete(self):
        j = mi.time_limited(2, iter(range(10)))
        g = list(j)
        h = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(g, h)
        self.assertFalse(j.timed_out)

    def test_zero_limit(self):
        j = mi.time_limited(0, count())
        g = list(j)
        h = []
        self.assertEqual(g, h)
        self.assertTrue(j.timed_out)

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            list(mi.time_limited(-0.1, count()))


class OnlyTests(TestCase):
    def test_defaults(self):
        self.assertEqual(mi.only([]), None)
        self.assertEqual(mi.only([1]), 1)
        self.assertRaises(ValueError, lambda: mi.only([1, 2]))

    def test_custom_value(self):
        self.assertEqual(mi.only([], default='!'), '!')
        self.assertEqual(mi.only([1], default='!'), 1)
        self.assertRaises(ValueError, lambda: mi.only([1, 2], default='!'))

    def test_custom_exception(self):
        self.assertEqual(mi.only([], too_long=RuntimeError), None)
        self.assertEqual(mi.only([1], too_long=RuntimeError), 1)
        self.assertRaises(
            RuntimeError, lambda: mi.only([1, 2], too_long=RuntimeError)
        )

    def test_default_exception_message(self):
        self.assertRaisesRegex(
            ValueError,
            "Expected exactly one item in iterable, "
            "but got 'foo', 'bar', and perhaps more",
            lambda: mi.only(['foo', 'bar', 'baz']),
        )


class IchunkedTests(TestCase):
    def test_even(self):
        j = (str(x) for x in range(10))
        g = [''.join(c) for c in mi.ichunked(j, 5)]
        h = ['01234', '56789']
        self.assertEqual(g, h)

    def test_odd(self):
        j = (str(x) for x in range(10))
        g = [''.join(c) for c in mi.ichunked(j, 4)]
        h = ['0123', '4567', '89']
        self.assertEqual(g, h)

    def test_zero(self):
        j = []
        g = [list(c) for c in mi.ichunked(j, 0)]
        h = []
        self.assertEqual(g, h)

    def test_negative(self):
        g = count()
        with self.assertRaises(ValueError):
            [list(c) for c in mi.ichunked(g, -1)]

    def test_out_of_order(self):
        m = map(str, count())
        j = mi.ichunked(m, 4)
        g = next(j)
        h = next(j)
        self.assertEqual(''.join(h), '4567')
        self.assertEqual(''.join(g), '0123')

    def test_laziness(self):
        def gen():
            yield 0
            raise RuntimeError
            yield from count(1)

        h = mi.ichunked(gen(), 4)
        g = next(h)
        self.assertEqual(next(g), 0)
        self.assertRaises(RuntimeError, next, h)

    def test_memory_in_order(self):
        m = []

        def gen():
            for t in count():
                m.append(t)
                yield t

        # No items should be kept in memory when a ichunked is first called
        g = mi.ichunked(gen(), 4)
        self.assertEqual(m, [])

        # The first item of each chunk should be generated on chunk generation
        h = next(g)
        self.assertEqual(m, [0])

        # If we don't read a chunk before getting its successor, its contents
        # will be cached
        o = next(g)
        self.assertEqual(m, [0, 1, 2, 3, 4])

        # Check if we can read in cached values
        self.assertEqual(list(h), [0, 1, 2, 3])
        self.assertEqual(list(o), [4, 5, 6, 7])

        # Again only the most recent chunk should have an item cached
        q = next(g)
        self.assertEqual(len(m), 9)

        # No new item should be cached when reading past the first number
        next(q)
        self.assertEqual(len(m), 9)

        # we should not be able to read spent chunks
        self.assertEqual(list(h), [])
        self.assertEqual(list(o), [])


class DistinctCombinationsTests(TestCase):
    def test_basic(self):
        for j in [
            (1, 2, 2, 3, 3, 3),  # In order
            range(6),  # All distinct
            'abbccc',  # Not numbers
            'cccbba',  # Backward
            'mississippi',  # No particular order
        ]:
            for r in range(len(j)):
                with self.subTest(iterable=j, r=r):
                    g = list(mi.distinct_combinations(j, r))
                    h = list(
                        mi.unique_everseen(combinations(j, r))
                    )
                    self.assertEqual(g, h)

    def test_negative(self):
        with self.assertRaises(ValueError):
            list(mi.distinct_combinations([], -1))

    def test_empty(self):
        self.assertEqual(list(mi.distinct_combinations([], 2)), [])


class FilterExceptTests(TestCase):
    def test_no_exceptions_pass(self):
        j = '0123'
        g = list(mi.filter_except(int, j))
        h = ['0', '1', '2', '3']
        self.assertEqual(g, h)

    def test_no_exceptions_raise(self):
        g = ['0', '1', 'two', '3']
        with self.assertRaises(ValueError):
            list(mi.filter_except(int, g))

    def test_raise(self):
        g = ['0', '12', 'three', None]
        with self.assertRaises(TypeError):
            list(mi.filter_except(int, g, ValueError))

    def test_false(self):
        # Even if the validator returns false, we pass through
        m = lambda x: False
        j = ['0', '1', '2', 'three', None]
        g = list(mi.filter_except(m, j, Exception))
        h = ['0', '1', '2', 'three', None]
        self.assertEqual(g, h)

    def test_multiple(self):
        j = ['0', '1', '2', 'three', None, '4']
        g = list(mi.filter_except(int, j, ValueError, TypeError))
        h = ['0', '1', '2', '4']
        self.assertEqual(g, h)


class MapExceptTests(TestCase):
    def test_no_exceptions_pass(self):
        j = '0123'
        g = list(mi.map_except(int, j))
        h = [0, 1, 2, 3]
        self.assertEqual(g, h)

    def test_no_exceptions_raise(self):
        g = ['0', '1', 'two', '3']
        with self.assertRaises(ValueError):
            list(mi.map_except(int, g))

    def test_raise(self):
        g = ['0', '12', 'three', None]
        with self.assertRaises(TypeError):
            list(mi.map_except(int, g, ValueError))

    def test_multiple(self):
        j = ['0', '1', '2', 'three', None, '4']
        g = list(mi.map_except(int, j, ValueError, TypeError))
        h = [0, 1, 2, 4]
        self.assertEqual(g, h)


class MapIfTests(TestCase):
    def test_without_func_else(self):
        j = list(range(-5, 5))
        g = list(mi.map_if(j, lambda x: x > 3, lambda x: 'toobig'))
        h = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 'toobig']
        self.assertEqual(g, h)

    def test_with_func_else(self):
        j = list(range(-5, 5))
        g = list(
            mi.map_if(
                j, lambda x: x >= 0, lambda x: 'notneg', lambda x: 'neg'
            )
        )
        h = ['neg'] * 5 + ['notneg'] * 5
        self.assertEqual(g, h)

    def test_empty(self):
        g = list(mi.map_if([], lambda x: len(x) > 5, lambda x: None))
        h = []
        self.assertEqual(g, h)


class SampleTests(TestCase):
    def test_specific_sample(self):
        """Verify reproducibility."""

        # Note, this test is surprisingly robust.  Although it depends on the quality
        # of the underlying libmath implementations for log, exp, and log1p, the
        # number of samples and population size are small enough that small errors
        # in those underlying functions won't affect the sample.

        seed(8675309)
        self.assertEqual(
            list(mi.sample(range(10**5), k=5)),
            [16845, 79805, 76057, 58302, 40472],
        )

        seed(8675309)
        self.assertEqual(
            list(mi.sample(range(10**5), counts=[1, 2] * (10**5 // 2), k=5)),
            [87899, 53203, 38868, 11230, 50705],
        )

        seed(8675309)
        self.assertEqual(
            list(mi.sample(range(10**5), weights=range(1, 10**5 + 1), k=5)),
            [50915, 33816, 32250, 98284, 43517],
        )

    def test_unit_case(self):
        """Test against a fixed case by seeding the random module."""
        # Beware that this test really just verifies random.random() behavior.
        # If the algorithm is changed (e.g. to a more naive implementation)
        # this test will fail, but the algorithm might be correct.
        # Also, this test can pass and the algorithm can be completely wrong.
        h = "abcdef"
        m = list(range(1, len(h) + 1))
        seed(123)
        g = mi.sample(h, k=2, weights=m)
        j = ['f', 'e']
        self.assertEqual(g, j)

    def test_negative(self):
        g = [1, 2, 3, 4, 5]
        with self.assertRaises(ValueError):
            mi.sample(g, k=-1)

    def test_length(self):
        """Check that *k* elements are sampled."""
        h = [1, 2, 3, 4, 5]
        for k in [0, 3, 5, 7]:
            m = mi.sample(h, k=k)
            g = len(m)
            j = min(k, len(h))
            self.assertEqual(g, j)

    def test_strict(self):
        g = ['1', '2', '3', '4', '5']
        self.assertEqual(set(mi.sample(g, 6, strict=False)), set(g))
        with self.assertRaises(ValueError):
            mi.sample(g, 6, strict=True)

    def test_counts(self):
        # Test with counts
        seed(0)
        o = ['red', 'blue']
        h = [4, 2]
        k = 5
        g = list(mi.sample(o, counts=h, k=k))

        # Test without counts
        seed(0)
        j = (['red'] * 4) + (['blue'] * 2)
        m = list(mi.sample(j, k=k))

        self.assertEqual(g, m)

    def test_counts_all(self):
        g = Counter(mi.sample('uwxyz', 35, counts=(1, 0, 4, 10, 20)))
        h = Counter({'u': 1, 'x': 4, 'y': 10, 'z': 20})
        self.assertEqual(g, h)

    def test_sampling_entire_iterable(self):
        """If k=len(iterable), the sample contains the original elements."""
        h = ["a", 2, "a", 4, (1, 2, 3)]
        g = set(mi.sample(h, k=len(h)))
        j = set(h)
        self.assertEqual(g, j)

    def test_scale_invariance_of_weights(self):
        """The probability of choosing element a_i is w_i / sum(weights).
        Scaling weights should not change the probability or outcome."""
        g = "abcdef"

        m = list(range(1, len(g) + 1))
        seed(123)
        h = mi.sample(g, k=2, weights=m)

        # Scale the weights and sample again
        o = [w / 1e10 for w in m]
        seed(123)
        j = mi.sample(g, k=2, weights=o)

        self.assertEqual(h, j)

    def test_invariance_under_permutations_unweighted(self):
        """The order of the data should not matter. This is a stochastic test,
        but it will fail in less than 1 / 10_000 cases."""

        # Create a data set and a reversed data set
        g = list(range(100))
        j = list(reversed(g))

        # Sample each data set 10 times
        h = [mean(mi.sample(g, k=50)) for _ in range(10)]
        m = [mean(mi.sample(j, k=50)) for _ in range(10)]

        # The difference in the means should be low, i.e. little bias
        o = abs(mean(h) - mean(m))

        # The observed largest difference in 10,000 simulations was 5.09599
        self.assertTrue(o < 5.1)

    def test_invariance_under_permutations_weighted(self):
        """The order of the data should not matter. This is a stochastic test,
        but it will fail in less than 1 / 10_000 cases."""

        # Create a data set and a reversed data set
        g = list(range(1, 101))
        j = list(reversed(g))

        # Sample each data set 10 times
        h = [
            mean(mi.sample(g, k=50, weights=g)) for _ in range(10)
        ]
        m = [
            mean(mi.sample(j, k=50, weights=j))
            for _ in range(10)
        ]

        # The difference in the means should be low, i.e. little bias
        o = abs(mean(h) - mean(m))

        # The observed largest difference in 10,000 simulations was 4.337999
        self.assertTrue(o < 4.4)

    def test_error_cases(self):
        # weights and counts are mutually exclusive
        with self.assertRaises(TypeError):
            mi.sample(
                'abcde', 3, weights=[1, 2, 3, 4, 5], counts=[1, 2, 3, 4, 5]
            )

        # Weighted sample larger than population
        with self.assertRaises(ValueError):
            mi.sample('abcde', 10, weights=[1, 2, 3, 4, 5], strict=True)

        # Counted sample larger than population
        with self.assertRaises(ValueError):
            mi.sample('abcde', 10, counts=[1, 1, 1, 1, 1], strict=True)


class BarelySortable:
    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        return self.value < other.value

    def __int__(self):
        return int(self.value)


class IsSortedTests(TestCase):
    def test_basic(self):
        for iterable, kwargs, expected in [
            ([], {}, True),
            ([1], {}, True),
            ([1, 2, 3], {}, True),
            ([1, 1, 2, 3], {}, True),
            ([1, 10, 2, 3], {}, False),
            (['1', '10', '2', '3'], {}, True),
            (['1', '10', '2', '3'], {'key': int}, False),
            ([1, 2, 3], {'reverse': True}, False),
            ([1, 1, 2, 3], {'reverse': True}, False),
            ([1, 10, 2, 3], {'reverse': True}, False),
            (['3', '2', '10', '1'], {'reverse': True}, True),
            (['3', '2', '10', '1'], {'key': int, 'reverse': True}, False),
            # strict
            ([], {'strict': True}, True),
            ([1], {'strict': True}, True),
            ([1, 1], {'strict': True}, False),
            ([1, 2, 3], {'strict': True}, True),
            ([1, 1, 2, 3], {'strict': True}, False),
            ([1, 10, 2, 3], {'strict': True}, False),
            (['1', '10', '2', '3'], {'strict': True}, True),
            (['1', '10', '2', '3', '3'], {'strict': True}, False),
            (['1', '10', '2', '3'], {'strict': True, 'key': int}, False),
            ([1, 2, 3], {'strict': True, 'reverse': True}, False),
            ([1, 1, 2, 3], {'strict': True, 'reverse': True}, False),
            ([1, 10, 2, 3], {'strict': True, 'reverse': True}, False),
            (['3', '2', '10', '1'], {'strict': True, 'reverse': True}, True),
            (
                ['3', '2', '10', '10', '1'],
                {'strict': True, 'reverse': True},
                False,
            ),
            (
                ['3', '2', '10', '1'],
                {'strict': True, 'key': int, 'reverse': True},
                False,
            ),
        ]:
            g = kwargs.get('key', None)
            m = kwargs.get('reverse', False)
            q = kwargs.get('strict', False)

            with self.subTest(
                iterable=iterable, key=g, reverse=m, strict=q
            ):
                h = mi.is_sorted(
                    map(BarelySortable, iterable),
                    key=g,
                    reverse=m,
                    strict=q,
                )

                o = sorted(iterable, key=g, reverse=m)
                if q:
                    o = list(mi.unique_justseen(o))

                j = iterable == o

                self.assertEqual(h, expected)
                self.assertEqual(h, j)


class CallbackIterTests(TestCase):
    def _target(self, cb=None, exc=None, wait=0):
        g = 0
        for i, c in enumerate('abc', 1):
            g += i
            if wait:
                sleep(wait)
            if cb:
                cb(i, c, intermediate_total=g)
            if exc:
                raise exc('error in target')

        return g

    def test_basic(self):
        g = lambda callback=None: self._target(cb=callback, wait=0.02)
        with mi.callback_iter(g, wait_seconds=0.01) as it:
            # Execution doesn't start until we begin iterating
            self.assertFalse(it.done)

            # Consume everything
            self.assertEqual(
                list(it),
                [
                    ((1, 'a'), {'intermediate_total': 1}),
                    ((2, 'b'), {'intermediate_total': 3}),
                    ((3, 'c'), {'intermediate_total': 6}),
                ],
            )

            # After consuming everything the future is done and the
            # result is available.
            self.assertTrue(it.done)
            self.assertEqual(it.result, 6)

        # This examines the internal state of the ThreadPoolExecutor. This
        # isn't documented, so may break in future Python versions.
        self.assertTrue(it._executor._shutdown)

    def test_callback_kwd(self):
        with mi.callback_iter(self._target, callback_kwd='cb') as it:
            self.assertEqual(
                list(it),
                [
                    ((1, 'a'), {'intermediate_total': 1}),
                    ((2, 'b'), {'intermediate_total': 3}),
                    ((3, 'c'), {'intermediate_total': 6}),
                ],
            )

    def test_partial_consumption(self):
        g = lambda callback=None: self._target(cb=callback)
        with mi.callback_iter(g) as it:
            self.assertEqual(next(it), ((1, 'a'), {'intermediate_total': 1}))

        self.assertTrue(it._executor._shutdown)

    def test_abort(self):
        g = lambda callback=None: self._target(cb=callback, wait=0.1)
        with mi.callback_iter(g) as it:
            self.assertEqual(next(it), ((1, 'a'), {'intermediate_total': 1}))

        with self.assertRaises(mi.AbortThread):
            it.result

    def test_no_result(self):
        g = lambda callback=None: self._target(cb=callback)
        with mi.callback_iter(g) as it:
            with self.assertRaises(RuntimeError):
                it.result

    def test_exception(self):
        g = lambda callback=None: self._target(cb=callback, exc=ValueError)
        with mi.callback_iter(g) as it:
            self.assertEqual(
                next(it),
                ((1, 'a'), {'intermediate_total': 1}),
            )

            with self.assertRaises(ValueError):
                it.result


class WindowedCompleteTests(TestCase):
    """Tests for ``windowed_complete()``"""

    def test_basic(self):
        g = list(mi.windowed_complete([1, 2, 3, 4, 5], 3))
        h = [
            ((), (1, 2, 3), (4, 5)),
            ((1,), (2, 3, 4), (5,)),
            ((1, 2), (3, 4, 5), ()),
        ]
        self.assertEqual(g, h)

    def test_zero_length(self):
        g = list(mi.windowed_complete([1, 2, 3], 0))
        h = [
            ((), (), (1, 2, 3)),
            ((1,), (), (2, 3)),
            ((1, 2), (), (3,)),
            ((1, 2, 3), (), ()),
        ]
        self.assertEqual(g, h)

    def test_wrong_length(self):
        g = [1, 2, 3, 4, 5]
        for n in (-10, -1, len(g) + 1, len(g) + 10):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    list(mi.windowed_complete(g, n))

    def test_every_partition(self):
        h = lambda m: chain(
            *map(partial(mi.windowed_complete, m), range(len(m)))
        )

        m = 'ABC'
        g = list(h(m))
        j = [
            ((), (), ('A', 'B', 'C')),
            (('A',), (), ('B', 'C')),
            (('A', 'B'), (), ('C',)),
            (('A', 'B', 'C'), (), ()),
            ((), ('A',), ('B', 'C')),
            (('A',), ('B',), ('C',)),
            (('A', 'B'), ('C',), ()),
            ((), ('A', 'B'), ('C',)),
            (('A',), ('B', 'C'), ()),
        ]
        self.assertEqual(g, j)


class AllUniqueTests(TestCase):
    def test_basic(self):
        for iterable, expected in [
            ([], True),
            ([1, 2, 3], True),
            ([1, 1], False),
            ([1, 2, 3, 1], False),
            ([1, 2, 3, '1'], True),
        ]:
            with self.subTest(args=(iterable,)):
                self.assertEqual(mi.all_unique(iterable), expected)

    def test_non_hashable(self):
        self.assertEqual(mi.all_unique([[1, 2], [3, 4]]), True)
        self.assertEqual(mi.all_unique([[1, 2], [3, 4], [1, 2]]), False)

    def test_partially_hashable(self):
        self.assertEqual(mi.all_unique([[1, 2], [3, 4], (5, 6)]), True)
        self.assertEqual(
            mi.all_unique([[1, 2], [3, 4], (5, 6), [1, 2]]), False
        )
        self.assertEqual(
            mi.all_unique([[1, 2], [3, 4], (5, 6), (5, 6)]), False
        )

    def test_key(self):
        g = ['A', 'B', 'C', 'b']
        self.assertEqual(mi.all_unique(g, lambda x: x), True)
        self.assertEqual(mi.all_unique(g, str.lower), False)

    def test_infinite(self):
        self.assertEqual(mi.all_unique(mi.prepend(3, count())), False)


class NthProductTests(TestCase):
    def test_basic(self):
        h = ['ab', 'cdef', 'ghi']
        for index, expected in enumerate(product(*h)):
            g = mi.nth_product(index, *h)
            self.assertEqual(g, expected)

    def test_long(self):
        g = mi.nth_product(1337, range(101), range(22), range(53))
        h = (1, 3, 12)
        self.assertEqual(g, h)

    def test_negative(self):
        h = ['abc', 'de', 'fghi']
        for index, expected in enumerate(product(*h)):
            g = mi.nth_product(index - 24, *h)
            self.assertEqual(g, expected)

    def test_invalid_index(self):
        with self.assertRaises(IndexError):
            mi.nth_product(24, 'ab', 'cde', 'fghi')

    def test_repeat(self):
        self.assertEqual(
            mi.nth_product(1234, 'abcde', repeat=5),
            mi.nth_product(1234, 'abcde', 'abcde', 'abcde', 'abcde', 'abcde'),
        )
        self.assertEqual(
            mi.nth_product(123, 'AB', 'CD', 'EFG', repeat=2),
            mi.nth_product(123, 'AB', 'CD', 'EFG', 'AB', 'CD', 'EFG'),
        )
        self.assertEqual(
            mi.nth_product(123, iter('AB'), iter('CD'), iter('EFG'), repeat=2),
            mi.nth_product(123, 'AB', 'CD', 'EFG', 'AB', 'CD', 'EFG'),
        )


class NthCombinationWithReplacementTests(TestCase):
    def test_basic(self):
        h = 'abcdefg'
        r = 4
        for index, expected in enumerate(
            combinations_with_replacement(h, r)
        ):
            g = mi.nth_combination_with_replacement(h, r, index)
            self.assertEqual(g, expected)
        self.assertEqual(
            mi.nth_combination_with_replacement('abcde', 7, 320),
            ('c', 'd', 'e', 'e', 'e', 'e', 'e'),
        )

    def test_long(self):
        g = mi.nth_combination_with_replacement(range(90), 4, 2000000)
        h = (22, 65, 68, 81)
        self.assertEqual(g, h)

    def test_invalid_r(self):
        with self.assertRaises(ValueError):
            mi.nth_combination_with_replacement([], -1, 0)

    def test_invalid_index(self):
        with self.assertRaises(IndexError):
            mi.nth_combination_with_replacement('abcdefg', 3, -85)
        with self.assertRaises(IndexError):
            mi.nth_combination_with_replacement('abcde', 7, 400)


class ValueChainTests(TestCase):
    def test_empty(self):
        g = list(mi.value_chain())
        h = []
        self.assertEqual(g, h)

    def test_simple(self):
        g = list(mi.value_chain(1, 2.71828, False, 'foo'))
        h = [1, 2.71828, False, 'foo']
        self.assertEqual(g, h)

    def test_more(self):
        g = list(mi.value_chain(b'bar', [1, 2, 3], 4, {'key': 1}))
        h = [b'bar', 1, 2, 3, 4, 'key']
        self.assertEqual(g, h)

    def test_empty_lists(self):
        g = list(mi.value_chain(1, 2, [], [3, 4]))
        h = [1, 2, 3, 4]
        self.assertEqual(g, h)

    def test_complex(self):
        j = object()
        g = list(
            mi.value_chain(
                (1, (2, (3,))),
                ['foo', ['bar', ['baz']], 'tic'],
                {'key': {'foo': 1}},
                j,
            )
        )
        h = [1, (2, (3,)), 'foo', ['bar', ['baz']], 'tic', 'key', j]
        self.assertEqual(g, h)


class ProductIndexTests(TestCase):
    def test_basic(self):
        m = ['ab', 'cdef', 'ghi']
        j = {}
        for index, element in enumerate(product(*m)):
            g = mi.product_index(element, *m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_multiplicity(self):
        m = ['ab', 'bab', 'cab']
        j = {}
        for index, element in enumerate(product(*m)):
            g = mi.product_index(element, *m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_long(self):
        g = mi.product_index((1, 3, 12), range(101), range(22), range(53))
        h = 1337
        self.assertEqual(g, h)

    def test_invalid_empty(self):
        with self.assertRaises(ValueError):
            mi.product_index('', 'ab', 'cde', 'fghi')

    def test_invalid_small(self):
        with self.assertRaises(ValueError):
            mi.product_index('ac', 'ab', 'cde', 'fghi')

    def test_invalid_large(self):
        with self.assertRaises(ValueError):
            mi.product_index('achi', 'ab', 'cde', 'fghi')

    def test_invalid_match(self):
        with self.assertRaises(ValueError):
            mi.product_index('axf', 'ab', 'cde', 'fghi')

    def test_iterator_input(self):
        self.assertEqual(
            mi.product_index(iter(['i', 'a']), iter('snicker'), iter('snack')),
            12,
        )

    def test_repeat(self):
        self.assertEqual(
            mi.product_index([1, 2, 3, 4], range(10), repeat=4),
            mi.product_index(
                [1, 2, 3, 4], range(10), range(10), range(10), range(10)
            ),
        )
        g = ['B', 'D', 'E', 'A', 'C', 'G']
        self.assertEqual(
            mi.product_index(g, 'AB', 'CD', 'EFG', repeat=2),
            mi.product_index(g, 'AB', 'CD', 'EFG', 'AB', 'CD', 'EFG'),
        )
        self.assertEqual(
            mi.product_index(
                iter(g), iter('AB'), iter('CD'), iter('EFG'), repeat=2
            ),
            mi.product_index(g, 'AB', 'CD', 'EFG', 'AB', 'CD', 'EFG'),
        )


class CombinationIndexTests(TestCase):
    def test_r_less_than_n(self):
        m = 'abcdefg'
        r = 4
        j = {}
        for index, element in enumerate(combinations(m, r)):
            g = mi.combination_index(element, m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_r_equal_to_n(self):
        m = 'abcd'
        r = len(m)
        j = {}
        for index, element in enumerate(combinations(m, r=r)):
            g = mi.combination_index(element, m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_multiplicity(self):
        m = 'abacba'
        r = 3
        j = {}
        for index, element in enumerate(combinations(m, r)):
            g = mi.combination_index(element, m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_null(self):
        g = mi.combination_index(tuple(), [])
        h = 0
        self.assertEqual(g, h)

    def test_long(self):
        g = mi.combination_index((2, 12, 35, 126), range(180))
        h = 2000000
        self.assertEqual(g, h)

    def test_invalid_order(self):
        with self.assertRaises(ValueError):
            mi.combination_index(tuple('acb'), 'abcde')

    def test_invalid_large(self):
        with self.assertRaises(ValueError):
            mi.combination_index(tuple('abcdefg'), 'abcdef')

    def test_invalid_match(self):
        with self.assertRaises(ValueError):
            mi.combination_index(tuple('axe'), 'abcde')


class CombinationWithReplacementIndexTests(TestCase):
    def test_r_less_than_n(self):
        m = 'abcdefg'
        r = 4
        j = {}
        for index, element in enumerate(
            combinations_with_replacement(m, r)
        ):
            g = mi.combination_with_replacement_index(element, m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_r_equal_to_n(self):
        m = 'abcd'
        r = len(m)
        j = {}
        for index, element in enumerate(
            combinations_with_replacement(m, r=r)
        ):
            g = mi.combination_with_replacement_index(element, m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_multiplicity(self):
        m = 'abacba'
        r = 3
        j = {}
        for index, element in enumerate(
            combinations_with_replacement(m, r)
        ):
            g = mi.combination_with_replacement_index(element, m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_null(self):
        g = mi.combination_with_replacement_index(tuple(), [])
        h = 0
        self.assertEqual(g, h)

    def test_long(self):
        g = mi.combination_with_replacement_index(
            (22, 65, 68, 81), range(90)
        )
        h = 2000000
        self.assertEqual(g, h)

    def test_invalid_order(self):
        with self.assertRaises(ValueError):
            mi.combination_with_replacement_index(tuple('acb'), 'abcde')

    def test_invalid_large(self):
        with self.assertRaises(ValueError):
            mi.combination_with_replacement_index(tuple('abcdefg'), 'abcdef')

    def test_invalid_match(self):
        with self.assertRaises(ValueError):
            mi.combination_with_replacement_index(tuple('axe'), 'abcde')


class PermutationIndexTests(TestCase):
    def test_r_less_than_n(self):
        m = 'abcdefg'
        r = 4
        j = {}
        for index, element in enumerate(permutations(m, r)):
            g = mi.permutation_index(element, m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_r_equal_to_n(self):
        m = 'abcd'
        j = {}
        for index, element in enumerate(permutations(m)):
            g = mi.permutation_index(element, m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_multiplicity(self):
        m = 'abacba'
        r = 3
        j = {}
        for index, element in enumerate(permutations(m, r)):
            g = mi.permutation_index(element, m)
            h = j.setdefault(element, index)
            self.assertEqual(g, h)

    def test_null(self):
        g = mi.permutation_index(tuple(), [])
        h = 0
        self.assertEqual(g, h)

    def test_long(self):
        g = mi.permutation_index((2, 12, 35, 126), range(180))
        h = 11631678
        self.assertEqual(g, h)

    def test_invalid_large(self):
        with self.assertRaises(ValueError):
            mi.permutation_index(tuple('abcdefg'), 'abcdef')

    def test_invalid_match(self):
        with self.assertRaises(ValueError):
            mi.permutation_index(tuple('axe'), 'abcde')


class CountableTests(TestCase):
    def test_empty(self):
        h = []
        g = mi.countable(h)
        self.assertEqual(g.items_seen, 0)
        self.assertEqual(list(g), [])

    def test_basic(self):
        h = '0123456789'
        g = mi.countable(h)
        self.assertEqual(g.items_seen, 0)
        self.assertEqual(next(g), '0')
        self.assertEqual(g.items_seen, 1)
        self.assertEqual(''.join(g), '123456789')
        self.assertEqual(g.items_seen, 10)


class ChunkedEvenTests(TestCase):
    """Tests for ``chunked_even()``"""

    def test_0(self):
        self._test_finite('', 3, [])

    def test_1(self):
        self._test_finite('A', 1, [['A']])

    def test_4(self):
        self._test_finite('ABCD', 3, [['A', 'B'], ['C', 'D']])

    def test_5(self):
        self._test_finite('ABCDE', 3, [['A', 'B', 'C'], ['D', 'E']])

    def test_6(self):
        self._test_finite('ABCDEF', 3, [['A', 'B', 'C'], ['D', 'E', 'F']])

    def test_7(self):
        self._test_finite(
            'ABCDEFG', 3, [['A', 'B', 'C'], ['D', 'E'], ['F', 'G']]
        )

    def _test_finite(self, seq, n, expected):
        # Check with and without `len()`
        self.assertEqual(list(mi.chunked_even(seq, n)), expected)
        self.assertEqual(list(mi.chunked_even(iter(seq), n)), expected)

    def test_infinite(self):
        for n in range(1, 5):
            k = 0

            def count_with_assert():
                for i in count():
                    # Look-ahead should be less than n^2
                    self.assertLessEqual(i, n * k + n * n)
                    yield i

            g = mi.chunked_even(count_with_assert(), n)
            while k < 2:
                self.assertEqual(next(g), list(range(k * n, (k + 1) * n)))
                k += 1

    def test_evenness(self):
        for N in range(1, 50):
            for n in range(1, N + 2):
                h = []
                g = []
                for l in mi.chunked_even(range(N), n):
                    L = len(l)
                    self.assertLessEqual(L, n)
                    self.assertGreaterEqual(L, 1)
                    h.append(L)
                    g.extend(l)
                self.assertEqual(g, list(range(N)))
                self.assertLessEqual(max(h) - min(h), 1)


class ZipBroadcastTests(TestCase):
    def test_zip(self):
        for objects, zipped, strict_ok in [
            # Empty
            ([], [], True),
            # One argument
            ([1], [(1,)], True),
            ([[1]], [(1,)], True),
            ([[1, 2]], [(1,), (2,)], True),
            # All scalars
            ([1, 2], [(1, 2)], True),
            ([1, 2, 3], [(1, 2, 3)], True),
            # Iterables with length = 0
            ([[], 1], [], True),
            ([1, []], [], True),
            ([[], []], [], True),
            ([[], 1, 2], [], True),
            ([[], 1, []], [], True),
            ([1, [], 2], [], True),
            ([1, [], []], [], True),
            ([[], [], 1], [], True),
            ([[], [], []], [], True),
            # Iterables with length = 1
            ([1, [2]], [(1, 2)], True),
            ([[1], 2], [(1, 2)], True),
            ([[1], [2]], [(1, 2)], True),
            ([1, [2], 3], [(1, 2, 3)], True),
            ([1, [2], [3]], [(1, 2, 3)], True),
            ([[1], 2, 3], [(1, 2, 3)], True),
            ([[1], 2, [3]], [(1, 2, 3)], True),
            ([[1], [2], 3], [(1, 2, 3)], True),
            ([[1], [2], [3]], [(1, 2, 3)], True),
            # Iterables with length > 1
            ([1, [2, 3]], [(1, 2), (1, 3)], True),
            ([[1, 2], 3], [(1, 3), (2, 3)], True),
            ([[1, 2], [3, 4]], [(1, 3), (2, 4)], True),
            ([1, [2, 3], 4], [(1, 2, 4), (1, 3, 4)], True),
            ([1, [2, 3], [4, 5]], [(1, 2, 4), (1, 3, 5)], True),
            ([[1, 2], 3, 4], [(1, 3, 4), (2, 3, 4)], True),
            ([[1, 2], 3, [4, 5]], [(1, 3, 4), (2, 3, 5)], True),
            ([[1, 2], [3, 4], 5], [(1, 3, 5), (2, 4, 5)], True),
            ([[1, 2], [3, 4], [5, 6]], [(1, 3, 5), (2, 4, 6)], True),
            # Iterables with different lengths
            ([[], [1]], [], False),
            ([[1], []], [], False),
            ([[1], [2, 3]], [(1, 2)], False),
            ([[1, 2], [3]], [(1, 3)], False),
            ([[1, 2], [3], [4]], [(1, 3, 4)], False),
            ([[1], [2, 3], [4]], [(1, 2, 4)], False),
            ([[1], [2], [3, 4]], [(1, 2, 3)], False),
            ([[1], [2, 3], [4, 5]], [(1, 2, 4)], False),
            ([[1, 2], [3], [4, 5]], [(1, 3, 4)], False),
            ([[1, 2], [3, 4], [5]], [(1, 3, 5)], False),
            ([1, [2, 3], [4, 5, 6]], [(1, 2, 4), (1, 3, 5)], False),
            ([[1, 2], 3, [4, 5, 6]], [(1, 3, 4), (2, 3, 5)], False),
            ([1, [2, 3, 4], [5, 6]], [(1, 2, 5), (1, 3, 6)], False),
            ([[1, 2, 3], 4, [5, 6]], [(1, 4, 5), (2, 4, 6)], False),
            ([[1, 2], [3, 4, 5], 6], [(1, 3, 6), (2, 4, 6)], False),
            ([[1, 2, 3], [4, 5], 6], [(1, 4, 6), (2, 5, 6)], False),
            # Infinite
            ([count(), 1, [2]], [(0, 1, 2)], False),
            ([count(), 1, [2, 3]], [(0, 1, 2), (1, 1, 3)], False),
            # Miscellaneous
            (['a', [1, 2], [3, 4, 5]], [('a', 1, 3), ('a', 2, 4)], False),
        ]:
            # Truncate by default
            with self.subTest(objects=objects, strict=False, zipped=zipped):
                self.assertEqual(list(mi.zip_broadcast(*objects)), zipped)

            # Raise an exception for strict=True
            with self.subTest(objects=objects, strict=True, zipped=zipped):
                if strict_ok:
                    self.assertEqual(
                        list(mi.zip_broadcast(*objects, strict=True)),
                        zipped,
                    )
                else:
                    with self.assertRaises(ValueError):
                        list(mi.zip_broadcast(*objects, strict=True))

    def test_scalar_types(self):
        # Default: str and bytes are treated as scalar
        self.assertEqual(
            list(mi.zip_broadcast('ab', [1, 2, 3])),
            [('ab', 1), ('ab', 2), ('ab', 3)],
        )
        self.assertEqual(
            list(mi.zip_broadcast(b'ab', [1, 2, 3])),
            [(b'ab', 1), (b'ab', 2), (b'ab', 3)],
        )
        # scalar_types=None allows str and bytes to be treated as iterable
        self.assertEqual(
            list(mi.zip_broadcast('abc', [1, 2, 3], scalar_types=None)),
            [('a', 1), ('b', 2), ('c', 3)],
        )
        # Use a custom type
        self.assertEqual(
            list(mi.zip_broadcast({'a': 'b'}, [1, 2, 3], scalar_types=dict)),
            [({'a': 'b'}, 1), ({'a': 'b'}, 2), ({'a': 'b'}, 3)],
        )


class UniqueInWindowTests(TestCase):
    def test_invalid_n(self):
        with self.assertRaises(ValueError):
            list(mi.unique_in_window([], 0))

    def test_basic(self):
        for iterable, n, expected in [
            (range(9), 10, list(range(9))),
            (range(20), 10, list(range(20))),
            ([1, 2, 3, 4, 4, 4], 1, [1, 2, 3, 4, 4, 4]),
            ([1, 2, 3, 4, 4, 4], 2, [1, 2, 3, 4]),
            ([1, 2, 3, 4, 4, 4], 3, [1, 2, 3, 4]),
            ([1, 2, 3, 4, 4, 4], 4, [1, 2, 3, 4]),
            ([1, 2, 3, 4, 4, 4], 5, [1, 2, 3, 4]),
            (
                [0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 2, 3, 4, 2],
                2,
                [0, 1, 0, 2, 3, 4, 2],
            ),
        ]:
            with self.subTest(expected=expected):
                g = list(mi.unique_in_window(iterable, n))
                self.assertEqual(g, expected)

    def test_key(self):
        j = [0, 1, 3, 4, 5, 6, 7, 8, 9]
        n = 3
        m = lambda x: x // 3
        g = list(mi.unique_in_window(j, n, key=m))
        h = [0, 3, 6, 9]
        self.assertEqual(g, h)


class StrictlyNTests(TestCase):
    def test_basic(self):
        j = ['a', 'b', 'c', 'd']
        n = 4
        g = list(mi.strictly_n(iter(j), n))
        h = j
        self.assertEqual(g, h)

    def test_too_short_default(self):
        g = ['a', 'b', 'c', 'd']
        n = 5
        with self.assertRaises(ValueError) as exc:
            list(mi.strictly_n(iter(g), n))

        self.assertEqual(
            'Too few items in iterable (got 4)', exc.exception.args[0]
        )

    def test_too_long_default(self):
        g = ['a', 'b', 'c', 'd']
        n = 3
        with self.assertRaises(ValueError) as cm:
            list(mi.strictly_n(iter(g), n))

        self.assertEqual(
            'Too many items in iterable (got at least 4)',
            cm.exception.args[0],
        )

    def test_too_short_custom(self):
        h = 0

        def too_short(item_count):
            nonlocal h
            h += 1

        o = ['a', 'b', 'c', 'd']
        n = 6
        g = []
        for m in mi.strictly_n(iter(o), n, too_short=too_short):
            g.append(m)
        j = ['a', 'b', 'c', 'd']
        self.assertEqual(g, j)
        self.assertEqual(h, 1)

    def test_too_long_custom(self):
        import logging

        h = ['a', 'b', 'c', 'd']
        n = 2
        j = lambda item_count: logging.warning(
            'Picked the first %s items', n
        )

        with self.assertLogs(level='WARNING') as cm:
            g = list(mi.strictly_n(iter(h), n, too_long=j))

        self.assertEqual(g, ['a', 'b'])
        self.assertIn('Picked the first 2 items', cm.output[0])


class DuplicatesEverSeenTests(TestCase):
    def test_basic(self):
        for iterable, expected in [
            ([], []),
            ([1, 2, 3], []),
            ([1, 1], [1]),
            ([1, 2, 1, 2], [1, 2]),
            ([1, 2, 3, '1'], []),
        ]:
            with self.subTest(args=(iterable,)):
                self.assertEqual(
                    list(mi.duplicates_everseen(iterable)), expected
                )

    def test_non_hashable(self):
        self.assertEqual(list(mi.duplicates_everseen([[1, 2], [3, 4]])), [])
        self.assertEqual(
            list(mi.duplicates_everseen([[1, 2], [3, 4], [1, 2]])), [[1, 2]]
        )

    def test_partially_hashable(self):
        self.assertEqual(
            list(mi.duplicates_everseen([[1, 2], [3, 4], (5, 6)])), []
        )
        self.assertEqual(
            list(mi.duplicates_everseen([[1, 2], [3, 4], (5, 6), [1, 2]])),
            [[1, 2]],
        )
        self.assertEqual(
            list(mi.duplicates_everseen([[1, 2], [3, 4], (5, 6), (5, 6)])),
            [(5, 6)],
        )

    def test_key_hashable(self):
        g = 'HEheHEhe'
        self.assertEqual(list(mi.duplicates_everseen(g)), list('HEhe'))
        self.assertEqual(
            list(mi.duplicates_everseen(g, str.lower)),
            list('heHEhe'),
        )

    def test_key_non_hashable(self):
        g = [[1, 2], [3, 0], [5, -2], [5, 6]]
        self.assertEqual(
            list(mi.duplicates_everseen(g, lambda x: x)), []
        )
        self.assertEqual(
            list(mi.duplicates_everseen(g, sum)), [[3, 0], [5, -2]]
        )

    def test_key_partially_hashable(self):
        g = [[1, 2], (1, 2), [1, 2], [5, 6]]
        self.assertEqual(
            list(mi.duplicates_everseen(g, lambda x: x)), [[1, 2]]
        )
        self.assertEqual(
            list(mi.duplicates_everseen(g, list)), [(1, 2), [1, 2]]
        )


class DuplicatesJustSeenTests(TestCase):
    def test_basic(self):
        for iterable, expected in [
            ([], []),
            ([1, 2, 3, 3, 2, 2], [3, 2]),
            ([1, 1], [1]),
            ([1, 2, 1, 2], []),
            ([1, 2, 3, '1'], []),
        ]:
            with self.subTest(args=(iterable,)):
                self.assertEqual(
                    list(mi.duplicates_justseen(iterable)), expected
                )

    def test_non_hashable(self):
        self.assertEqual(list(mi.duplicates_justseen([[1, 2], [3, 4]])), [])
        self.assertEqual(
            list(
                mi.duplicates_justseen(
                    [[1, 2], [3, 4], [3, 4], [3, 4], [1, 2]]
                )
            ),
            [[3, 4], [3, 4]],
        )

    def test_partially_hashable(self):
        self.assertEqual(
            list(mi.duplicates_justseen([[1, 2], [3, 4], (5, 6)])), []
        )
        self.assertEqual(
            list(
                mi.duplicates_justseen(
                    [[1, 2], [3, 4], (5, 6), [1, 2], [1, 2]]
                )
            ),
            [[1, 2]],
        )
        self.assertEqual(
            list(
                mi.duplicates_justseen(
                    [[1, 2], [3, 4], (5, 6), (5, 6), (5, 6)]
                )
            ),
            [(5, 6), (5, 6)],
        )

    def test_key_hashable(self):
        g = 'HEheHHHhEheeEe'
        self.assertEqual(list(mi.duplicates_justseen(g)), list('HHe'))
        self.assertEqual(
            list(mi.duplicates_justseen(g, str.lower)),
            list('HHheEe'),
        )

    def test_key_non_hashable(self):
        g = [[1, 2], [3, 0], [5, -2], [5, 6], [1, 2]]
        self.assertEqual(
            list(mi.duplicates_justseen(g, lambda x: x)), []
        )
        self.assertEqual(
            list(mi.duplicates_justseen(g, sum)), [[3, 0], [5, -2]]
        )

    def test_key_partially_hashable(self):
        g = [[1, 2], (1, 2), [1, 2], [5, 6], [1, 2]]
        self.assertEqual(
            list(mi.duplicates_justseen(g, lambda x: x)), []
        )
        self.assertEqual(
            list(mi.duplicates_justseen(g, list)), [(1, 2), [1, 2]]
        )

    def test_nested(self):
        g = [[[1, 2], [1, 2]], [5, 6], [5, 6]]
        self.assertEqual(list(mi.duplicates_justseen(g)), [[5, 6]])


class ClassifyUniqueTests(TestCase):
    def test_basic(self):
        self.assertEqual(
            list(mi.classify_unique('mississippi')),
            [
                ('m', True, True),
                ('i', True, True),
                ('s', True, True),
                ('s', False, False),
                ('i', True, False),
                ('s', True, False),
                ('s', False, False),
                ('i', True, False),
                ('p', True, True),
                ('p', False, False),
                ('i', True, False),
            ],
        )

    def test_non_hashable(self):
        self.assertEqual(
            list(mi.classify_unique([[1, 2], [3, 4], [3, 4], [1, 2]])),
            [
                ([1, 2], True, True),
                ([3, 4], True, True),
                ([3, 4], False, False),
                ([1, 2], True, False),
            ],
        )

    def test_partially_hashable(self):
        self.assertEqual(
            list(
                mi.classify_unique(
                    [[1, 2], [3, 4], (5, 6), (5, 6), (3, 4), [1, 2]]
                )
            ),
            [
                ([1, 2], True, True),
                ([3, 4], True, True),
                ((5, 6), True, True),
                ((5, 6), False, False),
                ((3, 4), True, True),
                ([1, 2], True, False),
            ],
        )

    def test_key_hashable(self):
        g = 'HEheHHHhEheeEe'
        self.assertEqual(
            list(mi.classify_unique(g)),
            [
                ('H', True, True),
                ('E', True, True),
                ('h', True, True),
                ('e', True, True),
                ('H', True, False),
                ('H', False, False),
                ('H', False, False),
                ('h', True, False),
                ('E', True, False),
                ('h', True, False),
                ('e', True, False),
                ('e', False, False),
                ('E', True, False),
                ('e', True, False),
            ],
        )
        self.assertEqual(
            list(mi.classify_unique(g, str.lower)),
            [
                ('H', True, True),
                ('E', True, True),
                ('h', True, False),
                ('e', True, False),
                ('H', True, False),
                ('H', False, False),
                ('H', False, False),
                ('h', False, False),
                ('E', True, False),
                ('h', True, False),
                ('e', True, False),
                ('e', False, False),
                ('E', False, False),
                ('e', False, False),
            ],
        )

    def test_key_non_hashable(self):
        g = [[1, 2], [3, 0], [5, -2], [5, 6], [1, 2]]
        self.assertEqual(
            list(mi.classify_unique(g, lambda x: x)),
            [
                ([1, 2], True, True),
                ([3, 0], True, True),
                ([5, -2], True, True),
                ([5, 6], True, True),
                ([1, 2], True, False),
            ],
        )
        self.assertEqual(
            list(mi.classify_unique(g, sum)),
            [
                ([1, 2], True, True),
                ([3, 0], False, False),
                ([5, -2], False, False),
                ([5, 6], True, True),
                ([1, 2], True, False),
            ],
        )

    def test_key_partially_hashable(self):
        g = [[1, 2], (1, 2), [1, 2], [5, 6], [1, 2]]
        self.assertEqual(
            list(mi.classify_unique(g, lambda x: x)),
            [
                ([1, 2], True, True),
                ((1, 2), True, True),
                ([1, 2], True, False),
                ([5, 6], True, True),
                ([1, 2], True, False),
            ],
        )
        self.assertEqual(
            list(mi.classify_unique(g, list)),
            [
                ([1, 2], True, True),
                ((1, 2), False, False),
                ([1, 2], False, False),
                ([5, 6], True, True),
                ([1, 2], True, False),
            ],
        )

    def test_vs_unique_everseen(self):
        input = 'AAAABBBBCCDAABBB'
        g = [e for e, j, u in mi.classify_unique(input) if u]
        self.assertEqual(g, ['A', 'B', 'C', 'D'])
        self.assertEqual(list(mi.unique_everseen(input)), g)

    def test_vs_unique_everseen_key(self):
        input = 'aAbACCc'
        g = [e for e, j, u in mi.classify_unique(input, str.lower) if u]
        self.assertEqual(g, list('abC'))
        self.assertEqual(list(mi.unique_everseen(input, str.lower)), g)

    def test_vs_unique_justseen(self):
        input = 'AAAABBBCCDABB'
        g = [e for e, j, u in mi.classify_unique(input) if j]
        self.assertEqual(g, list('ABCDAB'))
        self.assertEqual(list(mi.unique_justseen(input)), g)

    def test_vs_unique_justseen_key(self):
        input = 'AABCcAD'
        g = [e for e, j, u in mi.classify_unique(input, str.lower) if j]
        self.assertEqual(g, list('ABCAD'))
        self.assertEqual(list(mi.unique_justseen(input, str.lower)), g)

    def test_vs_duplicates_everseen(self):
        input = [1, 2, 1, 2]
        g = [e for e, j, u in mi.classify_unique(input) if not u]
        self.assertEqual(g, [1, 2])
        self.assertEqual(list(mi.duplicates_everseen(input)), g)

    def test_vs_duplicates_everseen_key(self):
        input = 'HEheHEhe'
        g = [
            e for e, j, u in mi.classify_unique(input, str.lower) if not u
        ]
        self.assertEqual(g, list('heHEhe'))
        self.assertEqual(
            list(mi.duplicates_everseen(input, str.lower)), g
        )

    def test_vs_duplicates_justseen(self):
        input = [1, 2, 3, 3, 2, 2]
        g = [e for e, j, u in mi.classify_unique(input) if not j]
        self.assertEqual(g, [3, 2])
        self.assertEqual(list(mi.duplicates_justseen(input)), g)

    def test_vs_duplicates_justseen_key(self):
        input = 'HEheHHHhEheeEe'
        g = [
            e for e, j, u in mi.classify_unique(input, str.lower) if not j
        ]
        self.assertEqual(g, list('HHheEe'))
        self.assertEqual(
            list(mi.duplicates_justseen(input, str.lower)), g
        )


class LongestCommonPrefixTests(TestCase):
    def test_basic(self):
        g = [[1, 2], [1, 2, 3], [1, 2, 4]]
        self.assertEqual(list(mi.longest_common_prefix(g)), [1, 2])

    def test_iterators(self):
        g = iter([iter([1, 2]), iter([1, 2, 3]), iter([1, 2, 4])])
        self.assertEqual(list(mi.longest_common_prefix(g)), [1, 2])

    def test_no_iterables(self):
        g = []
        self.assertEqual(list(mi.longest_common_prefix(g)), [])

    def test_empty_iterables_only(self):
        g = [[], [], []]
        self.assertEqual(list(mi.longest_common_prefix(g)), [])

    def test_includes_empty_iterables(self):
        g = [[1, 2], [1, 2, 3], [1, 2, 4], []]
        self.assertEqual(list(mi.longest_common_prefix(g)), [])

    def test_non_hashable(self):
        # See https://github.com/more-itertools/more-itertools/issues/603
        g = [[[1], [2]], [[1], [2], [3]], [[1], [2], [4]]]
        self.assertEqual(list(mi.longest_common_prefix(g)), [[1], [2]])

    def test_prefix_contains_elements_of_the_first_iterable(self):
        g = [[[1], [2]], [[1], [2], [3]], [[1], [2], [4]]]
        h = list(mi.longest_common_prefix(g))
        self.assertIs(h[0], g[0][0])
        self.assertIs(h[1], g[0][1])
        self.assertIsNot(h[0], g[1][0])
        self.assertIsNot(h[1], g[1][1])
        self.assertIsNot(h[0], g[2][0])
        self.assertIsNot(h[1], g[2][1])

    def test_infinite_iterables(self):
        g = mi.longest_common_prefix([count(), count()])
        self.assertEqual(next(g), 0)
        self.assertEqual(next(g), 1)
        self.assertEqual(next(g), 2)

    def test_contains_infinite_iterables(self):
        g = [[0, 1, 2], count()]
        self.assertEqual(list(mi.longest_common_prefix(g)), [0, 1, 2])


class IequalsTests(TestCase):
    def test_basic(self):
        self.assertTrue(mi.iequals("abc", iter("abc")))
        self.assertTrue(mi.iequals(range(3), [0, 1, 2]))
        self.assertFalse(mi.iequals("abc", [0, 1, 2]))

    def test_no_iterables(self):
        self.assertTrue(mi.iequals())

    def test_one_iterable(self):
        self.assertTrue(mi.iequals("abc"))

    def test_more_than_two_iterable(self):
        self.assertTrue(mi.iequals("abc", iter("abc"), ['a', 'b', 'c']))
        self.assertFalse(mi.iequals("abc", iter("abc"), ['a', 'b', 'd']))

    def test_order_matters(self):
        self.assertFalse(mi.iequals("abc", "acb"))

    def test_not_equal_lengths(self):
        self.assertFalse(mi.iequals("abc", "ab"))
        self.assertFalse(mi.iequals("abc", "bc"))
        self.assertFalse(mi.iequals("aaa", "aaaa"))

    def test_empty_iterables(self):
        self.assertTrue(mi.iequals([], ""))

    def test_none_is_not_a_sentinel(self):
        # See https://stackoverflow.com/a/900444
        self.assertFalse(mi.iequals([1, 2], [1, 2, None]))
        self.assertFalse(mi.iequals([1, 2], [None, 1, 2]))

    def test_not_identical_but_equal(self):
        self.assertTrue([1, True], [1.0, complex(1, 0)])

    def test_fillvalue_not_fakeable(self):
        # See https://github.com/more-itertools/more-itertools/issues/900
        self.assertFalse(mi.iequals([], [mock.ANY]))


class ConstrainedBatchesTests(TestCase):
    def test_basic(self):
        h = [
            'Beautiful is better than ugly',
            'Explicit is better than implicit',
            'Simple is better than complex',
            'Complex is better than complicated',
            'Flat is better than nested',
            'Sparse is better than dense',
            'Readability counts',
        ]
        for size, expected in (
            (
                34,
                [
                    (h[0],),
                    (h[1],),
                    (h[2],),
                    (h[3],),
                    (h[4],),
                    (h[5],),
                    (h[6],),
                ],
            ),
            (
                61,
                [
                    (h[0], h[1]),
                    (h[2],),
                    (h[3], h[4]),
                    (h[5], h[6]),
                ],
            ),
            (
                90,
                [
                    (h[0], h[1], h[2]),
                    (h[3], h[4], h[5]),
                    (h[6],),
                ],
            ),
            (
                124,
                [(h[0], h[1], h[2], h[3]), (h[4], h[5], h[6])],
            ),
            (
                150,
                [(h[0], h[1], h[2], h[3], h[4]), (h[5], h[6])],
            ),
            (
                177,
                [(h[0], h[1], h[2], h[3], h[4], h[5]), (h[6],)],
            ),
        ):
            with self.subTest(size=size):
                g = list(mi.constrained_batches(iter(h), size))
                self.assertEqual(g, expected)

    def test_max_count(self):
        j = ['1', '1', '12345678', '12345', '12345']
        o = 10
        m = 2
        g = list(mi.constrained_batches(j, o, m))
        h = [('1', '1'), ('12345678',), ('12345', '12345')]
        self.assertEqual(g, h)

    def test_strict(self):
        j = ['1', '123456789', '1']
        m = 8
        with self.assertRaises(ValueError):
            list(mi.constrained_batches(j, m))

        g = list(mi.constrained_batches(j, m, strict=False))
        h = [('1',), ('123456789',), ('1',)]
        self.assertEqual(g, h)

    def test_get_len(self):
        class Record(tuple):
            def total_size(self):
                return sum(len(x) for x in self)

        m = Record(('1', '23'))
        o = Record(('1234', '1'))
        h = Record(('1', '12345678', '1'))
        j = Record(('1', '1'))
        g = [m, o, h, j]

        self.assertEqual(
            list(
                mi.constrained_batches(
                    g, 10, get_len=lambda x: x.total_size()
                )
            ),
            [(m, o), (h,), (j,)],
        )

    def test_bad_max(self):
        with self.assertRaises(ValueError):
            list(mi.constrained_batches([], 0))


class GrayProductTests(TestCase):
    def test_basic(self):
        self.assertEqual(
            tuple(mi.gray_product(('a', 'b', 'c'), range(1, 3))),
            (("a", 1), ("b", 1), ("c", 1), ("c", 2), ("b", 2), ("a", 2)),
        )
        g = mi.gray_product(('foo', 'bar'), (3, 4, 5, 6), ['quz', 'baz'])
        self.assertEqual(next(g), ('foo', 3, 'quz'))
        self.assertEqual(
            list(g),
            [
                ('bar', 3, 'quz'),
                ('bar', 4, 'quz'),
                ('foo', 4, 'quz'),
                ('foo', 5, 'quz'),
                ('bar', 5, 'quz'),
                ('bar', 6, 'quz'),
                ('foo', 6, 'quz'),
                ('foo', 6, 'baz'),
                ('bar', 6, 'baz'),
                ('bar', 5, 'baz'),
                ('foo', 5, 'baz'),
                ('foo', 4, 'baz'),
                ('bar', 4, 'baz'),
                ('bar', 3, 'baz'),
                ('foo', 3, 'baz'),
            ],
        )
        self.assertEqual(tuple(mi.gray_product()), ((),))
        self.assertEqual(tuple(mi.gray_product((1, 2))), ((1,), (2,)))

    def test_errors(self):
        with self.assertRaises(ValueError):
            list(mi.gray_product((1, 2), ()))
        with self.assertRaises(ValueError):
            list(mi.gray_product((1, 2), (2,)))

    def test_vs_product(self):
        g = (
            ("a", "b"),
            range(3, 6),
            [None, None],
            {"i", "j", "k", "l"},
            "XYZ",
        )
        self.assertEqual(
            sorted(product(*g)), sorted(mi.gray_product(*g))
        )

    def test_repeat(self):
        self.assertEqual(
            list(mi.gray_product('ABC', repeat=5)),
            list(mi.gray_product('ABC', 'ABC', 'ABC', 'ABC', 'ABC')),
        )
        self.assertEqual(
            list(mi.gray_product('ABC', 'DE', repeat=5)),
            list(
                mi.gray_product(
                    'ABC',
                    'DE',
                    'ABC',
                    'DE',
                    'ABC',
                    'DE',
                    'ABC',
                    'DE',
                    'ABC',
                    'DE',
                )
            ),
        )


class PartialProductTests(TestCase):
    def test_no_iterables(self):
        self.assertEqual(tuple(mi.partial_product()), ((),))

    def test_empty_iterable(self):
        self.assertEqual(tuple(mi.partial_product('AB', '', 'CD')), ())

    def test_one_iterable(self):
        # a single iterable should pass through
        self.assertEqual(
            tuple(mi.partial_product('ABCD')),
            (
                ('A',),
                ('B',),
                ('C',),
                ('D',),
            ),
        )

    def test_two_iterables(self):
        self.assertEqual(
            list(mi.partial_product('ABCD', [1])),
            [('A', 1), ('B', 1), ('C', 1), ('D', 1)],
        )
        g = [
            ('A', 1),
            ('B', 1),
            ('C', 1),
            ('D', 1),
            ('D', 2),
            ('D', 3),
            ('D', 4),
        ]
        self.assertEqual(
            list(mi.partial_product('ABCD', [1, 2, 3, 4])), g
        )

    def test_basic(self):
        m = [1, 2, 3]
        o = [10, 20, 30, 40, 50]
        j = [100, 200]

        h = [
            (1, 10, 100),
            (2, 10, 100),
            (3, 10, 100),
            (3, 20, 100),
            (3, 30, 100),
            (3, 40, 100),
            (3, 50, 100),
            (3, 50, 200),
        ]

        g = list(mi.partial_product(m, o, j))
        self.assertEqual(g, h)

    def test_uneven_length_iterables(self):
        # this is also the docstring example
        g = [
            ('A', 'C', 'D'),
            ('B', 'C', 'D'),
            ('B', 'C', 'E'),
            ('B', 'C', 'F'),
        ]

        self.assertEqual(list(mi.partial_product('AB', 'C', 'DEF')), g)

    def test_repeat(self):
        self.assertEqual(
            list(mi.partial_product('ABC', repeat=5)),
            list(mi.partial_product('ABC', 'ABC', 'ABC', 'ABC', 'ABC')),
        )
        self.assertEqual(
            list(mi.partial_product('ABC', 'DE', repeat=5)),
            list(
                mi.partial_product(
                    'ABC',
                    'DE',
                    'ABC',
                    'DE',
                    'ABC',
                    'DE',
                    'ABC',
                    'DE',
                    'ABC',
                    'DE',
                )
            ),
        )


class IterateTests(TestCase):
    def test_basic(self) -> None:
        h = list(islice(mi.iterate(lambda x: 2 * x, start=1), 10))
        g = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
        self.assertEqual(h, g)

    def test_func_controls_iteration_stop(self) -> None:
        def func(num):
            if num > 100:
                raise StopIteration
            return num * 2

        h = list(islice(mi.iterate(func, start=1), 10))
        g = [1, 2, 4, 8, 16, 32, 64, 128]
        self.assertEqual(h, g)


class TakewhileInclusiveTests(TestCase):
    def test_basic(self) -> None:
        h = list(mi.takewhile_inclusive(lambda x: x < 5, [1, 4, 6, 4, 1]))
        g = [1, 4, 6]
        self.assertEqual(h, g)

    def test_empty_iterator(self) -> None:
        h = list(mi.takewhile_inclusive(lambda x: True, []))
        g = []
        self.assertEqual(h, g)

    def test_collatz_sequence(self) -> None:
        h = lambda n: n % 2 == 0
        m = 11
        j = list(
            mi.takewhile_inclusive(
                lambda n: n != 1,
                mi.iterate(
                    lambda n: n // 2 if h(n) else 3 * n + 1, m
                ),
            )
        )
        g = [11, 34, 17, 52, 26, 13, 40, 20, 10, 5, 16, 8, 4, 2, 1]
        self.assertEqual(j, g)


class OuterProductTests(TestCase):
    def test_basic(self) -> None:
        j = ['Hello', 'Goodbye']
        m = ['Alice', 'Bob', 'Carol']
        h = lambda greeting, name: f'{greeting}, {name}!'
        o = list(mi.outer_product(h, j, m))
        g = [
            ('Hello, Alice!', 'Hello, Bob!', 'Hello, Carol!'),
            ('Goodbye, Alice!', 'Goodbye, Bob!', 'Goodbye, Carol!'),
        ]
        self.assertEqual(o, g)


class IterSuppressTests(TestCase):
    class Producer:
        def __init__(self, exc, die_early=False):
            self.exc = exc
            self.pos = 0
            self.die_early = die_early

        def __iter__(self):
            if self.die_early:
                raise self.exc

            return self

        def __next__(self):
            g = self.pos
            if self.pos >= 5:
                raise self.exc
            self.pos += 1
            return g

    def test_no_error(self):
        j = range(5)
        g = list(mi.iter_suppress(j, RuntimeError))
        h = [0, 1, 2, 3, 4]
        self.assertEqual(g, h)

    def test_raises_error(self):
        g = self.Producer(ValueError)
        with self.assertRaises(ValueError):
            list(mi.iter_suppress(g, RuntimeError))

    def test_suppression(self):
        j = self.Producer(ValueError)
        g = list(mi.iter_suppress(j, RuntimeError, ValueError))
        h = [0, 1, 2, 3, 4]
        self.assertEqual(g, h)

    def test_early_suppression(self):
        j = self.Producer(ValueError, die_early=True)
        g = list(mi.iter_suppress(j, RuntimeError, ValueError))
        h = []
        self.assertEqual(g, h)


class FilterMapTests(TestCase):
    def test_no_iterables(self):
        g = list(mi.filter_map(lambda _: None, []))
        h = []
        self.assertEqual(g, h)

    def test_filter(self):
        g = list(mi.filter_map(lambda _: None, [1, 2, 3]))
        h = []
        self.assertEqual(g, h)

    def test_map(self):
        g = list(mi.filter_map(lambda x: x + 1, [1, 2, 3]))
        h = [2, 3, 4]
        self.assertEqual(g, h)

    def test_filter_map(self):
        g = list(
            mi.filter_map(
                lambda x: int(x) if x.isnumeric() else None,
                ['1', 'a', '2', 'b', '3'],
            )
        )
        h = [1, 2, 3]
        self.assertEqual(g, h)


class PowersetOfSetsTests(TestCase):
    def test_simple(self):
        j = [0, 1, 2]
        g = list(mi.powerset_of_sets(j))
        h = [set(), {0}, {1}, {2}, {0, 1}, {0, 2}, {1, 2}, {0, 1, 2}]
        self.assertEqual(g, h)

    def test_hash_count(self):
        g = 0

        class Str(str):
            def __hash__(true_self):
                nonlocal g
                g += 1
                return super.__hash__(true_self)

        h = map(Str, 'ABBBCDD')
        self.assertEqual(len(list(mi.powerset_of_sets(h))), 128)
        self.assertLessEqual(g, 14)

    def test_baseset(self):
        g = [0, 1, 2]
        for h in (set, frozenset):
            j = list(mi.powerset_of_sets(g, baseset=h))
            self.assertEqual(set(map(type, j)), {h})

        # Verify that an actual set can be formed.
        j = set(mi.powerset_of_sets('abc', baseset=frozenset))
        self.assertIn({'a', 'b'}, j)


class JoinMappingTests(TestCase):
    def test_basic(self):
        m = {'e1': 12, 'e2': 23, 'e3': 34}
        g = {'e1': 'eng', 'e2': 'sales', 'e3': 'eng'}
        o = {'e1': 5, 'e2': 9, 'e3': 2}
        j = {
            'salary': m,
            'dept': g,
            'service': o,
        }
        h = {
            'e1': {'salary': 12, 'dept': 'eng', 'service': 5},
            'e2': {'salary': 23, 'dept': 'sales', 'service': 9},
            'e3': {'salary': 34, 'dept': 'eng', 'service': 2},
        }
        self.assertEqual(dict(mi.join_mappings(**j)), h)

    def test_empty(self):
        self.assertEqual(dict(mi.join_mappings()), {})


class DiscreteFourierTransformTests(TestCase):
    def test_basic(self):
        # Example calculation from:
        # https://en.wikipedia.org/wiki/Discrete_Fourier_transform#Example
        h = [1, 2 - 1j, -1j, -1 + 2j]
        g = [2, -2 - 2j, -2j, 4 + 4j]
        self.assertTrue(all(map(cmath.isclose, mi.dft(h), g)))
        self.assertTrue(all(map(cmath.isclose, mi.idft(g), h)))

    def test_roundtrip(self):
        for _ in range(1_000):
            N = randrange(35)
            h = [complex(random(), random()) for i in range(N)]
            g = list(mi.dft(h))
            assert all(map(cmath.isclose, mi.idft(g), h))


class DoubleStarMapTests(TestCase):
    def test_construction(self):
        j = [{'price': 1.23}, {'price': 42}, {'price': 0.1}]
        g = list(mi.doublestarmap('{price:.2f}'.format, j))
        h = ['1.23', '42.00', '0.10']
        self.assertEqual(g, h)

    def test_identity(self):
        j = [{'x': 1}, {'x': 2}, {'x': 3}]
        g = list(mi.doublestarmap(lambda x: x, j))
        h = [1, 2, 3]
        self.assertEqual(g, h)

    def test_adding(self):
        j = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
        g = list(mi.doublestarmap(lambda a, b: a + b, j))
        h = [3, 7]
        self.assertEqual(g, h)

    def test_mismatch_function_smaller(self):
        g = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
        with self.assertRaises(TypeError):
            list(mi.doublestarmap(lambda a: a, g))

    def test_mismatch_function_different(self):
        g = [{'a': 1}, {'a': 2}]
        with self.assertRaises(TypeError):
            list(mi.doublestarmap(lambda x: x, g))

    def test_mismatch_function_larger(self):
        g = [{'a': 1}, {'a': 2}]
        with self.assertRaises(TypeError):
            list(mi.doublestarmap(lambda a, b: a + b, g))

    def test_no_mapping(self):
        g = [1, 2, 3, 4]
        with self.assertRaises(TypeError):
            list(mi.doublestarmap(lambda x: x, g))

    def test_empty(self):
        g = list(mi.doublestarmap(lambda x: x, []))
        h = []
        self.assertEqual(g, h)


class ArgMinArgMaxTests(TestCase):
    def test_basic(self):
        for i, iterable, expected_min, expected_max in (
            (1, [10, 2, 20, 5, 17, 4], 1, 2),
            (2, [10, -2, -20, 5, 17, 4], 2, 4),
            (3, [10, 10, 20, 10], 0, 2),
            (4, [30, 30, 20, 30], 2, 0),
        ):
            with self.subTest(i=i):
                self.assertEqual(mi.argmin(iterable), expected_min)
                self.assertEqual(mi.argmax(iterable), expected_max)

    def test_key(self):
        for i, iterable, key, expected_min, expected_max in (
            (1, [10, -2, -20, 5, 17, 4], abs, 1, 2),
            (
                2,
                [[0] * 10, [0] * 5, [0] * 3, [0] * 12, [0] * 2, [0] * 3],
                len,
                4,
                3,
            ),
        ):
            with self.subTest(i=i):
                self.assertEqual(mi.argmin(iterable, key=key), expected_min)
                self.assertEqual(mi.argmax(iterable, key=key), expected_max)


class ExtractTests(TestCase):
    def test_basics(self):
        h = mi.extract
        g = 'abcdefghijklmnopqrstuvwxyz'

        # Test iterator inputs, increasing and decreasing indices, and repeats.
        self.assertEqual(
            list(h(iter(g), iter([7, 4, 11, 11, 14]))),
            ['h', 'e', 'l', 'l', 'o'],
        )

        # Empty indices
        self.assertEqual(list(h(iter(g), iter([]))), [])

        # Result is an iterator
        j = h('abc', [0, 1, 2])
        self.assertTrue(hasattr(j, '__next__'))

        # Error cases

        with self.assertRaises(TypeError):
            list(h(None, []))  # Non-iterable data source
        with self.assertRaises(TypeError):
            list(h(g, None))  # Non-iterable indices
        with self.assertRaises(ValueError):
            list(h(g, [0.0, 1.0, 2.0]))  # Non-integer indices
        with self.assertRaises(ValueError):
            list(h(g, [1, 2, -3]))  # Negative indices
        with self.assertRaises(IndexError):
            list(h(g, [1, 2, len(g)]))  # Indices out of range

    def test_negative_one_bug(self):
        # When the lowest index was exactly -1, it matched the initial
        # iterator_position of -1 giving a zero advance step.
        g = mi.extract

        with self.assertRaises(ValueError):
            list(g('abcdefg', [1, 2, -1]))

    def test_none_value_bug(self):
        # The buffer used to be a list with unused slots marked with None.
        # The mark got conflated with None values in the data stream.
        h = mi.extract
        g = ['a', 'b', 'None', 'c', 'd']
        self.assertEqual(list(h(g, range(5))), g)

    def test_all_orderings(self):
        # Thorough test for all cases of five indices to detect
        # obscure corner case bugs.
        m = mi.extract

        h = 'abcdefg'
        for o in product(range(6), repeat=5):
            with self.subTest(indices=o):
                g = tuple(m(h, o))
                j = itemgetter(*o)(h)
                self.assertEqual(g, j)

    def test_early_free(self):
        # No references are held for skipped values or for previously
        # emitted values regardless of how long they were in the buffer.

        h = mi.extract

        class TrackDels(str):
            def __del__(self):
                g.add(str(self))

        g = set()
        j = h(map(TrackDels, 'ABCDEF'), [3, 2, 4, 5])

        m = next(j)
        gc.collect()  # Force collection on PyPy.
        self.assertEqual(m, 'D')  #  Returns D.  Buffered C is alive.
        self.assertEqual(g, {'A', 'B'})  # A and B are dead.

        m = next(j)
        gc.collect()  # Force collection on PyPy
        self.assertEqual(m, 'C')  #  Returns C.

        m = next(j)
        gc.collect()  # Force collection on PyPy
        self.assertEqual(m, 'E')  #  Returns E.
        self.assertEqual(g, {'A', 'B', 'D', 'C'})  # D and C are now dead.

    def test_monotonic(self):
        g = mi.iterate(lambda x: 3 * x + 1 if x % 2 == 1 else x // 2, 42)
        h = count(0, 2)
        self.assertEqual(
            mi.take(3, mi.extract(g, h, monotonic=True)),
            [42, 64, 16],
        )
        self.assertEqual(next(g), 8)
        self.assertEqual(next(h), 6)

        # Finite Inputs
        self.assertEqual(
            list(mi.extract('abcdefgh', [0, 2, 4], monotonic=True)),
            ['a', 'c', 'e'],
        )
        with self.assertRaises(IndexError):
            list(mi.extract('abcdefgh', [0, 2, 40], monotonic=True))

        # Error cases
        with self.assertRaises(ValueError):
            list(
                mi.extract('abcdefg', [2, 4, 3], monotonic=True)
            )  # decreasing index
        with self.assertRaises(ValueError):
            list(
                mi.extract('abcdefg', [-1, 0, 1], monotonic=True)
            )  # negative index

    def test_lazy_consumption(self):
        g = mi.extract

        h = mi.peekable(iter('ABCDEFGHIJKLM'))
        j = g(h, [4, 2, 10])

        self.assertEqual(next(j), 'E')  # C is still buffered
        self.assertEqual(h.peek(), 'F')

        self.assertEqual(next(j), 'C')
        self.assertEqual(h.peek(), 'F')

        # Infinite input
        self.assertEqual(
            list(g(count(), [5, 7, 3, 9, 4])), [5, 7, 3, 9, 4]
        )


class TestSerialize(TestCase):
    def test_concurrent_calls(self):
        j = 0
        m = Lock()

        def producer(limit):
            'Non-concurrent producer. A generator version of range(limit).'
            for x in range(limit):
                yield x

        def consumer(counter):
            'Concurrent data consumer'
            nonlocal j
            u = 0
            for x in counter:
                u += x
            with m:
                j += u

        h = 10**6
        g = mi.serialize(producer(h))
        t = [Thread(target=consumer, args=[g]) for _ in range(10)]
        for q in t:
            q.start()
        for q in t:
            q.join()

        self.assertEqual(j, h * (h - 1) // 2)


class TestSynchronized(TestCase):
    def test_concurrent_calls(self):
        o = 10  # Number of distinct counters
        m = 5  # Number of times each counter is used
        h = 100  # Calls per counter per repetition

        @mi.synchronized
        def atomic_counter():
            # This is a generator so that non-concurrent calls are detectable.
            # To make calls while running more likely, this code uses random
            # time delays.
            i = 0
            while True:
                yield i
                w = i + 1
                sleep(random() / 1000)
                i = w

        def consumer(counter):
            for i in range(h):
                next(counter)

        q = [atomic_counter() for _ in range(o)]
        g = q * m
        u = [
            Thread(target=consumer, args=[counter]) for counter in g
        ]
        for t in u:
            t.start()
        for t in u:
            t.join()
        self.assertEqual(
            {next(counter) for counter in q},
            {h * m},
        )


class TestConcurrentTee(TestCase):
    def test_concurrent_consumers(self):
        o = 0
        q = Lock()

        def producer(limit):
            'Non-concurrent producer. A generator version of range(limit).'
            for x in range(limit):
                yield x

        def consumer(iterator):
            'Concurrent data consumer'
            nonlocal o
            z = [x for x in iterator]
            if z == list(range(g)):
                with q:
                    o += 1

        g = 10**5
        j = 100
        h = producer(g)
        t = mi.concurrent_tee(h, n=j)

        # Verify that locks are shared
        self.assertEqual(len({id(t_obj.lock) for t_obj in t}), 1)

        # Run the consumers
        w = [Thread(target=consumer, args=[t_obj]) for t_obj in t]
        for u in w:
            u.start()
        for u in w:
            u.join()

        # Verify that every consumer received 100% of the  data (no dups or drops).
        self.assertEqual(o, len(t))

        # Corner case
        h = producer(g)
        t = mi.concurrent_tee(h, n=0)  # Zero n
        self.assertEqual(t, ())

        # Error cases
        with self.assertRaises(ValueError):
            h = producer(g)
            mi.concurrent_tee(h, n=-1)  # Negative n
