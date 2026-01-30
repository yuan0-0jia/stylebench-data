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


def loadTests(loader, tests, ignore):
    # Add the doctests
    tests.addTests(DocTestSuite('more_itertools.more'))
    return tests


class ChunkedTests(TestCase):
    """Tests for ``chunked()``"""

    def testEven(self):
        """Test when ``n`` divides evenly into the length of the iterable."""
        self.assertEqual(
            list(mi.chunked('ABCDEF', 3)), [['A', 'B', 'C'], ['D', 'E', 'F']]
        )

    def testOdd(self):
        """Test when ``n`` does not divide evenly into the length of the
        iterable.

        """
        self.assertEqual(
            list(mi.chunked('ABCDE', 3)), [['A', 'B', 'C'], ['D', 'E']]
        )

    def testNone(self):
        """Test when ``n`` has the value ``None``."""
        self.assertEqual(
            list(mi.chunked('ABCDE', None)), [['A', 'B', 'C', 'D', 'E']]
        )

    def testStrictFalse(self):
        """Test when ``n`` does not divide evenly into the length of the
        iterable and strict is false.

        """
        self.assertEqual(
            list(mi.chunked('ABCDE', 3, strict=False)),
            [['A', 'B', 'C'], ['D', 'E']],
        )

    def testStrictBeingTrue(self):
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

    def testStrictBeingTrueWithSizeNone(self):
        """Test when ``n`` has value ``None`` and the keyword strict is True
        (raising an exception).

        """

        def f():
            return list(mi.chunked('ABCDE', None, strict=True))

        self.assertRaisesRegex(
            ValueError, "n must not be None when using strict mode.", f
        )


class FirstTests(TestCase):
    def testMany(self):
        # Also try it on a generator expression to make sure it works on
        # whatever those return, across Python versions.
        self.assertEqual(mi.first(x for x in range(4)), 0)

    def testOne(self):
        self.assertEqual(mi.first([3]), 3)

    def testEmpty(self):
        with self.assertRaises(ValueError):
            mi.first([])

    def testDefault(self):
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
    def testBasic(self):
        cases = [
            (range(4), 3),
            (iter(range(4)), 3),
            (range(1), 0),
            (iter(range(1)), 0),
            (IterOnlyRange(5), 4),
            ({n: str(n) for n in range(5)}, 4),
            ({0: '0', -1: '-1', 2: '-2'}, 2),
        ]

        for iterable, expected in cases:
            with self.subTest(iterable=iterable):
                self.assertEqual(mi.last(iterable), expected)

    def testDefault(self):
        for iterable, default, expected in [
            (range(1), None, 0),
            ([], None, None),
            ({}, None, None),
            (iter([]), None, None),
        ]:
            with self.subTest(args=(iterable, default)):
                self.assertEqual(mi.last(iterable, default=default), expected)

    def testEmpty(self):
        for iterable in ([], iter(range(0))):
            with self.subTest(iterable=iterable):
                with self.assertRaises(ValueError):
                    mi.last(iterable)

    def testReversedIsNone(self):
        # See https://github.com/more-itertools/more-itertools/issues/1001
        class ReversedIsNone:
            __reversed__ = None

            def __iter__(self):
                return iter([1])

        self.assertEqual(mi.last(ReversedIsNone()), 1)


class NthOrLastTests(TestCase):
    """Tests for ``nth_or_last()``"""

    def testBasic(self):
        self.assertEqual(mi.nthOrLast(range(3), 1), 1)
        self.assertEqual(mi.nthOrLast(range(3), 3), 2)

    def testDefaultValue(self):
        default = 42
        self.assertEqual(mi.nthOrLast(range(0), 3, default), default)

    def testEmptyIterableNoDefault(self):
        self.assertRaises(ValueError, lambda: mi.nthOrLast(range(0), 0))


class PeekableMixinTests:
    """Common tests for ``peekable()`` and ``seekable()`` behavior"""

    cls = None

    def testPassthrough(self):
        """Iterating a peekable without using ``peek()`` or ``prepend()``
        should just give the underlying iterable's elements (a trivial test but
        useful to set a baseline in case something goes wrong)"""
        expected = [1, 2, 3, 4, 5]
        actual = list(self.cls(expected))
        self.assertEqual(actual, expected)

    def testPeekDefault(self):
        """Make sure passing a default into ``peek()`` works."""
        p = self.cls([])
        self.assertEqual(p.peek(7), 7)

    def testTruthiness(self):
        """Make sure a ``peekable`` tests true iff there are items remaining in
        the iterable.

        """
        p = self.cls([])
        self.assertFalse(p)

        p = self.cls(range(3))
        self.assertTrue(p)

    def testSimplePeeking(self):
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

    def testIndexing(self):
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

    def testSlicing(self):
        """Slicing the peekable shouldn't advance the iterator."""
        seq = list('abcdefghijkl')
        p = mi.peekable(seq)

        # Slicing the peekable should just be like slicing a re-iterable
        self.assertEqual(p[1:4], seq[1:4])

        # Advancing the iterator moves the slices up also
        self.assertEqual(next(p), 'a')
        self.assertEqual(p[1:4], seq[1:][1:4])

        # Implicit starts and stop should work
        self.assertEqual(p[:5], seq[1:][:5])
        self.assertEqual(p[:], seq[1:][:])

        # Indexing past the end should work
        self.assertEqual(p[:100], seq[1:][:100])

        # Steps should work, including negative
        self.assertEqual(p[::2], seq[1:][::2])
        self.assertEqual(p[::-1], seq[1:][::-1])

    def testSlicingReset(self):
        """Test slicing on a fresh iterable each time"""
        iterable = ['0', '1', '2', '3', '4', '5']
        indexes = list(range(-4, len(iterable) + 4)) + [None]
        steps = [1, 2, 3, 4, -1, -2, -3, 4]
        for sliceArgs in product(indexes, indexes, steps):
            it = iter(iterable)
            p = mi.peekable(it)
            next(p)
            index = slice(*sliceArgs)
            actual = p[index]
            expected = iterable[1:][index]
            self.assertEqual(actual, expected, sliceArgs)

    def testSlicingError(self):
        iterable = '01234567'
        p = mi.peekable(iter(iterable))

        # Prime the cache
        p.peek()
        oldCache = list(p._cache)

        # Illegal slice
        with self.assertRaises(ValueError):
            p[1:-1:0]

        # Neither the cache nor the iteration should be affected
        self.assertEqual(oldCache, list(p._cache))
        self.assertEqual(list(p), list(iterable))

    # prepend() behavior tests

    def testPrepend(self):
        """Tests interspersed ``prepend()`` and ``next()`` calls"""
        it = mi.peekable(range(2))
        actual = []

        # Test prepend() before next()
        it.prepend(10)
        actual += [next(it), next(it)]

        # Test prepend() between next()s
        it.prepend(11)
        actual += [next(it), next(it)]

        # Test prepend() after source iterable is consumed
        it.prepend(12)
        actual += [next(it)]

        expected = [10, 0, 11, 1, 12]
        self.assertEqual(actual, expected)

    def testMultiPrepend(self):
        """Tests prepending multiple items and getting them in proper order"""
        it = mi.peekable(range(5))
        actual = [next(it), next(it)]
        it.prepend(10, 11, 12)
        it.prepend(20, 21)
        actual += list(it)
        expected = [0, 1, 20, 21, 10, 11, 12, 2, 3, 4]
        self.assertEqual(actual, expected)

    def testEmpty(self):
        """Tests prepending in front of an empty iterable"""
        it = mi.peekable([])
        it.prepend(10)
        actual = list(it)
        expected = [10]
        self.assertEqual(actual, expected)

    def testPrependTruthiness(self):
        """Tests that ``__bool__()`` or ``__nonzero__()`` works properly
        with ``prepend()``"""
        it = mi.peekable(range(5))
        self.assertTrue(it)
        actual = list(it)
        self.assertFalse(it)
        it.prepend(10)
        self.assertTrue(it)
        actual += [next(it)]
        self.assertFalse(it)
        expected = [0, 1, 2, 3, 4, 10]
        self.assertEqual(actual, expected)

    def testMultiPrependPeek(self):
        """Tests prepending multiple elements and getting them in reverse order
        while peeking"""
        it = mi.peekable(range(5))
        actual = [next(it), next(it)]
        self.assertEqual(it.peek(), 2)
        it.prepend(10, 11, 12)
        self.assertEqual(it.peek(), 10)
        it.prepend(20, 21)
        self.assertEqual(it.peek(), 20)
        actual += list(it)
        self.assertFalse(it)
        expected = [0, 1, 20, 21, 10, 11, 12, 2, 3, 4]
        self.assertEqual(actual, expected)

    def testPrependAfterStop(self):
        """Test resuming iteration after a previous exhaustion"""
        it = mi.peekable(range(3))
        self.assertEqual(list(it), [0, 1, 2])
        self.assertRaises(StopIteration, lambda: next(it))
        it.prepend(10)
        self.assertEqual(next(it), 10)
        self.assertRaises(StopIteration, lambda: next(it))

    def testPrependSlicing(self):
        """Tests interaction between prepending and slicing"""
        seq = list(range(20))
        p = mi.peekable(seq)

        p.prepend(30, 40, 50)
        pseq = [30, 40, 50] + seq  # pseq for prepended_seq

        # adapt the specific tests from test_slicing
        self.assertEqual(p[0], 30)
        self.assertEqual(p[1:8], pseq[1:8])
        self.assertEqual(p[1:], pseq[1:])
        self.assertEqual(p[:5], pseq[:5])
        self.assertEqual(p[:], pseq[:])
        self.assertEqual(p[:100], pseq[:100])
        self.assertEqual(p[::2], pseq[::2])
        self.assertEqual(p[::-1], pseq[::-1])

    def testPrependIndexing(self):
        """Tests interaction between prepending and indexing"""
        seq = list(range(20))
        p = mi.peekable(seq)

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

    def testPrependIterable(self):
        """Tests prepending from an iterable"""
        it = mi.peekable(range(5))
        # Don't directly use the range() object to avoid any range-specific
        # optimizations
        it.prepend(*(x for x in range(5)))
        actual = list(it)
        expected = list(chain(range(5), range(5)))
        self.assertEqual(actual, expected)

    def testPrependMany(self):
        """Tests that prepending a huge number of elements works"""
        it = mi.peekable(range(5))
        # Don't directly use the range() object to avoid any range-specific
        # optimizations
        it.prepend(*(x for x in range(20000)))
        actual = list(it)
        expected = list(chain(range(20000), range(5)))
        self.assertEqual(actual, expected)

    def testPrependReversed(self):
        """Tests prepending from a reversed iterable"""
        it = mi.peekable(range(3))
        it.prepend(*reversed((10, 11, 12)))
        actual = list(it)
        expected = [12, 11, 10, 0, 1, 2]
        self.assertEqual(actual, expected)


class ConsumerTests(TestCase):
    """Tests for ``consumer()``"""

    def testConsumer(self):
        @mi.consumer
        def eater():
            while True:
                x = yield  # noqa

        e = eater()
        e.send('hi')  # without @consumer, would raise TypeError


class DistinctPermutationsTests(TestCase):
    def testBasic(self):
        iterable = ['z', 'a', 'a', 'q', 'q', 'q', 'y']
        actual = list(mi.distinctPermutations(iterable))
        expected = set(permutations(iterable))
        self.assertCountEqual(actual, expected)

    def testR(self):
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
                expected = set(permutations(iterable, r))
                actual = list(mi.distinctPermutations(iter(iterable), r))
                self.assertCountEqual(actual, expected)

    def testUnsortable(self):
        iterable = ['1', 2, 2, 3, 3, 3]
        actual = list(mi.distinctPermutations(iterable))
        expected = set(permutations(iterable))
        self.assertCountEqual(actual, expected)

    def testUnsortableR(self):
        iterable = ['1', 2, 2, 3, 3, 3]
        for r in range(len(iterable) + 1):
            with self.subTest(iterable=iterable, r=r):
                actual = list(mi.distinctPermutations(iterable, r=r))
                expected = set(permutations(iterable, r=r))
                self.assertCountEqual(actual, expected)

    def testUnsortedEquivalent(self):
        iterable = [1, True, '3']
        actual = list(mi.distinctPermutations(iterable))
        expected = set(permutations(iterable))
        self.assertCountEqual(actual, expected)

    def testUnhashable(self):
        iterable = ([1], [1], 2)
        actual = list(mi.distinctPermutations(iterable))
        expected = list(mi.uniqueEverseen(permutations(iterable)))
        self.assertCountEqual(actual, expected)


class DerangementsTests(TestCase):
    def testUniqueValues(self):
        n = 8
        expected = set(
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
            actual = set(mi.derangements(iterable))
            self.assertEqual(actual, expected)

    def testRepeatedValues(self):
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

    def testUnsortableUnhashable(self):
        iterable = (0, True, ['Carol'])
        actual = list(mi.derangements(iterable))
        expected = [(True, ['Carol'], 0), (['Carol'], 0, True)]
        self.assertListEqual(actual, expected)

    def testR(self):
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
                actual = [''.join(x) for x in mi.derangements(s, r=r)]
                self.assertEqual(actual, expected)


class IlenTests(TestCase):
    def testIlen(self):
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
    def testBasic(self):
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

    def testUnpacked(self):
        self.assertTupleEqual(mi.minmax(2, 3, 1), (1, 3))
        self.assertTupleEqual(mi.minmax(12, 3, 4, key=str), (12, 4))

    def testIterables(self):
        self.assertTupleEqual(mi.minmax(x for x in [0, 1, 2, 3]), (0, 3))
        self.assertTupleEqual(
            mi.minmax(map(str, [3, 5.5, 'a', 2])), ('2', 'a')
        )
        self.assertTupleEqual(
            mi.minmax(filter(None, [0, 3, '', None, 10])), (3, 10)
        )

    def testKey(self):
        self.assertTupleEqual(
            mi.minmax({(), (1, 4, 2), 'abcde', range(4)}, key=len),
            ((), 'abcde'),
        )
        self.assertTupleEqual(
            mi.minmax((x for x in [10, 3, 25]), key=str), (10, 3)
        )

    def testDefault(self):
        with self.assertRaises(ValueError):
            mi.minmax([])

        self.assertIs(mi.minmax([], default=None), None)
        self.assertListEqual(mi.minmax([], default=[1, 'a']), [1, 'a'])


class WithIterTests(TestCase):
    def testWithIter(self):
        s = StringIO('One fish\nTwo fish')
        initialWords = [line.split()[0] for line in mi.withIter(s)]

        # Iterable's items should be faithfully represented
        self.assertEqual(initialWords, ['One', 'Two'])
        # The file object should be closed
        self.assertTrue(s.closed)


class OneTests(TestCase):
    def testBasic(self):
        it = iter(['item'])
        self.assertEqual(mi.one(it), 'item')

    def testTooShortNew(self):
        it = iter([])
        self.assertRaises(ValueError, lambda: mi.one(it))
        self.assertRaises(
            OverflowError, lambda: mi.one(it, tooShort=OverflowError)
        )

    def testTooLong(self):
        it = count()
        self.assertRaises(ValueError, lambda: mi.one(it))  # burn 0 and 1
        self.assertEqual(next(it), 2)
        self.assertRaises(
            OverflowError, lambda: mi.one(it, tooLong=OverflowError)
        )

    def testTooLongDefaultMessage(self):
        it = count()
        self.assertRaisesRegex(
            ValueError,
            "Expected exactly one item in "
            "iterable, but got 0, 1, and "
            "perhaps more.",
            lambda: mi.one(it),
        )


class IntersperseTest(TestCase):
    """Tests for intersperse()"""

    def testEven(self):
        iterable = (x for x in '01')
        self.assertEqual(
            list(mi.intersperse(None, iterable)), ['0', None, '1']
        )

    def testOdd(self):
        iterable = (x for x in '012')
        self.assertEqual(
            list(mi.intersperse(None, iterable)), ['0', None, '1', None, '2']
        )

    def testNested(self):
        element = ('a', 'b')
        iterable = (x for x in '012')
        actual = list(mi.intersperse(element, iterable))
        expected = ['0', ('a', 'b'), '1', ('a', 'b'), '2']
        self.assertEqual(actual, expected)

    def testNotIterable(self):
        self.assertRaises(TypeError, lambda: mi.intersperse('x', 1))

    def testN(self):
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
            iterable = (x for x in '012345')
            actual = list(mi.intersperse(element, iterable, n=n))
            self.assertEqual(actual, expected)

    def testNZero(self):
        self.assertRaises(
            ValueError, lambda: list(mi.intersperse('x', '012', n=0))
        )


class UniqueToEachTests(TestCase):
    """Tests for ``unique_to_each()``"""

    def testAllUnique(self):
        """When all the input iterables are unique the output should match
        the input."""
        iterables = [[1, 2], [3, 4, 5], [6, 7, 8]]
        self.assertEqual(mi.uniqueToEach(*iterables), iterables)

    def testDuplicates(self):
        """When there are duplicates in any of the input iterables that aren't
        in the rest, those duplicates should be emitted."""
        iterables = ["mississippi", "missouri"]
        self.assertEqual(
            mi.uniqueToEach(*iterables), [['p', 'p'], ['o', 'u', 'r']]
        )

    def testMixed(self):
        """When the input iterables contain different types the function should
        still behave properly"""
        iterables = ['x', (i for i in range(3)), [1, 2, 3], tuple()]
        self.assertEqual(mi.uniqueToEach(*iterables), [['x'], [0], [3], []])


class WindowedTests(TestCase):
    def testBasic(self):
        iterable = [1, 2, 3, 4, 5]

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
                actual = list(mi.windowed(iterable, n))
                self.assertEqual(actual, expected)

    def testFillvalue(self):
        actual = list(mi.windowed([1, 2, 3, 4, 5], 6, fillvalue='!'))
        expected = [(1, 2, 3, 4, 5, '!')]
        self.assertEqual(actual, expected)

    def testStep(self):
        iterable = [1, 2, 3, 4, 5, 6, 7]
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
                actual = list(mi.windowed(iterable, n, step=step))
                self.assertEqual(actual, expected)

    def testInvalidStep(self):
        # Step must be greater than or equal to 1
        with self.assertRaises(ValueError):
            list(mi.windowed([1, 2, 3, 4, 5], 3, step=0))

    def testFillvalueStep(self):
        actual = list(mi.windowed([1, 2, 3, 4, 5], 3, fillvalue='!', step=3))
        expected = [(1, 2, 3), (4, 5, '!')]
        self.assertEqual(actual, expected)

    def testNegative(self):
        with self.assertRaises(ValueError):
            list(mi.windowed([1, 2, 3, 4, 5], -1))

    def testEmptySeq(self):
        actual = list(mi.windowed([], 3))
        expected = []
        self.assertEqual(actual, expected)


class SubstringsTests(TestCase):
    def testBasic(self):
        iterable = (x for x in range(4))
        actual = list(mi.substrings(iterable))
        expected = [
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
        self.assertEqual(actual, expected)

    def testStrings(self):
        iterable = 'abc'
        actual = list(mi.substrings(iterable))
        expected = [
            ('a',),
            ('b',),
            ('c',),
            ('a', 'b'),
            ('b', 'c'),
            ('a', 'b', 'c'),
        ]
        self.assertEqual(actual, expected)

    def testEmpty(self):
        iterable = iter([])
        actual = list(mi.substrings(iterable))
        expected = []
        self.assertEqual(actual, expected)

    def testOrder(self):
        iterable = [2, 0, 1]
        actual = list(mi.substrings(iterable))
        expected = [(2,), (0,), (1,), (2, 0), (0, 1), (2, 0, 1)]
        self.assertEqual(actual, expected)


class SubstringsIndexesTests(TestCase):
    def testBasic(self):
        sequence = [x for x in range(4)]
        actual = list(mi.substringsIndexes(sequence))
        expected = [
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
        self.assertEqual(actual, expected)

    def testStrings(self):
        sequence = 'abc'
        actual = list(mi.substringsIndexes(sequence))
        expected = [
            ('a', 0, 1),
            ('b', 1, 2),
            ('c', 2, 3),
            ('ab', 0, 2),
            ('bc', 1, 3),
            ('abc', 0, 3),
        ]
        self.assertEqual(actual, expected)

    def testEmpty(self):
        sequence = []
        actual = list(mi.substringsIndexes(sequence))
        expected = []
        self.assertEqual(actual, expected)

    def testOrder(self):
        sequence = [2, 0, 1]
        actual = list(mi.substringsIndexes(sequence))
        expected = [
            ([2], 0, 1),
            ([0], 1, 2),
            ([1], 2, 3),
            ([2, 0], 0, 2),
            ([0, 1], 1, 3),
            ([2, 0, 1], 0, 3),
        ]
        self.assertEqual(actual, expected)

    def testReverse(self):
        sequence = [2, 0, 1]
        actual = list(mi.substringsIndexes(sequence, reverse=True))
        expected = [
            ([2, 0, 1], 0, 3),
            ([2, 0], 0, 2),
            ([0, 1], 1, 3),
            ([2], 0, 1),
            ([0], 1, 2),
            ([1], 2, 3),
        ]
        self.assertEqual(actual, expected)


class BucketTests(TestCase):
    def testBasic(self):
        iterable = [10, 20, 30, 11, 21, 31, 12, 22, 23, 33]
        D = mi.bucket(iterable, key=lambda x: 10 * (x // 10))

        # In-order access
        self.assertEqual(list(D[10]), [10, 11, 12])

        # Out of order access
        self.assertEqual(list(D[30]), [30, 31, 33])
        self.assertEqual(list(D[20]), [20, 21, 22, 23])

        self.assertEqual(list(D[40]), [])  # Nothing in here!

    def testIn(self):
        iterable = [10, 20, 30, 11, 21, 31, 12, 22, 23, 33]
        D = mi.bucket(iterable, key=lambda x: 10 * (x // 10))

        self.assertIn(10, D)
        self.assertNotIn(40, D)
        self.assertIn(20, D)
        self.assertNotIn(21, D)

        # Checking in-ness shouldn't advance the iterator
        self.assertEqual(next(D[10]), 10)

    def testValidator(self):
        iterable = count(0)
        key = lambda x: int(str(x)[0])  # First digit of each number
        validator = lambda x: 0 < x < 10  # No leading zeros
        D = mi.bucket(iterable, key, validator=validator)
        self.assertEqual(mi.take(3, D[1]), [1, 10, 11])
        self.assertNotIn(0, D)  # Non-valid entries don't return True
        self.assertNotIn(0, D._cache)  # Don't store non-valid entries
        self.assertEqual(list(D[0]), [])

    def testList(self):
        iterable = [10, 20, 30, 11, 21, 31, 12, 22, 23, 33]
        D = mi.bucket(iterable, key=lambda x: 10 * (x // 10))
        self.assertEqual(list(D[10]), [10, 11, 12])
        self.assertEqual(list(D[20]), [20, 21, 22, 23])
        self.assertEqual(list(D[30]), [30, 31, 33])
        self.assertEqual(set(D), {10, 20, 30})

    def testListValidator(self):
        iterable = [10, 20, 30, 11, 21, 31, 12, 22, 23, 33]
        key = lambda x: 10 * (x // 10)
        validator = lambda x: x != 20
        D = mi.bucket(iterable, key, validator=validator)
        self.assertEqual(set(D), {10, 30})
        self.assertEqual(list(D[10]), [10, 11, 12])
        self.assertEqual(list(D[20]), [])
        self.assertEqual(list(D[30]), [30, 31, 33])


class SpyTests(TestCase):
    """Tests for ``spy()``"""

    def testBasic(self):
        originalIterable = iter('abcdefg')
        head, newIterable = mi.spy(originalIterable)
        self.assertEqual(head, ['a'])
        self.assertEqual(
            list(newIterable), ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        )

    def testUnpacking(self):
        originalIterable = iter('abcdefg')
        (first, second, third), newIterable = mi.spy(originalIterable, 3)
        self.assertEqual(first, 'a')
        self.assertEqual(second, 'b')
        self.assertEqual(third, 'c')
        self.assertEqual(
            list(newIterable), ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        )

    def testTooMany(self):
        originalIterable = iter('abc')
        head, newIterable = mi.spy(originalIterable, 4)
        self.assertEqual(head, ['a', 'b', 'c'])
        self.assertEqual(list(newIterable), ['a', 'b', 'c'])

    def testZero(self):
        originalIterable = iter('abc')
        head, newIterable = mi.spy(originalIterable, 0)
        self.assertEqual(head, [])
        self.assertEqual(list(newIterable), ['a', 'b', 'c'])

    def testImmutable(self):
        originalIterable = iter('abcdefg')
        head, newIterable = mi.spy(originalIterable, 3)
        head[0] = 'A'
        self.assertEqual(head, ['A', 'b', 'c'])
        self.assertEqual(
            list(newIterable), ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        )


class InterleaveTests(TestCase):
    def testEven(self):
        actual = list(mi.interleave([1, 4, 7], [2, 5, 8], [3, 6, 9]))
        expected = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(actual, expected)

    def testShort(self):
        actual = list(mi.interleave([1, 4], [2, 5, 7], [3, 6, 8]))
        expected = [1, 2, 3, 4, 5, 6]
        self.assertEqual(actual, expected)

    def testMixedTypes(self):
        itList = ['a', 'b', 'c', 'd']
        itStr = '12345'
        itInf = count()
        actual = list(mi.interleave(itList, itStr, itInf))
        expected = ['a', '1', 0, 'b', '2', 1, 'c', '3', 2, 'd', '4', 3]
        self.assertEqual(actual, expected)


class InterleaveLongestTests(TestCase):
    def testEven(self):
        actual = list(mi.interleaveLongest([1, 4, 7], [2, 5, 8], [3, 6, 9]))
        expected = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(actual, expected)

    def testShort(self):
        actual = list(mi.interleaveLongest([1, 4], [2, 5, 7], [3, 6, 8]))
        expected = [1, 2, 3, 4, 5, 6, 7, 8]
        self.assertEqual(actual, expected)

    def testMixedTypes(self):
        itList = ['a', 'b', 'c', 'd']
        itStr = '12345'
        itGen = (x for x in range(3))
        actual = list(mi.interleaveLongest(itList, itStr, itGen))
        expected = ['a', '1', 0, 'b', '2', 1, 'c', '3', 2, 'd', '4', '5']
        self.assertEqual(actual, expected)


class InterleaveEvenlyTests(TestCase):
    def testEqualLengths(self):
        # when lengths are equal, the relative order shouldn't change
        a = [1, 2, 3]
        b = [5, 6, 7]
        actual = list(mi.interleaveEvenly([a, b]))
        expected = [1, 5, 2, 6, 3, 7]
        self.assertEqual(actual, expected)

    def testProportional(self):
        # easy case where the iterables have proportional length
        a = [1, 2, 3, 4]
        b = [5, 6]
        actual = list(mi.interleaveEvenly([a, b]))
        expected = [1, 2, 5, 3, 4, 6]
        self.assertEqual(actual, expected)

        # swapping a and b should yield the same result
        actualSwapped = list(mi.interleaveEvenly([b, a]))
        self.assertEqual(actualSwapped, expected)

    def testNotProportional(self):
        a = [1, 2, 3, 4, 5, 6, 7]
        b = [8, 9, 10]
        expected = [1, 2, 8, 3, 4, 9, 5, 6, 10, 7]
        actual = list(mi.interleaveEvenly([a, b]))
        self.assertEqual(actual, expected)

    def testDegenerateOne(self):
        a = [0, 1, 2, 3, 4]
        b = [5]
        expected = [0, 1, 2, 5, 3, 4]
        actual = list(mi.interleaveEvenly([a, b]))
        self.assertEqual(actual, expected)

    def testDegenerateEmpty(self):
        a = [1, 2, 3]
        b = []
        expected = [1, 2, 3]
        actual = list(mi.interleaveEvenly([a, b]))
        self.assertEqual(actual, expected)

    def testThreeIters(self):
        a = ["a1", "a2", "a3", "a4", "a5"]
        b = ["b1", "b2", "b3"]
        c = ["c1"]
        actual = list(mi.interleaveEvenly([a, b, c]))
        expected = ["a1", "b1", "a2", "c1", "a3", "b2", "a4", "b3", "a5"]
        self.assertEqual(actual, expected)

    def testManyIters(self):
        # smoke test with many iterables: create iterables with a random
        # number of elements starting with a character ("a0", "a1", ...)
        rng = Random(0)
        iterables = []
        for ch in ascii_letters:
            length = rng.randint(0, 100)
            iterable = [f"{ch}{i}" for i in range(length)]
            iterables.append(iterable)

        interleaved = list(mi.interleaveEvenly(iterables))

        # for each iterable, check that the result contains all its items
        for iterable, chExpect in zip(iterables, ascii_letters):
            interleavedActual = [
                e for e in interleaved if e.startswith(chExpect)
            ]
            assert len(set(interleavedActual)) == len(iterable)

    def testManualLengths(self):
        a = combinations(range(4), 2)
        lenA = 4 * (4 - 1) // 2  # == 6
        b = combinations(range(4), 3)
        lenB = 4

        expected = [
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
        actual = list(mi.interleaveEvenly([a, b], lengths=[lenA, lenB]))
        self.assertEqual(expected, actual)

    def testNoLengthRaises(self):
        # combinations doesn't have __len__, should trigger ValueError
        iterables = [range(5), combinations(range(5), 2)]
        with self.assertRaises(ValueError):
            list(mi.interleaveEvenly(iterables))

    def testArgumentMismatchRaises(self):
        # pass mismatching number of iterables and lengths
        iterables = [range(3)]
        lengths = [3, 4]
        with self.assertRaises(ValueError):
            list(mi.interleaveEvenly(iterables, lengths=lengths))


class InterleaveRandomlyTests(TestCase):
    def testBasic(self):
        seed(0)  # For reproducibility
        iterables = [1, 2, 3], 'abc', (True, False, None)
        self.assertEqual(
            list(mi.interleaveRandomly(*iterables)),
            ['a', 'b', 1, 'c', True, False, None, 2, 3],
        )

    def testSomeEmpty(self):
        self.assertEqual(
            list(mi.interleaveRandomly([1, 2, 3], [], [])),
            [1, 2, 3],
        )
        self.assertEqual(
            list(mi.interleaveRandomly([], [1, 2, 3], [])),
            [1, 2, 3],
        )
        self.assertEqual(
            list(mi.interleaveRandomly([], [], [1, 2, 3])),
            [1, 2, 3],
        )

    def testAllEmpty(self):
        iterables = [], [], []
        self.assertEqual(list(mi.interleaveRandomly(*iterables)), [])

    def testNoArgs(self):
        self.assertEqual(list(mi.interleaveRandomly()), [])

    def testBadType(self):
        # Should raise TypeError if not all arguments are iterable
        with self.assertRaises(TypeError):
            list(mi.interleaveRandomly(1, [2, 3], 'abc'))


class TestCollapse(TestCase):
    """Tests for ``collapse()``"""

    def testCollapse(self):
        l = [[1], 2, [[3], 4], [[[5]]]]
        self.assertEqual(list(mi.collapse(l)), [1, 2, 3, 4, 5])

    def testCollapseToString(self):
        l = [["s1"], "s2", [["s3"], "s4"], [[["s5"]]]]
        self.assertEqual(list(mi.collapse(l)), ["s1", "s2", "s3", "s4", "s5"])

    def testCollapseToBytes(self):
        l = [[b"s1"], b"s2", [[b"s3"], b"s4"], [[[b"s5"]]]]
        self.assertEqual(
            list(mi.collapse(l)), [b"s1", b"s2", b"s3", b"s4", b"s5"]
        )

    def testCollapseFlatten(self):
        l = [[1], [2], [[3], 4], [[[5]]]]
        self.assertEqual(list(mi.collapse(l, levels=1)), list(mi.flatten(l)))

    def testCollapseToLevel(self):
        l = [[1], 2, [[3], 4], [[[5]]]]
        self.assertEqual(list(mi.collapse(l, levels=2)), [1, 2, 3, 4, [5]])
        self.assertEqual(
            list(mi.collapse(mi.collapse(l, levels=1), levels=1)),
            list(mi.collapse(l, levels=2)),
        )

    def testCollapseToList(self):
        l = (1, [2], (3, [4, (5,)], 'ab'))
        actual = list(mi.collapse(l, baseType=list))
        expected = [1, [2], 3, [4, (5,)], 'ab']
        self.assertEqual(actual, expected)


class SideEffectTests(TestCase):
    """Tests for ``side_effect()``"""

    def testIndividual(self):
        # The function increments the counter for each call
        counter = [0]

        def func(arg):
            counter[0] += 1

        result = list(mi.sideEffect(func, range(10)))
        self.assertEqual(result, list(range(10)))
        self.assertEqual(counter[0], 10)

    def testChunked(self):
        # The function increments the counter for each call
        counter = [0]

        def func(arg):
            counter[0] += 1

        result = list(mi.sideEffect(func, range(10), 2))
        self.assertEqual(result, list(range(10)))
        self.assertEqual(counter[0], 5)

    def testBeforeAfter(self):
        f = StringIO()
        collector = []

        def func(item):
            print(item, file=f)
            collector.append(f.getvalue())

        def it():
            yield 'a'
            yield 'b'
            raise RuntimeError('kaboom')

        before = lambda: print('HEADER', file=f)
        after = f.close

        try:
            mi.consume(mi.sideEffect(func, it(), before=before, after=after))
        except RuntimeError:
            pass

        # The iterable should have been written to the file
        self.assertEqual(collector, ['HEADER\na\n', 'HEADER\na\nb\n'])

        # The file should be closed even though something bad happened
        self.assertTrue(f.closed)

    def testBeforeFails(self):
        f = StringIO()
        func = lambda x: print(x, file=f)

        def before():
            raise RuntimeError('ouch')

        try:
            mi.consume(
                mi.sideEffect(func, 'abc', before=before, after=f.close)
            )
        except RuntimeError:
            pass

        # The file should be closed even though something bad happened in the
        # before function
        self.assertTrue(f.closed)


class SlicedTests(TestCase):
    """Tests for ``sliced()``"""

    def testEven(self):
        """Test when the length of the sequence is divisible by *n*"""
        seq = 'ABCDEFGHI'
        self.assertEqual(list(mi.sliced(seq, 3)), ['ABC', 'DEF', 'GHI'])

    def testOdd(self):
        """Test when the length of the sequence is not divisible by *n*"""
        seq = 'ABCDEFGHI'
        self.assertEqual(list(mi.sliced(seq, 4)), ['ABCD', 'EFGH', 'I'])

    def testNotSliceable(self):
        seq = (x for x in 'ABCDEFGHI')

        with self.assertRaises(TypeError):
            list(mi.sliced(seq, 3))

    def testOddAndStrict(self):
        seq = [x for x in 'ABCDEFGHI']

        with self.assertRaises(ValueError):
            list(mi.sliced(seq, 4, strict=True))

    def testNumpyLikeArray(self):
        # Numpy arrays don't behave like Python lists - calling bool()
        # on them doesn't return False for empty lists and True for non-empty
        # ones. Emulate that behavior.
        class FalseList(list):
            def __getitem__(self, key):
                ret = super().__getitem__(key)
                if isinstance(key, slice):
                    return FalseList(ret)

                return ret

            def __bool__(self):
                return False

        seq = FalseList(range(9))
        actual = list(mi.sliced(seq, 3))
        expected = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
        self.assertEqual(actual, expected)


class SplitAtTests(TestCase):
    def testBasic(self):
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
                it = iter(iterable)
                pred = lambda x: x == separator
                actual = [''.join(x) for x in mi.splitAt(it, pred)]
                expected = iterable.split(separator)
                self.assertEqual(actual, expected)

    def testMaxsplit(self):
        iterable = 'a,bb,ccc,dddd'
        separator = ','
        pred = lambda x: x == separator

        for maxsplit in range(-1, 4):
            with self.subTest(maxsplit=maxsplit):
                it = iter(iterable)
                result = mi.splitAt(it, pred, maxsplit=maxsplit)
                actual = [''.join(x) for x in result]
                expected = iterable.split(separator, maxsplit)
                self.assertEqual(actual, expected)

    def testKeepSeparator(self):
        separator = ','
        pred = lambda x: x == separator

        for iterable, expected in [
            ('a,bb,ccc', ['a', ',', 'bb', ',', 'ccc']),
            (',a,bb,ccc', ['', ',', 'a', ',', 'bb', ',', 'ccc']),
            ('a,bb,ccc,', ['a', ',', 'bb', ',', 'ccc', ',', '']),
        ]:
            with self.subTest(iterable=iterable):
                it = iter(iterable)
                result = mi.splitAt(it, pred, keepSeparator=True)
                actual = [''.join(x) for x in result]
                self.assertEqual(actual, expected)

    def testCombination(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        pred = lambda x: x % 3 == 0
        actual = list(
            mi.splitAt(iterable, pred, maxsplit=2, keepSeparator=True)
        )
        expected = [[1, 2], [3], [4, 5], [6], [7, 8, 9, 10]]
        self.assertEqual(actual, expected)


class SplitBeforeTest(TestCase):
    """Tests for ``split_before()``"""

    def testStartsWithSep(self):
        actual = list(mi.splitBefore('xooxoo', lambda c: c == 'x'))
        expected = [['x', 'o', 'o'], ['x', 'o', 'o']]
        self.assertEqual(actual, expected)

    def testEndsWithSep(self):
        actual = list(mi.splitBefore('ooxoox', lambda c: c == 'x'))
        expected = [['o', 'o'], ['x', 'o', 'o'], ['x']]
        self.assertEqual(actual, expected)

    def testNoSep(self):
        actual = list(mi.splitBefore('ooo', lambda c: c == 'x'))
        expected = [['o', 'o', 'o']]
        self.assertEqual(actual, expected)

    def testEmptyCollection(self):
        actual = list(mi.splitBefore([], lambda c: bool(c)))
        expected = []
        self.assertEqual(actual, expected)

    def testMaxSplit(self):
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
            actual = list(mi.splitBefore(*args))
            self.assertEqual(actual, expected)


class SplitAfterTest(TestCase):
    """Tests for ``split_after()``"""

    def testStartsWithSep(self):
        actual = list(mi.splitAfter('xooxoo', lambda c: c == 'x'))
        expected = [['x'], ['o', 'o', 'x'], ['o', 'o']]
        self.assertEqual(actual, expected)

    def testEndsWithSep(self):
        actual = list(mi.splitAfter('ooxoox', lambda c: c == 'x'))
        expected = [['o', 'o', 'x'], ['o', 'o', 'x']]
        self.assertEqual(actual, expected)

    def testNoSep(self):
        actual = list(mi.splitAfter('ooo', lambda c: c == 'x'))
        expected = [['o', 'o', 'o']]
        self.assertEqual(actual, expected)

    def testMaxSplit(self):
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
            actual = list(mi.splitAfter(*args))
            self.assertEqual(actual, expected)


class SplitWhenTests(TestCase):
    """Tests for ``split_when()``"""

    @staticmethod
    def _splitWhenBefore(iterable, pred):
        return mi.splitWhen(iterable, lambda _, c: pred(c))

    @staticmethod
    def _splitWhenAfter(iterable, pred):
        return mi.splitWhen(iterable, lambda c, _: pred(c))

    # split_before emulation
    def testBeforeEmulationStartsWithSep(self):
        actual = list(self._splitWhenBefore('xooxoo', lambda c: c == 'x'))
        expected = [['x', 'o', 'o'], ['x', 'o', 'o']]
        self.assertEqual(actual, expected)

    def testBeforeEmulationEndsWithSep(self):
        actual = list(self._splitWhenBefore('ooxoox', lambda c: c == 'x'))
        expected = [['o', 'o'], ['x', 'o', 'o'], ['x']]
        self.assertEqual(actual, expected)

    def testBeforeEmulationNoSep(self):
        actual = list(self._splitWhenBefore('ooo', lambda c: c == 'x'))
        expected = [['o', 'o', 'o']]
        self.assertEqual(actual, expected)

    # split_after emulation
    def testAfterEmulationStartsWithSep(self):
        actual = list(self._splitWhenAfter('xooxoo', lambda c: c == 'x'))
        expected = [['x'], ['o', 'o', 'x'], ['o', 'o']]
        self.assertEqual(actual, expected)

    def testAfterEmulationEndsWithSep(self):
        actual = list(self._splitWhenAfter('ooxoox', lambda c: c == 'x'))
        expected = [['o', 'o', 'x'], ['o', 'o', 'x']]
        self.assertEqual(actual, expected)

    def testAfterEmulationNoSep(self):
        actual = list(self._splitWhenAfter('ooo', lambda c: c == 'x'))
        expected = [['o', 'o', 'o']]
        self.assertEqual(actual, expected)

    # edge cases
    def testEmptyIterable(self):
        actual = list(mi.splitWhen('', lambda a, b: a != b))
        expected = []
        self.assertEqual(actual, expected)

    def testOneElement(self):
        actual = list(mi.splitWhen('o', lambda a, b: a == b))
        expected = [['o']]
        self.assertEqual(actual, expected)

    def testOneElementIsSecondItem(self):
        actual = list(self._splitWhenBefore('x', lambda c: c == 'x'))
        expected = [['x']]
        self.assertEqual(actual, expected)

    def testOneElementIsFirstItem(self):
        actual = list(self._splitWhenAfter('x', lambda c: c == 'x'))
        expected = [['x']]
        self.assertEqual(actual, expected)

    def testMaxSplit(self):
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
            actual = list(mi.splitWhen(*args))
            self.assertEqual(actual, expected, str(args))


class SplitIntoTests(TestCase):
    """Tests for ``split_into()``"""

    def testIterableJustRight(self):
        """Size of ``iterable`` equals the sum of ``sizes``."""
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [2, 3, 4]
        expected = [[1, 2], [3, 4, 5], [6, 7, 8, 9]]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testIterableTooSmall(self):
        """Size of ``iterable`` is smaller than sum of ``sizes``. Last return
        list is shorter as a result."""
        iterable = [1, 2, 3, 4, 5, 6, 7]
        sizes = [2, 3, 4]
        expected = [[1, 2], [3, 4, 5], [6, 7]]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testIterableTooSmallExtra(self):
        """Size of ``iterable`` is smaller than sum of ``sizes``. Second last
        return list is shorter and last return list is empty as a result."""
        iterable = [1, 2, 3, 4, 5, 6, 7]
        sizes = [2, 3, 4, 5]
        expected = [[1, 2], [3, 4, 5], [6, 7], []]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testIterableTooLarge(self):
        """Size of ``iterable`` is larger than sum of ``sizes``. Not all
        items of iterable are returned."""
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [2, 3, 2]
        expected = [[1, 2], [3, 4, 5], [6, 7]]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testUsingNoneWithLeftover(self):
        """Last item of ``sizes`` is None when items still remain in
        ``iterable``. Last list returned stretches to fit all remaining items
        of ``iterable``."""
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [2, 3, None]
        expected = [[1, 2], [3, 4, 5], [6, 7, 8, 9]]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testUsingNoneWithoutLeftover(self):
        """Last item of ``sizes`` is None when no items remain in
        ``iterable``. Last list returned is empty."""
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [2, 3, 4, None]
        expected = [[1, 2], [3, 4, 5], [6, 7, 8, 9], []]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testUsingNoneMidSizes(self):
        """None is present in ``sizes`` but is not the last item. Last list
        returned stretches to fit all remaining items of ``iterable`` but
        all items in ``sizes`` after None are ignored."""
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [2, 3, None, 4]
        expected = [[1, 2], [3, 4, 5], [6, 7, 8, 9]]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testIterableEmpty(self):
        """``iterable`` argument is empty but ``sizes`` is not. An empty
        list is returned for each item in ``sizes``."""
        iterable = []
        sizes = [2, 4, 2]
        expected = [[], [], []]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testIterableEmptyUsingNone(self):
        """``iterable`` argument is empty but ``sizes`` is not. An empty
        list is returned for each item in ``sizes`` that is not after a
        None item."""
        iterable = []
        sizes = [2, 4, None, 2]
        expected = [[], [], []]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testSizesEmpty(self):
        """``sizes`` argument is empty but ``iterable`` is not. An empty
        generator is returned."""
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = []
        expected = []
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testBothEmpty(self):
        """Both ``sizes`` and ``iterable`` arguments are empty. An empty
        generator is returned."""
        iterable = []
        sizes = []
        expected = []
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testBoolInSizes(self):
        """A bool object is present in ``sizes`` is treated as a 1 or 0 for
        ``True`` or ``False`` due to bool being an instance of int."""
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [3, True, 2, False]
        expected = [[1, 2, 3], [4], [5, 6], []]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testInvalidInSizes(self):
        """A ValueError is raised if an object in ``sizes`` is neither ``None``
        or an integer."""
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [1, [], 3]
        with self.assertRaises(ValueError):
            list(mi.splitInto(iterable, sizes))

    def testInvalidInSizesAfterNone(self):
        """A item in ``sizes`` that is invalid will not raise a TypeError if it
        comes after a ``None`` item."""
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [3, 4, None, []]
        expected = [[1, 2, 3], [4, 5, 6, 7], [8, 9]]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

    def testGeneratorIterableIntegrity(self):
        """Check that if ``iterable`` is an iterator, it is consumed only by as
        many items as the sum of ``sizes``."""
        iterable = (i for i in range(10))
        sizes = [2, 3]

        expected = [[0, 1], [2, 3, 4]]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

        iterableExpected = [5, 6, 7, 8, 9]
        iterableActual = list(iterable)
        self.assertEqual(iterableActual, iterableExpected)

    def testGeneratorSizesIntegrity(self):
        """Check that if ``sizes`` is an iterator, it is consumed only until a
        ``None`` item is reached"""
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = (i for i in [1, 2, None, 3, 4])

        expected = [[1], [2, 3], [4, 5, 6, 7, 8, 9]]
        actual = list(mi.splitInto(iterable, sizes))
        self.assertEqual(actual, expected)

        sizesExpected = [3, 4]
        sizesActual = list(sizes)
        self.assertEqual(sizesActual, sizesExpected)


class PaddedTest(TestCase):
    """Tests for ``padded()``"""

    def testNoN(self):
        seq = [1, 2, 3]

        # No fillvalue
        self.assertEqual(mi.take(5, mi.padded(seq)), [1, 2, 3, None, None])

        # With fillvalue
        self.assertEqual(
            mi.take(5, mi.padded(seq, fillvalue='')), [1, 2, 3, '', '']
        )

    def testInvalidN(self):
        self.assertRaises(ValueError, lambda: list(mi.padded([1, 2, 3], n=-1)))
        self.assertRaises(ValueError, lambda: list(mi.padded([1, 2, 3], n=0)))

    def testValidN(self):
        seq = [1, 2, 3, 4, 5]

        # No need for padding: len(seq) <= n
        self.assertEqual(list(mi.padded(seq, n=4)), [1, 2, 3, 4, 5])
        self.assertEqual(list(mi.padded(seq, n=5)), [1, 2, 3, 4, 5])

        # No fillvalue
        self.assertEqual(
            list(mi.padded(seq, n=7)), [1, 2, 3, 4, 5, None, None]
        )

        # With fillvalue
        self.assertEqual(
            list(mi.padded(seq, fillvalue='', n=7)), [1, 2, 3, 4, 5, '', '']
        )

    def testNextMultiple(self):
        seq = [1, 2, 3, 4, 5, 6]

        # No need for padding: len(seq) % n == 0
        self.assertEqual(
            list(mi.padded(seq, n=3, nextMultiple=True)), [1, 2, 3, 4, 5, 6]
        )

        # Padding needed: len(seq) < n
        self.assertEqual(
            list(mi.padded(seq, n=8, nextMultiple=True)),
            [1, 2, 3, 4, 5, 6, None, None],
        )

        # No padding needed: len(seq) == n
        self.assertEqual(
            list(mi.padded(seq, n=6, nextMultiple=True)), [1, 2, 3, 4, 5, 6]
        )

        # Padding needed: len(seq) > n
        self.assertEqual(
            list(mi.padded(seq, n=4, nextMultiple=True)),
            [1, 2, 3, 4, 5, 6, None, None],
        )

        # With fillvalue
        self.assertEqual(
            list(mi.padded(seq, fillvalue='', n=4, nextMultiple=True)),
            [1, 2, 3, 4, 5, 6, '', ''],
        )


class RepeatEachTests(TestCase):
    """Tests for repeat_each()"""

    def testDefault(self):
        actual = list(mi.repeatEach('ABC'))
        expected = ['A', 'A', 'B', 'B', 'C', 'C']
        self.assertEqual(actual, expected)

    def testBasic(self):
        actual = list(mi.repeatEach('ABC', 3))
        expected = ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C']
        self.assertEqual(actual, expected)

    def testEmpty(self):
        actual = list(mi.repeatEach(''))
        expected = []
        self.assertEqual(actual, expected)

    def testNoRepeat(self):
        actual = list(mi.repeatEach('ABC', 0))
        expected = []
        self.assertEqual(actual, expected)

    def testNegativeRepeat(self):
        actual = list(mi.repeatEach('ABC', -1))
        expected = []
        self.assertEqual(actual, expected)

    def testInfiniteInput(self):
        repeater = mi.repeatEach(cycle('AB'))
        actual = mi.take(6, repeater)
        expected = ['A', 'A', 'B', 'B', 'A', 'A']
        self.assertEqual(actual, expected)


class RepeatLastTests(TestCase):
    def testEmptyIterable(self):
        sliceLength = 3
        iterable = iter([])
        actual = mi.take(sliceLength, mi.repeatLast(iterable))
        expected = [None] * sliceLength
        self.assertEqual(actual, expected)

    def testDefaultValue(self):
        sliceLength = 3
        iterable = iter([])
        default = '3'
        actual = mi.take(sliceLength, mi.repeatLast(iterable, default))
        expected = ['3'] * sliceLength
        self.assertEqual(actual, expected)

    def testBasic(self):
        sliceLength = 10
        iterable = (str(x) for x in range(5))
        actual = mi.take(sliceLength, mi.repeatLast(iterable))
        expected = ['0', '1', '2', '3', '4', '4', '4', '4', '4', '4']
        self.assertEqual(actual, expected)


class DistributeTest(TestCase):
    """Tests for distribute()"""

    def testInvalidN(self):
        self.assertRaises(ValueError, lambda: mi.distribute(-1, [1, 2, 3]))
        self.assertRaises(ValueError, lambda: mi.distribute(0, [1, 2, 3]))

    def testBasic(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        for n, expected in [
            (1, [iterable]),
            (2, [[1, 3, 5, 7, 9], [2, 4, 6, 8, 10]]),
            (3, [[1, 4, 7, 10], [2, 5, 8], [3, 6, 9]]),
            (10, [[n] for n in range(1, 10 + 1)]),
        ]:
            self.assertEqual(
                [list(x) for x in mi.distribute(n, iterable)], expected
            )

    def testLargeN(self):
        iterable = [1, 2, 3, 4]
        self.assertEqual(
            [list(x) for x in mi.distribute(6, iterable)],
            [[1], [2], [3], [4], [], []],
        )


class StaggerTest(TestCase):
    """Tests for ``stagger()``"""

    def testDefault(self):
        iterable = [0, 1, 2, 3]
        actual = list(mi.stagger(iterable))
        expected = [(None, 0, 1), (0, 1, 2), (1, 2, 3)]
        self.assertEqual(actual, expected)

    def testOffsets(self):
        iterable = [0, 1, 2, 3]
        for offsets, expected in [
            ((-2, 0, 2), [('', 0, 2), ('', 1, 3)]),
            ((-2, -1), [('', ''), ('', 0), (0, 1), (1, 2), (2, 3)]),
            ((1, 2), [(1, 2), (2, 3)]),
        ]:
            allGroups = mi.stagger(iterable, offsets=offsets, fillvalue='')
            self.assertEqual(list(allGroups), expected)

    def testLongest(self):
        iterable = [0, 1, 2, 3]
        for offsets, expected in [
            (
                (-1, 0, 1),
                [('', 0, 1), (0, 1, 2), (1, 2, 3), (2, 3, ''), (3, '', '')],
            ),
            ((-2, -1), [('', ''), ('', 0), (0, 1), (1, 2), (2, 3), (3, '')]),
            ((1, 2), [(1, 2), (2, 3), (3, '')]),
        ]:
            allGroups = mi.stagger(
                iterable, offsets=offsets, fillvalue='', longest=True
            )
            self.assertEqual(list(allGroups), expected)


class ZipOffsetTest(TestCase):
    """Tests for ``zip_offset()``"""

    def testShortest(self):
        a1 = [0, 1, 2, 3]
        a2 = [0, 1, 2, 3, 4, 5]
        a3 = [0, 1, 2, 3, 4, 5, 6, 7]
        actual = list(
            mi.zipOffset(a1, a2, a3, offsets=(-1, 0, 1), fillvalue='')
        )
        expected = [('', 0, 1), (0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]
        self.assertEqual(actual, expected)

    def testLongest(self):
        a1 = [0, 1, 2, 3]
        a2 = [0, 1, 2, 3, 4, 5]
        a3 = [0, 1, 2, 3, 4, 5, 6, 7]
        actual = list(
            mi.zipOffset(a1, a2, a3, offsets=(-1, 0, 1), longest=True)
        )
        expected = [
            (None, 0, 1),
            (0, 1, 2),
            (1, 2, 3),
            (2, 3, 4),
            (3, 4, 5),
            (None, 5, 6),
            (None, None, 7),
        ]
        self.assertEqual(actual, expected)

    def testMismatch(self):
        iterables = [0, 1, 2], [2, 3, 4]
        offsets = (-1, 0, 1)
        self.assertRaises(
            ValueError,
            lambda: list(mi.zipOffset(*iterables, offsets=offsets)),
        )


class UnzipTests(TestCase):
    """Tests for unzip()"""

    def testEmptyIterable(self):
        self.assertEqual(list(mi.unzip([])), [])
        # in reality zip([], [], []) is equivalent to iter([])
        # but it doesn't hurt to test both
        self.assertEqual(list(mi.unzip(zip([], [], []))), [])

    def testLengthOneIterable(self):
        xs, ys, zs = mi.unzip(zip([1], [2], [3]))
        self.assertEqual(list(xs), [1])
        self.assertEqual(list(ys), [2])
        self.assertEqual(list(zs), [3])

    def testNormalCase(self):
        xs, ys, zs = range(10), range(1, 11), range(2, 12)
        zipped = zip(xs, ys, zs)
        xs, ys, zs = mi.unzip(zipped)
        self.assertEqual(list(xs), list(range(10)))
        self.assertEqual(list(ys), list(range(1, 11)))
        self.assertEqual(list(zs), list(range(2, 12)))

    def testImproperlyZipped(self):
        zipped = iter([(1, 2, 3), (4, 5), (6,)])
        xs, ys, zs = mi.unzip(zipped)
        self.assertEqual(list(xs), [1, 4, 6])
        self.assertEqual(list(ys), [2, 5])
        self.assertEqual(list(zs), [3])

    def testIncreasinglyZipped(self):
        zipped = iter([(1, 2), (3, 4, 5), (6, 7, 8, 9)])
        unzipped = mi.unzip(zipped)
        # from the docstring:
        # len(first tuple) is the number of iterables zipped
        self.assertEqual(len(unzipped), 2)
        xs, ys = unzipped
        self.assertEqual(list(xs), [1, 3, 6])
        self.assertEqual(list(ys), [2, 4, 7])


class SortTogetherTest(TestCase):
    """Tests for sort_together()"""

    def testKeyList(self):
        """tests `key_list` including default, iterables include duplicates"""
        iterables = [
            ['GA', 'GA', 'GA', 'CT', 'CT', 'CT'],
            ['May', 'Aug.', 'May', 'June', 'July', 'July'],
            [97, 20, 100, 70, 100, 20],
        ]

        self.assertEqual(
            mi.sortTogether(iterables),
            [
                ('CT', 'CT', 'CT', 'GA', 'GA', 'GA'),
                ('June', 'July', 'July', 'May', 'Aug.', 'May'),
                (70, 100, 20, 97, 20, 100),
            ],
        )

        self.assertEqual(
            mi.sortTogether(iterables, keyList=(0, 1)),
            [
                ('CT', 'CT', 'CT', 'GA', 'GA', 'GA'),
                ('July', 'July', 'June', 'Aug.', 'May', 'May'),
                (100, 20, 70, 20, 97, 100),
            ],
        )

        self.assertEqual(
            mi.sortTogether(iterables, keyList=(0, 1, 2)),
            [
                ('CT', 'CT', 'CT', 'GA', 'GA', 'GA'),
                ('July', 'July', 'June', 'Aug.', 'May', 'May'),
                (20, 100, 70, 20, 97, 100),
            ],
        )

        self.assertEqual(
            mi.sortTogether(iterables, keyList=(2,)),
            [
                ('GA', 'CT', 'CT', 'GA', 'GA', 'CT'),
                ('Aug.', 'July', 'June', 'May', 'May', 'July'),
                (20, 20, 70, 97, 100, 100),
            ],
        )

    def testInvalidKeyList(self):
        """tests `key_list` for indexes not available in `iterables`"""
        iterables = [
            ['GA', 'GA', 'GA', 'CT', 'CT', 'CT'],
            ['May', 'Aug.', 'May', 'June', 'July', 'July'],
            [97, 20, 100, 70, 100, 20],
        ]

        self.assertRaises(
            IndexError, lambda: mi.sortTogether(iterables, keyList=(5,))
        )

    def testKeyFunction(self):
        """tests `key` function, including interaction with `key_list`"""
        iterables = [
            ['GA', 'GA', 'GA', 'CT', 'CT', 'CT'],
            ['May', 'Aug.', 'May', 'June', 'July', 'July'],
            [97, 20, 100, 70, 100, 20],
        ]
        self.assertEqual(
            mi.sortTogether(iterables, key=lambda x: x),
            [
                ('CT', 'CT', 'CT', 'GA', 'GA', 'GA'),
                ('June', 'July', 'July', 'May', 'Aug.', 'May'),
                (70, 100, 20, 97, 20, 100),
            ],
        )
        self.assertEqual(
            mi.sortTogether(iterables, key=lambda x: x[::-1]),
            [
                ('GA', 'GA', 'GA', 'CT', 'CT', 'CT'),
                ('May', 'Aug.', 'May', 'June', 'July', 'July'),
                (97, 20, 100, 70, 100, 20),
            ],
        )
        self.assertEqual(
            mi.sortTogether(
                iterables,
                keyList=(0, 2),
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

    def testReverse(self):
        """tests `reverse` to ensure a reverse sort for `key_list` iterables"""
        iterables = [
            ['GA', 'GA', 'GA', 'CT', 'CT', 'CT'],
            ['May', 'Aug.', 'May', 'June', 'July', 'July'],
            [97, 20, 100, 70, 100, 20],
        ]

        self.assertEqual(
            mi.sortTogether(iterables, keyList=(0, 1, 2), reverse=True),
            [
                ('GA', 'GA', 'GA', 'CT', 'CT', 'CT'),
                ('May', 'May', 'Aug.', 'June', 'July', 'July'),
                (100, 97, 20, 70, 100, 20),
            ],
        )

    def testUnevenIterables(self):
        """tests trimming of iterables to the shortest length before sorting"""
        iterables = [
            ['GA', 'GA', 'GA', 'CT', 'CT', 'CT', 'MA'],
            ['May', 'Aug.', 'May', 'June', 'July', 'July'],
            [97, 20, 100, 70, 100, 20, 0],
        ]

        self.assertEqual(
            mi.sortTogether(iterables),
            [
                ('CT', 'CT', 'CT', 'GA', 'GA', 'GA'),
                ('June', 'July', 'July', 'May', 'Aug.', 'May'),
                (70, 100, 20, 97, 20, 100),
            ],
        )

    def testStrict(self):
        # Test for list of lists or tuples
        self.assertRaises(
            ValueError,
            lambda: mi.sortTogether(
                [(4, 3, 2, 1), ('a', 'b', 'c')], strict=True
            ),
        )

        # Test for list of iterables
        self.assertRaises(
            ValueError,
            lambda: mi.sortTogether([range(4), range(5)], strict=True),
        )

        # Test for iterable of iterables
        self.assertRaises(
            ValueError,
            lambda: mi.sortTogether(
                (range(i) for i in range(4)), strict=True
            ),
        )


class DivideTest(TestCase):
    """Tests for divide()"""

    def testInvalidN(self):
        self.assertRaises(ValueError, lambda: mi.divide(-1, [1, 2, 3]))
        self.assertRaises(ValueError, lambda: mi.divide(0, [1, 2, 3]))

    def testBasic(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        for n, expected in [
            (1, [iterable]),
            (2, [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]),
            (3, [[1, 2, 3, 4], [5, 6, 7], [8, 9, 10]]),
            (10, [[n] for n in range(1, 10 + 1)]),
        ]:
            self.assertEqual(
                [list(x) for x in mi.divide(n, iterable)], expected
            )

    def testLargeN(self):
        self.assertEqual(
            [list(x) for x in mi.divide(6, iter(range(1, 4 + 1)))],
            [[1], [2], [3], [4], [], []],
        )


class TestAlwaysIterable(TestCase):
    """Tests for always_iterable()"""

    def testSingle(self):
        self.assertEqual(list(mi.alwaysIterable(1)), [1])

    def testStrings(self):
        for obj in ['foo', b'bar', 'baz']:
            actual = list(mi.alwaysIterable(obj))
            expected = [obj]
            self.assertEqual(actual, expected)

    def testBaseType(self):
        dictObj = {'a': 1, 'b': 2}
        strObj = '123'

        # Default: dicts are iterable like they normally are
        defaultActual = list(mi.alwaysIterable(dictObj))
        defaultExpected = list(dictObj)
        self.assertEqual(defaultActual, defaultExpected)

        # Unitary types set: dicts are not iterable
        customActual = list(mi.alwaysIterable(dictObj, baseType=dict))
        customExpected = [dictObj]
        self.assertEqual(customActual, customExpected)

        # With unitary types set, strings are iterable
        strActual = list(mi.alwaysIterable(strObj, baseType=None))
        strExpected = list(strObj)
        self.assertEqual(strActual, strExpected)

        # base_type handles nested tuple (via isinstance).
        baseType = ((dict,),)
        customActual = list(mi.alwaysIterable(dictObj, baseType=baseType))
        customExpected = [dictObj]
        self.assertEqual(customActual, customExpected)

    def testIterables(self):
        self.assertEqual(list(mi.alwaysIterable([0, 1])), [0, 1])
        self.assertEqual(
            list(mi.alwaysIterable([0, 1], baseType=list)), [[0, 1]]
        )
        self.assertEqual(
            list(mi.alwaysIterable(iter('foo'))), ['f', 'o', 'o']
        )
        self.assertEqual(list(mi.alwaysIterable([])), [])

    def testNone(self):
        self.assertEqual(list(mi.alwaysIterable(None)), [])

    def testGenerator(self):
        def _gen():
            yield 0
            yield 1

        self.assertEqual(list(mi.alwaysIterable(_gen())), [0, 1])


class AdjacentTests(TestCase):
    def testTypical(self):
        actual = list(mi.adjacent(lambda x: x % 5 == 0, range(10)))
        expected = [
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
        self.assertEqual(actual, expected)

    def testEmptyIterable(self):
        actual = list(mi.adjacent(lambda x: x % 5 == 0, []))
        expected = []
        self.assertEqual(actual, expected)

    def testLengthOne(self):
        actual = list(mi.adjacent(lambda x: x % 5 == 0, [0]))
        expected = [(True, 0)]
        self.assertEqual(actual, expected)

        actual = list(mi.adjacent(lambda x: x % 5 == 0, [1]))
        expected = [(False, 1)]
        self.assertEqual(actual, expected)

    def testConsecutiveTrue(self):
        """Test that when the predicate matches multiple consecutive elements
        it doesn't repeat elements in the output"""
        actual = list(mi.adjacent(lambda x: x % 5 < 2, range(10)))
        expected = [
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
        self.assertEqual(actual, expected)

    def testDistance(self):
        actual = list(mi.adjacent(lambda x: x % 5 == 0, range(10), distance=2))
        expected = [
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
        self.assertEqual(actual, expected)

        actual = list(mi.adjacent(lambda x: x % 5 == 0, range(10), distance=3))
        expected = [
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
        self.assertEqual(actual, expected)

    def testLargeDistance(self):
        """Test distance larger than the length of the iterable"""
        iterable = range(10)
        actual = list(mi.adjacent(lambda x: x % 5 == 4, iterable, distance=20))
        expected = list(zip(repeat(True), iterable))
        self.assertEqual(actual, expected)

        actual = list(mi.adjacent(lambda x: False, iterable, distance=20))
        expected = list(zip(repeat(False), iterable))
        self.assertEqual(actual, expected)

    def testZeroDistance(self):
        """Test that adjacent() reduces to zip+map when distance is 0"""
        iterable = range(1000)
        predicate = lambda x: x % 4 == 2
        actual = mi.adjacent(predicate, iterable, 0)
        expected = zip(map(predicate, iterable), iterable)
        self.assertTrue(all(a == e for a, e in zip(actual, expected)))

    def testNegativeDistance(self):
        """Test that adjacent() raises an error with negative distance"""
        pred = lambda x: x
        self.assertRaises(
            ValueError, lambda: mi.adjacent(pred, range(1000), -1)
        )
        self.assertRaises(
            ValueError, lambda: mi.adjacent(pred, range(10), -10)
        )

    def testGrouping(self):
        """Test interaction of adjacent() with groupby_transform()"""
        iterable = mi.adjacent(lambda x: x % 5 == 0, range(10))
        grouper = mi.groupbyTransform(iterable, itemgetter(0), itemgetter(1))
        actual = [(k, list(g)) for k, g in grouper]
        expected = [
            (True, [0, 1]),
            (False, [2, 3]),
            (True, [4, 5, 6]),
            (False, [7, 8, 9]),
        ]
        self.assertEqual(actual, expected)

    def testCallOnce(self):
        """Test that the predicate is only called once per item."""
        alreadySeen = set()
        iterable = range(10)

        def predicate(item):
            self.assertNotIn(item, alreadySeen)
            alreadySeen.add(item)
            return True

        actual = list(mi.adjacent(predicate, iterable))
        expected = [(True, x) for x in iterable]
        self.assertEqual(actual, expected)


class GroupByTransformTests(TestCase):
    def assertAllGroupsEqual(self, groupby1, groupby2):
        for a, b in zip(groupby1, groupby2):
            key1, group1 = a
            key2, group2 = b
            self.assertEqual(key1, key2)
            self.assertListEqual(list(group1), list(group2))
        self.assertRaises(StopIteration, lambda: next(groupby1))
        self.assertRaises(StopIteration, lambda: next(groupby2))

    def testDefaultFuncs(self):
        iterable = [(x // 5, x) for x in range(1000)]
        actual = mi.groupbyTransform(iterable)
        expected = groupby(iterable)
        self.assertAllGroupsEqual(actual, expected)

    def testValuefunc(self):
        iterable = [(int(x / 5), int(x / 3), x) for x in range(10)]

        # Test the standard usage of grouping one iterable using another's keys
        grouper = mi.groupbyTransform(
            iterable, keyfunc=itemgetter(0), valuefunc=itemgetter(-1)
        )
        actual = [(k, list(g)) for k, g in grouper]
        expected = [(0, [0, 1, 2, 3, 4]), (1, [5, 6, 7, 8, 9])]
        self.assertEqual(actual, expected)

        grouper = mi.groupbyTransform(
            iterable, keyfunc=itemgetter(1), valuefunc=itemgetter(-1)
        )
        actual = [(k, list(g)) for k, g in grouper]
        expected = [(0, [0, 1, 2]), (1, [3, 4, 5]), (2, [6, 7, 8]), (3, [9])]
        self.assertEqual(actual, expected)

        # and now for something a little different
        d = dict(zip(range(10), 'abcdefghij'))
        grouper = mi.groupbyTransform(
            range(10), keyfunc=lambda x: x // 5, valuefunc=d.get
        )
        actual = [(k, ''.join(g)) for k, g in grouper]
        expected = [(0, 'abcde'), (1, 'fghij')]
        self.assertEqual(actual, expected)

    def testNoValuefunc(self):
        iterable = range(1000)

        def key(x):
            return x // 5

        actual = mi.groupbyTransform(iterable, key, valuefunc=None)
        expected = groupby(iterable, key)
        self.assertAllGroupsEqual(actual, expected)

        actual = mi.groupbyTransform(iterable, key)  # default valuefunc
        expected = groupby(iterable, key)
        self.assertAllGroupsEqual(actual, expected)

    def testReducefunc(self):
        iterable = range(50)
        keyfunc = lambda k: 10 * (k // 10)
        valuefunc = lambda v: v + 1
        reducefunc = sum
        actual = list(
            mi.groupbyTransform(
                iterable,
                keyfunc=keyfunc,
                valuefunc=valuefunc,
                reducefunc=reducefunc,
            )
        )
        expected = [(0, 55), (10, 155), (20, 255), (30, 355), (40, 455)]
        self.assertEqual(actual, expected)


class NumericRangeTests(TestCase):
    def testBasic(self):
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
            actual = list(mi.numericRange(*args))
            self.assertEqual(expected, actual)
            self.assertTrue(
                all(type(a) is type(e) for a, e in zip(actual, expected))
            )

    def testArgCount(self):
        for args, message in [
            ((), 'numeric_range expected at least 1 argument, got 0'),
            (
                (0, 1, 2, 3),
                'numeric_range expected at most 3 arguments, got 4',
            ),
        ]:
            with self.assertRaisesRegex(TypeError, message):
                mi.numericRange(*args)

    def testZeroStep(self):
        for args in [
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
                list(mi.numericRange(*args))

    def testBool(self):
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
            self.assertEqual(expected, bool(mi.numericRange(*args)))

    def testContains(self):
        for args, expectedIn, expectedNotIn in [
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
            r = mi.numericRange(*args)
            for v in expectedIn:
                self.assertTrue(v in r)
                self.assertFalse(v not in r)

            for v in expectedNotIn:
                self.assertFalse(v in r)
                self.assertTrue(v not in r)

    def testEq(self):
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
                mi.numericRange(*args1), mi.numericRange(*args2)
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
                mi.numericRange(*args1), mi.numericRange(*args2)
            )

        self.assertNotEqual(mi.numericRange(7.0), 1)
        self.assertNotEqual(mi.numericRange(7.0), "abc")

    def testGetItemByIndex(self):
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
            self.assertEqual(expected, mi.numericRange(*args)[index])

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
                mi.numericRange(*args)[index]

    def testGetItemBySlice(self):
        for args, sl, expectedArgs in [
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
                mi.numericRange(*expectedArgs), mi.numericRange(*args)[sl]
            )

    def testHash(self):
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
            self.assertEqual(expected, hash(mi.numericRange(*args)))

    def testIterTwice(self):
        r1 = mi.numericRange(1.0, 9.9, 1.5)
        r2 = mi.numericRange(8.5, 0.0, -1.5)
        self.assertEqual([1.0, 2.5, 4.0, 5.5, 7.0, 8.5], list(r1))
        self.assertEqual([1.0, 2.5, 4.0, 5.5, 7.0, 8.5], list(r1))
        self.assertEqual([8.5, 7.0, 5.5, 4.0, 2.5, 1.0], list(r2))
        self.assertEqual([8.5, 7.0, 5.5, 4.0, 2.5, 1.0], list(r2))

    def testLen(self):
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
            self.assertEqual(expected, len(mi.numericRange(*args)))

    def testRepr(self):
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
                self.assertIn(repr(mi.numericRange(*args)), expected)

    def testReversed(self):
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
            self.assertEqual(expected, list(reversed(mi.numericRange(*args))))

    def testCount(self):
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
            self.assertEqual(c, mi.numericRange(*args).count(v))

    def testIndex(self):
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
            self.assertEqual(i, mi.numericRange(*args).index(v))

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
                mi.numericRange(*args).index(v)

    def testParentClasses(self):
        r = mi.numericRange(7.0)
        self.assertTrue(isinstance(r, Iterable))
        self.assertFalse(isinstance(r, Iterator))
        self.assertTrue(isinstance(r, Sequence))
        self.assertTrue(isinstance(r, Hashable))

    def testBadKey(self):
        r = mi.numericRange(7.0)
        for arg, message in [
            ('a', 'numeric range indices must be integers or slices, not str'),
            (
                (),
                'numeric range indices must be integers or slices, not tuple',
            ),
        ]:
            with self.assertRaisesRegex(TypeError, message):
                r[arg]

    def testPickle(self):
        for args in [
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
            r = mi.numericRange(*args)
            self.assertTrue(dumps(r))  # assert not empty
            self.assertEqual(r, loads(dumps(r)))


class CountCycleTests(TestCase):
    def testBasic(self):
        expected = [
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
        for actual in [
            mi.take(9, mi.countCycle('abc')),  # n=None
            list(mi.countCycle('abc', 3)),  # n=3
        ]:
            self.assertEqual(actual, expected)

    def testEmpty(self):
        self.assertEqual(list(mi.countCycle('')), [])
        self.assertEqual(list(mi.countCycle('', 2)), [])

    def testNegative(self):
        self.assertEqual(list(mi.countCycle('abc', -3)), [])


class MarkEndsTests(TestCase):
    def testBasic(self):
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
                iterable = map(str, range(size))
                actual = list(mi.markEnds(iterable))
                self.assertEqual(actual, expected)


class LocateTests(TestCase):
    def testDefaultPred(self):
        iterable = [0, 1, 1, 0, 1, 0, 0]
        actual = list(mi.locate(iterable))
        expected = [1, 2, 4]
        self.assertEqual(actual, expected)

    def testNoMatches(self):
        iterable = [0, 0, 0]
        actual = list(mi.locate(iterable))
        expected = []
        self.assertEqual(actual, expected)

    def testCustomPred(self):
        iterable = ['0', 1, 1, '0', 1, '0', '0']
        pred = lambda x: x == '0'
        actual = list(mi.locate(iterable, pred))
        expected = [0, 3, 5, 6]
        self.assertEqual(actual, expected)

    def testWindowSize(self):
        iterable = ['0', 1, 1, '0', 1, '0', '0']
        pred = lambda *args: args == ('0', 1)
        actual = list(mi.locate(iterable, pred, windowSize=2))
        expected = [0, 3]
        self.assertEqual(actual, expected)

    def testWindowSizeLarge(self):
        iterable = [1, 2, 3, 4]
        pred = lambda a, b, c, d, e: True
        actual = list(mi.locate(iterable, pred, windowSize=5))
        expected = [0]
        self.assertEqual(actual, expected)

    def testWindowSizeZero(self):
        iterable = [1, 2, 3, 4]
        pred = lambda: True
        with self.assertRaises(ValueError):
            list(mi.locate(iterable, pred, windowSize=0))


class StripFunctionTests(TestCase):
    def testHashable(self):
        iterable = list('www.example.com')
        pred = lambda x: x in set('cmowz.')

        self.assertEqual(list(mi.lstrip(iterable, pred)), list('example.com'))
        self.assertEqual(list(mi.rstrip(iterable, pred)), list('www.example'))
        self.assertEqual(list(mi.strip(iterable, pred)), list('example'))

    def testNotHashable(self):
        iterable = [
            list('http://'),
            list('www'),
            list('.example'),
            list('.com'),
        ]
        pred = lambda x: x in [list('http://'), list('www'), list('.com')]

        self.assertEqual(list(mi.lstrip(iterable, pred)), iterable[2:])
        self.assertEqual(list(mi.rstrip(iterable, pred)), iterable[:3])
        self.assertEqual(list(mi.strip(iterable, pred)), iterable[2:3])

    def testMath(self):
        iterable = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2]
        pred = lambda x: x <= 2

        self.assertEqual(list(mi.lstrip(iterable, pred)), iterable[3:])
        self.assertEqual(list(mi.rstrip(iterable, pred)), iterable[:-3])
        self.assertEqual(list(mi.strip(iterable, pred)), iterable[3:-3])


class IteratorWithWeakReferences:
    class _anobj:
        pass

    @classmethod
    def FROM_SIZE(cls, size: int) -> IteratorWithWeakReferences:
        return cls([IteratorWithWeakReferences._anobj() for _ in range(size)])

    def __init__(self, iterable: Iterable):
        self._data = deque(element for element in iterable)
        self._weakreferences = [weakref.ref(a) for a in self._data]

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> object:
        if len(self._data) == 0:
            raise StopIteration
        return self._data.popleft()

    def weakReferencesState(self) -> list[bool]:
        return [wr() is not None for wr in self._weakreferences]


class IsliceExtendedTests(TestCase):
    def testAll(self):
        iterable = ['0', '1', '2', '3', '4', '5']
        indexes = [*range(-4, 10), None]
        steps = [1, 2, 3, 4, -1, -2, -3, -4]
        for sliceArgs in product(indexes, indexes, steps):
            with self.subTest(sliceArgs=sliceArgs):
                actual = list(mi.isliceExtended(iterable, *sliceArgs))
                expected = iterable[slice(*sliceArgs)]
                self.assertEqual(actual, expected, sliceArgs)

    def testZeroStep(self):
        with self.assertRaises(ValueError):
            list(mi.isliceExtended([1, 2, 3], 0, 1, 0))

    def testSlicing(self):
        iterable = map(str, count())
        firstSlice = mi.isliceExtended(iterable)[10:]
        secondSlice = mi.isliceExtended(firstSlice)[:10]
        thirdSlice = mi.isliceExtended(secondSlice)[::2]
        self.assertEqual(list(thirdSlice), ['10', '12', '14', '16', '18'])

    def testSlicingExtensive(self):
        iterable = range(10)
        options = (None, 1, 2, 7, -1)
        for start, stop, step in product(options, options, options):
            with self.subTest(sliceArgs=(start, stop, step)):
                slicedTuple0 = tuple(
                    mi.isliceExtended(iterable)[start:stop:step]
                )
                slicedTuple1 = tuple(
                    mi.isliceExtended(iterable, start, stop, step)
                )
                slicedRange = tuple(iterable[start:stop:step])
                self.assertEqual(slicedTuple0, slicedRange)
                self.assertEqual(slicedTuple1, slicedRange)

    def testInvalidSlice(self):
        with self.assertRaises(TypeError):
            mi.isliceExtended(count())[13]

    def testElementsLifecycle(self):
        # CPython does reference counting.
        # GC is not required when ref counting is supported.
        refCountSupported = platform.python_implementation() == 'CPython'

        class TestCase(NamedTuple):
            initialSize: int
            slice: int
            # list of expected intermediate elements states (alive or not)
            # during a complete iteration
            expectedAliveStates: list[list[int]]

        # fmt: off
        testCases = [
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

        for index, testCase in enumerate(testCases):
            with self.subTest(f"{index:02d}", testCase=testCase):
                iterator = IteratorWithWeakReferences.FROM_SIZE(
                    testCase.initialSize
                )
                isliceIterator = mi.isliceExtended(iterator, *testCase.slice)

                aliveStates = []
                refCountSupported or gc.collect()
                # initial alive states
                aliveStates.append(iterator.weakReferencesState())
                while True:
                    try:
                        next(isliceIterator)
                        refCountSupported or gc.collect()
                        # intermediate alive states
                        aliveStates.append(iterator.weakReferencesState())
                    except StopIteration:
                        refCountSupported or gc.collect()
                        # final alive states
                        aliveStates.append(iterator.weakReferencesState())
                        break
                self.assertEqual(aliveStates, testCase.expectedAliveStates)


class ConsecutiveGroupsTest(TestCase):
    def testNumbers(self):
        iterable = [-10, -8, -7, -6, 1, 2, 4, 5, -1, 7]
        actual = [list(g) for g in mi.consecutiveGroups(iterable)]
        expected = [[-10], [-8, -7, -6], [1, 2], [4, 5], [-1], [7]]
        self.assertEqual(actual, expected)

    def testCustomOrdering(self):
        iterable = ['1', '10', '11', '20', '21', '22', '30', '31']
        ordering = lambda x: int(x)
        actual = [list(g) for g in mi.consecutiveGroups(iterable, ordering)]
        expected = [['1'], ['10', '11'], ['20', '21', '22'], ['30', '31']]
        self.assertEqual(actual, expected)

    def testExoticOrdering(self):
        iterable = [
            ('a', 'b', 'c', 'd'),
            ('a', 'c', 'b', 'd'),
            ('a', 'c', 'd', 'b'),
            ('a', 'd', 'b', 'c'),
            ('d', 'b', 'c', 'a'),
            ('d', 'c', 'a', 'b'),
        ]
        ordering = list(permutations('abcd')).index
        actual = [list(g) for g in mi.consecutiveGroups(iterable, ordering)]
        expected = [
            [('a', 'b', 'c', 'd')],
            [('a', 'c', 'b', 'd'), ('a', 'c', 'd', 'b'), ('a', 'd', 'b', 'c')],
            [('d', 'b', 'c', 'a'), ('d', 'c', 'a', 'b')],
        ]
        self.assertEqual(actual, expected)


class DifferenceTest(TestCase):
    def testNormal(self):
        iterable = [10, 20, 30, 40, 50]
        actual = list(mi.difference(iterable))
        expected = [10, 10, 10, 10, 10]
        self.assertEqual(actual, expected)

    def testCustom(self):
        iterable = [10, 20, 30, 40, 50]
        actual = list(mi.difference(iterable, add))
        expected = [10, 30, 50, 70, 90]
        self.assertEqual(actual, expected)

    def testRoundtrip(self):
        original = list(range(100))
        accumulated = accumulate(original)
        actual = list(mi.difference(accumulated))
        self.assertEqual(actual, original)

    def testOne(self):
        self.assertEqual(list(mi.difference([0])), [0])

    def testEmpty(self):
        self.assertEqual(list(mi.difference([])), [])

    def testInitial(self):
        original = list(range(100))
        accumulated = accumulate(original, initial=100)
        actual = list(mi.difference(accumulated, initial=100))
        self.assertEqual(actual, original)


class SeekableTest(PeekableMixinTests, TestCase):
    cls = mi.seekable

    def testExhaustionReset(self):
        iterable = [str(n) for n in range(10)]

        s = mi.seekable(iterable)
        self.assertEqual(list(s), iterable)  # Normal iteration
        self.assertEqual(list(s), [])  # Iterable is exhausted

        s.seek(0)
        self.assertEqual(list(s), iterable)  # Back in action

    def testPartialReset(self):
        iterable = [str(n) for n in range(10)]

        s = mi.seekable(iterable)
        self.assertEqual(mi.take(5, s), iterable[:5])  # Normal iteration

        s.seek(1)
        self.assertEqual(list(s), iterable[1:])  # Get the rest of the iterable

    def testForward(self):
        iterable = [str(n) for n in range(10)]

        s = mi.seekable(iterable)
        self.assertEqual(mi.take(1, s), iterable[:1])  # Normal iteration

        s.seek(3)  # Skip over index 2
        self.assertEqual(list(s), iterable[3:])  # Result is similar to slicing

        s.seek(0)  # Back to 0
        self.assertEqual(list(s), iterable)  # No difference in result

    def testPastEnd(self):
        iterable = [str(n) for n in range(10)]

        s = mi.seekable(iterable)
        self.assertEqual(mi.take(1, s), iterable[:1])  # Normal iteration

        s.seek(20)
        self.assertEqual(list(s), [])  # Iterable is exhausted

        s.seek(0)  # Back to 0
        self.assertEqual(list(s), iterable)  # No difference in result

    def testElements(self):
        iterable = map(str, count())

        s = mi.seekable(iterable)
        mi.take(10, s)

        elements = s.elements()
        self.assertEqual(
            [elements[i] for i in range(10)], [str(n) for n in range(10)]
        )
        self.assertEqual(len(elements), 10)

        mi.take(10, s)
        self.assertEqual(list(elements), [str(n) for n in range(20)])

    def testMaxlen(self):
        iterable = map(str, count())

        s = mi.seekable(iterable, maxlen=4)
        self.assertEqual(mi.take(10, s), [str(n) for n in range(10)])
        self.assertEqual(list(s.elements()), ['6', '7', '8', '9'])

        s.seek(0)
        self.assertEqual(mi.take(14, s), [str(n) for n in range(6, 20)])
        self.assertEqual(list(s.elements()), ['16', '17', '18', '19'])

    def testMaxlenZero(self):
        iterable = [str(x) for x in range(5)]
        s = mi.seekable(iterable, maxlen=0)
        self.assertEqual(list(s), iterable)
        self.assertEqual(list(s.elements()), [])

    def testRelativeSeek(self):
        iterable = [str(x) for x in range(5)]
        s = mi.seekable(iterable)
        s.relativeSeek(2)
        self.assertEqual(next(s), '2')
        s.relativeSeek(-2)
        self.assertEqual(next(s), '1')
        s.relativeSeek(-2)
        self.assertEqual(
            next(s), '0'
        )  # Seek relative to current position within the cache
        s.relativeSeek(-10)  # Lower bound
        self.assertEqual(next(s), '0')
        s.relativeSeek(10)  # Lower bound
        self.assertEqual(list(s.elements()), [str(x) for x in range(5)])


class SequenceViewTests(TestCase):
    def testInit(self):
        view = mi.SequenceView((1, 2, 3))
        self.assertEqual(repr(view), "SequenceView((1, 2, 3))")
        self.assertRaises(TypeError, lambda: mi.SequenceView({}))

    def testUpdate(self):
        seq = [1, 2, 3]
        view = mi.SequenceView(seq)
        self.assertEqual(len(view), 3)
        self.assertEqual(repr(view), "SequenceView([1, 2, 3])")

        seq.pop()
        self.assertEqual(len(view), 2)
        self.assertEqual(repr(view), "SequenceView([1, 2])")

    def testIndexing(self):
        seq = ('a', 'b', 'c', 'd', 'e', 'f')
        view = mi.SequenceView(seq)
        for i in range(-len(seq), len(seq)):
            self.assertEqual(view[i], seq[i])

    def testSlicing(self):
        seq = ('a', 'b', 'c', 'd', 'e', 'f')
        view = mi.SequenceView(seq)
        n = len(seq)
        indexes = list(range(-n - 1, n + 1)) + [None]
        steps = list(range(-n, n + 1))
        steps.remove(0)
        for sliceArgs in product(indexes, indexes, steps):
            i = slice(*sliceArgs)
            self.assertEqual(view[i], seq[i])

    def testAbcMethods(self):
        # collections.Sequence should provide all of this functionality
        seq = ('a', 'b', 'c', 'd', 'e', 'f', 'f')
        view = mi.SequenceView(seq)

        # __contains__
        self.assertIn('b', view)
        self.assertNotIn('g', view)

        # __iter__
        self.assertEqual(list(iter(view)), list(seq))

        # __reversed__
        self.assertEqual(list(reversed(view)), list(reversed(seq)))

        # index
        self.assertEqual(view.index('b'), 1)

        # count
        self.assertEqual(seq.count('f'), 2)


class RunLengthTest(TestCase):
    def testEncode(self):
        iterable = (int(str(n)[0]) for n in count(800))
        actual = mi.take(4, mi.runLength.encode(iterable))
        expected = [(8, 100), (9, 100), (1, 1000), (2, 1000)]
        self.assertEqual(actual, expected)

    def testDecode(self):
        iterable = [('d', 4), ('c', 3), ('b', 2), ('a', 1)]
        actual = ''.join(mi.runLength.decode(iterable))
        expected = 'ddddcccbba'
        self.assertEqual(actual, expected)


class ExactlyNTests(TestCase):
    """Tests for ``exactly_n()``"""

    def testTrue(self):
        """Iterable has ``n`` ``True`` elements"""
        self.assertTrue(mi.exactlyN([True, False, True], 2))
        self.assertTrue(mi.exactlyN([1, 1, 1, 0], 3))
        self.assertTrue(mi.exactlyN([False, False], 0))
        self.assertTrue(mi.exactlyN(range(100), 10, lambda x: x < 10))
        self.assertTrue(mi.exactlyN(repeat(True, 100), 100))
        self.assertTrue(mi.exactlyN(repeat(False, 100), 100, predicate=not_))

    def testFalse(self):
        """Iterable does not have ``n`` ``True`` elements"""
        self.assertFalse(mi.exactlyN([True, False, False], 2))
        self.assertFalse(mi.exactlyN([True, True, False], 1))
        self.assertFalse(mi.exactlyN([False], 1))
        self.assertFalse(mi.exactlyN([True], -1))
        self.assertFalse(mi.exactlyN([True], -10))
        self.assertFalse(mi.exactlyN([], -1))
        self.assertFalse(mi.exactlyN([], -10))
        self.assertFalse(mi.exactlyN([True], 0))
        self.assertFalse(mi.exactlyN(repeat(True), 100))

    def testEmpty(self):
        """Return ``True`` if the iterable is empty and ``n`` is 0"""
        self.assertTrue(mi.exactlyN([], 0))
        self.assertFalse(mi.exactlyN([], 1))


class AlwaysReversibleTests(TestCase):
    """Tests for ``always_reversible()``"""

    def testRegularReversed(self):
        self.assertEqual(
            list(reversed(range(10))), list(mi.alwaysReversible(range(10)))
        )
        self.assertEqual(
            list(reversed([1, 2, 3])), list(mi.alwaysReversible([1, 2, 3]))
        )
        self.assertEqual(
            reversed([1, 2, 3]).__class__,
            mi.alwaysReversible([1, 2, 3]).__class__,
        )

    def testNonseqReversed(self):
        # Create a non-reversible generator from a sequence
        with self.assertRaises(TypeError):
            reversed(x for x in range(10))

        self.assertEqual(
            list(reversed(range(10))),
            list(mi.alwaysReversible(x for x in range(10))),
        )
        self.assertEqual(
            list(reversed([1, 2, 3])),
            list(mi.alwaysReversible(x for x in [1, 2, 3])),
        )
        self.assertNotEqual(
            reversed((1, 2)).__class__,
            mi.alwaysReversible(x for x in (1, 2)).__class__,
        )


class CircularShiftsTests(TestCase):
    def testEmpty(self):
        # empty iterable -> empty list
        self.assertEqual(list(mi.circularShifts([])), [])

    def testSimpleCircularShifts(self):
        # test the a simple iterator case
        self.assertEqual(
            list(mi.circularShifts(range(4))),
            [(0, 1, 2, 3), (1, 2, 3, 0), (2, 3, 0, 1), (3, 0, 1, 2)],
        )

    def testDuplicates(self):
        # test non-distinct entries
        self.assertEqual(
            list(mi.circularShifts([0, 1, 0, 1])),
            [(0, 1, 0, 1), (1, 0, 1, 0), (0, 1, 0, 1), (1, 0, 1, 0)],
        )

    def testStepsPositive(self):
        actual = list(mi.circularShifts(range(5), steps=2))
        expected = [
            (0, 1, 2, 3, 4),
            (2, 3, 4, 0, 1),
            (4, 0, 1, 2, 3),
            (1, 2, 3, 4, 0),
            (3, 4, 0, 1, 2),
        ]
        self.assertEqual(actual, expected)

    def testStepsNegative(self):
        actual = list(mi.circularShifts(range(5), steps=-2))
        expected = [
            (0, 1, 2, 3, 4),
            (3, 4, 0, 1, 2),
            (1, 2, 3, 4, 0),
            (4, 0, 1, 2, 3),
            (2, 3, 4, 0, 1),
        ]
        self.assertEqual(actual, expected)

    def testStepsZero(self):
        with self.assertRaises(ValueError):
            list(mi.circularShifts(range(5), steps=0))


class MakeDecoratorTests(TestCase):
    def testBasic(self):
        slicer = mi.makeDecorator(islice)

        @slicer(1, 10, 2)
        def userFunction(arg1, arg2, kwarg1=None):
            self.assertEqual(arg1, 'arg_1')
            self.assertEqual(arg2, 'arg_2')
            self.assertEqual(kwarg1, 'kwarg_1')
            return map(str, count())

        it = userFunction('arg_1', 'arg_2', kwarg1='kwarg_1')
        actual = list(it)
        expected = ['1', '3', '5', '7', '9']
        self.assertEqual(actual, expected)

    def testResultIndex(self):
        def stringify(*args, **kwargs):
            self.assertEqual(args[0], 'arg_0')
            iterable = args[1]
            self.assertEqual(args[2], 'arg_2')
            self.assertEqual(kwargs['kwarg1'], 'kwarg_1')
            return map(str, iterable)

        stringifier = mi.makeDecorator(stringify, resultIndex=1)

        @stringifier('arg_0', 'arg_2', kwarg1='kwarg_1')
        def userFunction(n):
            return count(n)

        it = userFunction(1)
        actual = mi.take(5, it)
        expected = ['1', '2', '3', '4', '5']
        self.assertEqual(actual, expected)

    def testWrapClass(self):
        seeker = mi.makeDecorator(mi.seekable)

        @seeker()
        def userFunction(n):
            return map(str, range(n))

        it = userFunction(5)
        self.assertEqual(list(it), ['0', '1', '2', '3', '4'])

        it.seek(0)
        self.assertEqual(list(it), ['0', '1', '2', '3', '4'])


class MapReduceTests(TestCase):
    def testDefault(self):
        iterable = (str(x) for x in range(5))
        keyfunc = lambda x: int(x) // 2
        actual = sorted(mi.mapReduce(iterable, keyfunc).items())
        expected = [(0, ['0', '1']), (1, ['2', '3']), (2, ['4'])]
        self.assertEqual(actual, expected)

    def testValuefunc(self):
        iterable = (str(x) for x in range(5))
        keyfunc = lambda x: int(x) // 2
        valuefunc = int
        actual = sorted(mi.mapReduce(iterable, keyfunc, valuefunc).items())
        expected = [(0, [0, 1]), (1, [2, 3]), (2, [4])]
        self.assertEqual(actual, expected)

    def testReducefunc(self):
        iterable = (str(x) for x in range(5))
        keyfunc = lambda x: int(x) // 2
        valuefunc = int
        reducefunc = lambda valueList: reduce(mul, valueList, 1)
        actual = sorted(
            mi.mapReduce(iterable, keyfunc, valuefunc, reducefunc).items()
        )
        expected = [(0, 0), (1, 6), (2, 4)]
        self.assertEqual(actual, expected)

    def testRet(self):
        d = mi.mapReduce([1, 0, 2, 0, 1, 0], bool)
        self.assertEqual(d, {False: [0, 0, 0], True: [1, 2, 1]})
        self.assertRaises(KeyError, lambda: d[None].append(1))


class RlocateTests(TestCase):
    def testDefaultPred(self):
        iterable = [0, 1, 1, 0, 1, 0, 0]
        for it in (iterable[:], iter(iterable)):
            actual = list(mi.rlocate(it))
            expected = [4, 2, 1]
            self.assertEqual(actual, expected)

    def testNoMatches(self):
        iterable = [0, 0, 0]
        for it in (iterable[:], iter(iterable)):
            actual = list(mi.rlocate(it))
            expected = []
            self.assertEqual(actual, expected)

    def testCustomPred(self):
        iterable = ['0', 1, 1, '0', 1, '0', '0']
        pred = lambda x: x == '0'
        for it in (iterable[:], iter(iterable)):
            actual = list(mi.rlocate(it, pred))
            expected = [6, 5, 3, 0]
            self.assertEqual(actual, expected)

    def testEfficientReversal(self):
        iterable = range(9**9)  # Is efficiently reversible
        target = 9**9 - 2
        pred = lambda x: x == target  # Find-able from the right
        actual = next(mi.rlocate(iterable, pred))
        self.assertEqual(actual, target)

    def testWindowSize(self):
        iterable = ['0', 1, 1, '0', 1, '0', '0']
        pred = lambda *args: args == ('0', 1)
        for it in (iterable, iter(iterable)):
            actual = list(mi.rlocate(it, pred, windowSize=2))
            expected = [3, 0]
            self.assertEqual(actual, expected)

    def testWindowSizeLarge(self):
        iterable = [1, 2, 3, 4]
        pred = lambda a, b, c, d, e: True
        for it in (iterable, iter(iterable)):
            actual = list(mi.rlocate(iterable, pred, windowSize=5))
            expected = [0]
            self.assertEqual(actual, expected)

    def testWindowSizeZero(self):
        iterable = [1, 2, 3, 4]
        pred = lambda: True
        for it in (iterable, iter(iterable)):
            with self.assertRaises(ValueError):
                list(mi.locate(iterable, pred, windowSize=0))


class ReplaceTests(TestCase):
    def testBasic(self):
        iterable = range(10)
        pred = lambda x: x % 2 == 0
        substitutes = []
        actual = list(mi.replace(iterable, pred, substitutes))
        expected = [1, 3, 5, 7, 9]
        self.assertEqual(actual, expected)

    def testCount(self):
        iterable = range(10)
        pred = lambda x: x % 2 == 0
        substitutes = []
        actual = list(mi.replace(iterable, pred, substitutes, count=4))
        expected = [1, 3, 5, 7, 8, 9]
        self.assertEqual(actual, expected)

    def testWindowSize(self):
        iterable = range(10)
        pred = lambda *args: args == (0, 1, 2)
        substitutes = []
        actual = list(mi.replace(iterable, pred, substitutes, windowSize=3))
        expected = [3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(actual, expected)

    def testWindowSizeEnd(self):
        iterable = range(10)
        pred = lambda *args: args == (7, 8, 9)
        substitutes = []
        actual = list(mi.replace(iterable, pred, substitutes, windowSize=3))
        expected = [0, 1, 2, 3, 4, 5, 6]
        self.assertEqual(actual, expected)

    def testWindowSizeCount(self):
        iterable = range(10)
        pred = lambda *args: (args == (0, 1, 2)) or (args == (7, 8, 9))
        substitutes = []
        actual = list(
            mi.replace(iterable, pred, substitutes, count=1, windowSize=3)
        )
        expected = [3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(actual, expected)

    def testWindowSizeLarge(self):
        iterable = range(4)
        pred = lambda a, b, c, d, e: True
        substitutes = [5, 6, 7]
        actual = list(mi.replace(iterable, pred, substitutes, windowSize=5))
        expected = [5, 6, 7]
        self.assertEqual(actual, expected)

    def testWindowSizeZero(self):
        iterable = range(10)
        pred = lambda *args: True
        substitutes = []
        with self.assertRaises(ValueError):
            list(mi.replace(iterable, pred, substitutes, windowSize=0))

    def testIterableSubstitutes(self):
        iterable = range(5)
        pred = lambda x: x % 2 == 0
        substitutes = iter('__')
        actual = list(mi.replace(iterable, pred, substitutes))
        expected = ['_', '_', 1, '_', '_', 3, '_', '_']
        self.assertEqual(actual, expected)


class PartitionsTest(TestCase):
    def testTypes(self):
        for iterable in ['abcd', ['a', 'b', 'c', 'd'], ('a', 'b', 'c', 'd')]:
            with self.subTest(iterable=iterable):
                actual = list(mi.partitions(iterable))
                expected = [
                    [['a', 'b', 'c', 'd']],
                    [['a'], ['b', 'c', 'd']],
                    [['a', 'b'], ['c', 'd']],
                    [['a', 'b', 'c'], ['d']],
                    [['a'], ['b'], ['c', 'd']],
                    [['a'], ['b', 'c'], ['d']],
                    [['a', 'b'], ['c'], ['d']],
                    [['a'], ['b'], ['c'], ['d']],
                ]
                self.assertEqual(actual, expected)

    def testEmpty(self):
        iterable = []
        actual = list(mi.partitions(iterable))
        expected = [[[]]]
        self.assertEqual(actual, expected)

    def testOrder(self):
        iterable = iter([3, 2, 1])
        actual = list(mi.partitions(iterable))
        expected = [[[3, 2, 1]], [[3], [2, 1]], [[3, 2], [1]], [[3], [2], [1]]]
        self.assertEqual(actual, expected)

    def testDuplicates(self):
        iterable = [1, 1, 1]
        actual = list(mi.partitions(iterable))
        expected = [[[1, 1, 1]], [[1], [1, 1]], [[1, 1], [1]], [[1], [1], [1]]]
        self.assertEqual(actual, expected)


class _frozenmultiset(Set):
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

    def hasDuplicates(self):
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
    def _normalizePartition(p):
        """
        Return a normalized, hashable, version of a partition using
        _FrozenMultiset
        """
        return _frozenmultiset(_frozenmultiset(g) for g in p)

    @staticmethod
    def _normalizePartitions(ps):
        """
        Return a normalized set of all normalized partitions using
        _FrozenMultiset
        """
        return _frozenmultiset(
            SetPartitionsTests._normalizePartition(p) for p in ps
        )

    def testRepeated(self):
        it = 'aaa'
        actual = mi.setPartitions(it, 2)
        expected = [['a', 'aa'], ['a', 'aa'], ['a', 'aa']]
        self.assertEqual(
            self._normalizePartitions(expected),
            self._normalizePartitions(actual),
        )

    def testEachCorrect(self):
        a = set(range(6))
        for p in mi.setPartitions(a):
            total = {e for g in p for e in g}
            self.assertEqual(a, total)

    def testDuplicates(self):
        a = set(range(6))
        for p in mi.setPartitions(a):
            self.assertFalse(self._normalizePartition(p).hasDuplicates())

    def testFoundAll(self):
        """small example, hand-checked"""
        expected = [
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
        actual = mi.setPartitions(range(5), 3)
        self.assertEqual(
            self._normalizePartitions(expected),
            self._normalizePartitions(actual),
        )

    def testStirlingNumbers(self):
        """Check against https://en.wikipedia.org/wiki/
        Stirling_numbers_of_the_second_kind#Table_of_values"""
        cardinalityByKByN = [
            [1],
            [1, 1],
            [1, 3, 1],
            [1, 7, 6, 1],
            [1, 15, 25, 10, 1],
            [1, 31, 90, 65, 15, 1],
        ]
        for n, cardinalityByK in enumerate(cardinalityByKByN, 1):
            for k, cardinality in enumerate(cardinalityByK, 1):
                self.assertEqual(
                    cardinality, len(list(mi.setPartitions(range(n), k)))
                )

    def testNoGroup(self):
        def helper():
            list(mi.setPartitions(range(4), -1))

        self.assertRaises(ValueError, helper)

    def testToManyGroups(self):
        self.assertEqual([], list(mi.setPartitions(range(4), 5)))

    def testMinSize(self):
        it = 'abc'
        actual = mi.setPartitions(it, minSize=2)
        expected = [['abc']]
        self.assertEqual(
            self._normalizePartitions(expected),
            self._normalizePartitions(actual),
        )

    def testMaxSize(self):
        it = 'abc'
        actual = mi.setPartitions(it, maxSize=2)
        expected = [['a', 'bc'], ['ab', 'c'], ['b', 'ac'], ['a', 'b', 'c']]
        self.assertEqual(
            self._normalizePartitions(expected),
            self._normalizePartitions(actual),
        )

    def testMinMax(self):
        it = 'abcdefg'
        self.assertEqual(
            list(mi.setPartitions(it, minSize=4, maxSize=3)), []
        )


class TimeLimitedTests(TestCase):
    def testBasic(self):
        def generator():
            yield 1
            yield 2
            sleep(0.2)
            yield 3

        iterable = mi.timeLimited(0.1, generator())
        actual = list(iterable)
        expected = [1, 2]
        self.assertEqual(actual, expected)
        self.assertTrue(iterable.timedOut)

    def testComplete(self):
        iterable = mi.timeLimited(2, iter(range(10)))
        actual = list(iterable)
        expected = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(actual, expected)
        self.assertFalse(iterable.timedOut)

    def testZeroLimit(self):
        iterable = mi.timeLimited(0, count())
        actual = list(iterable)
        expected = []
        self.assertEqual(actual, expected)
        self.assertTrue(iterable.timedOut)

    def testInvalidLimit(self):
        with self.assertRaises(ValueError):
            list(mi.timeLimited(-0.1, count()))


class OnlyTests(TestCase):
    def testDefaults(self):
        self.assertEqual(mi.only([]), None)
        self.assertEqual(mi.only([1]), 1)
        self.assertRaises(ValueError, lambda: mi.only([1, 2]))

    def testCustomValue(self):
        self.assertEqual(mi.only([], default='!'), '!')
        self.assertEqual(mi.only([1], default='!'), 1)
        self.assertRaises(ValueError, lambda: mi.only([1, 2], default='!'))

    def testCustomException(self):
        self.assertEqual(mi.only([], tooLong=RuntimeError), None)
        self.assertEqual(mi.only([1], tooLong=RuntimeError), 1)
        self.assertRaises(
            RuntimeError, lambda: mi.only([1, 2], tooLong=RuntimeError)
        )

    def testDefaultExceptionMessage(self):
        self.assertRaisesRegex(
            ValueError,
            "Expected exactly one item in iterable, "
            "but got 'foo', 'bar', and perhaps more",
            lambda: mi.only(['foo', 'bar', 'baz']),
        )


class IchunkedTests(TestCase):
    def testEven(self):
        iterable = (str(x) for x in range(10))
        actual = [''.join(c) for c in mi.ichunked(iterable, 5)]
        expected = ['01234', '56789']
        self.assertEqual(actual, expected)

    def testOdd(self):
        iterable = (str(x) for x in range(10))
        actual = [''.join(c) for c in mi.ichunked(iterable, 4)]
        expected = ['0123', '4567', '89']
        self.assertEqual(actual, expected)

    def testZero(self):
        iterable = []
        actual = [list(c) for c in mi.ichunked(iterable, 0)]
        expected = []
        self.assertEqual(actual, expected)

    def testNegative(self):
        iterable = count()
        with self.assertRaises(ValueError):
            [list(c) for c in mi.ichunked(iterable, -1)]

    def testOutOfOrder(self):
        iterable = map(str, count())
        it = mi.ichunked(iterable, 4)
        chunk1 = next(it)
        chunk2 = next(it)
        self.assertEqual(''.join(chunk2), '4567')
        self.assertEqual(''.join(chunk1), '0123')

    def testLaziness(self):
        def gen():
            yield 0
            raise RuntimeError
            yield from count(1)

        it = mi.ichunked(gen(), 4)
        chunk = next(it)
        self.assertEqual(next(chunk), 0)
        self.assertRaises(RuntimeError, next, it)

    def testMemoryInOrder(self):
        genNumbers = []

        def gen():
            for genNumber in count():
                genNumbers.append(genNumber)
                yield genNumber

        # No items should be kept in memory when a ichunked is first called
        allChunks = mi.ichunked(gen(), 4)
        self.assertEqual(genNumbers, [])

        # The first item of each chunk should be generated on chunk generation
        firstChunk = next(allChunks)
        self.assertEqual(genNumbers, [0])

        # If we don't read a chunk before getting its successor, its contents
        # will be cached
        secondChunk = next(allChunks)
        self.assertEqual(genNumbers, [0, 1, 2, 3, 4])

        # Check if we can read in cached values
        self.assertEqual(list(firstChunk), [0, 1, 2, 3])
        self.assertEqual(list(secondChunk), [4, 5, 6, 7])

        # Again only the most recent chunk should have an item cached
        thirdChunk = next(allChunks)
        self.assertEqual(len(genNumbers), 9)

        # No new item should be cached when reading past the first number
        next(thirdChunk)
        self.assertEqual(len(genNumbers), 9)

        # we should not be able to read spent chunks
        self.assertEqual(list(firstChunk), [])
        self.assertEqual(list(secondChunk), [])


class DistinctCombinationsTests(TestCase):
    def testBasic(self):
        for iterable in [
            (1, 2, 2, 3, 3, 3),  # In order
            range(6),  # All distinct
            'abbccc',  # Not numbers
            'cccbba',  # Backward
            'mississippi',  # No particular order
        ]:
            for r in range(len(iterable)):
                with self.subTest(iterable=iterable, r=r):
                    actual = list(mi.distinctCombinations(iterable, r))
                    expected = list(
                        mi.uniqueEverseen(combinations(iterable, r))
                    )
                    self.assertEqual(actual, expected)

    def testNegative(self):
        with self.assertRaises(ValueError):
            list(mi.distinctCombinations([], -1))

    def testEmpty(self):
        self.assertEqual(list(mi.distinctCombinations([], 2)), [])


class FilterExceptTests(TestCase):
    def testNoExceptionsPass(self):
        iterable = '0123'
        actual = list(mi.filterExcept(int, iterable))
        expected = ['0', '1', '2', '3']
        self.assertEqual(actual, expected)

    def testNoExceptionsRaise(self):
        iterable = ['0', '1', 'two', '3']
        with self.assertRaises(ValueError):
            list(mi.filterExcept(int, iterable))

    def testRaise(self):
        iterable = ['0', '12', 'three', None]
        with self.assertRaises(TypeError):
            list(mi.filterExcept(int, iterable, ValueError))

    def testFalse(self):
        # Even if the validator returns false, we pass through
        validator = lambda x: False
        iterable = ['0', '1', '2', 'three', None]
        actual = list(mi.filterExcept(validator, iterable, Exception))
        expected = ['0', '1', '2', 'three', None]
        self.assertEqual(actual, expected)

    def testMultiple(self):
        iterable = ['0', '1', '2', 'three', None, '4']
        actual = list(mi.filterExcept(int, iterable, ValueError, TypeError))
        expected = ['0', '1', '2', '4']
        self.assertEqual(actual, expected)


class MapExceptTests(TestCase):
    def testNoExceptionsPass(self):
        iterable = '0123'
        actual = list(mi.mapExcept(int, iterable))
        expected = [0, 1, 2, 3]
        self.assertEqual(actual, expected)

    def testNoExceptionsRaise(self):
        iterable = ['0', '1', 'two', '3']
        with self.assertRaises(ValueError):
            list(mi.mapExcept(int, iterable))

    def testRaise(self):
        iterable = ['0', '12', 'three', None]
        with self.assertRaises(TypeError):
            list(mi.mapExcept(int, iterable, ValueError))

    def testMultiple(self):
        iterable = ['0', '1', '2', 'three', None, '4']
        actual = list(mi.mapExcept(int, iterable, ValueError, TypeError))
        expected = [0, 1, 2, 4]
        self.assertEqual(actual, expected)


class MapIfTests(TestCase):
    def testWithoutFuncElse(self):
        iterable = list(range(-5, 5))
        actual = list(mi.mapIf(iterable, lambda x: x > 3, lambda x: 'toobig'))
        expected = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 'toobig']
        self.assertEqual(actual, expected)

    def testWithFuncElse(self):
        iterable = list(range(-5, 5))
        actual = list(
            mi.mapIf(
                iterable, lambda x: x >= 0, lambda x: 'notneg', lambda x: 'neg'
            )
        )
        expected = ['neg'] * 5 + ['notneg'] * 5
        self.assertEqual(actual, expected)

    def testEmpty(self):
        actual = list(mi.mapIf([], lambda x: len(x) > 5, lambda x: None))
        expected = []
        self.assertEqual(actual, expected)


class SampleTests(TestCase):
    def testSpecificSample(self):
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

    def testUnitCase(self):
        """Test against a fixed case by seeding the random module."""
        # Beware that this test really just verifies random.random() behavior.
        # If the algorithm is changed (e.g. to a more naive implementation)
        # this test will fail, but the algorithm might be correct.
        # Also, this test can pass and the algorithm can be completely wrong.
        data = "abcdef"
        weights = list(range(1, len(data) + 1))
        seed(123)
        actual = mi.sample(data, k=2, weights=weights)
        expected = ['f', 'e']
        self.assertEqual(actual, expected)

    def testNegative(self):
        data = [1, 2, 3, 4, 5]
        with self.assertRaises(ValueError):
            mi.sample(data, k=-1)

    def testLength(self):
        """Check that *k* elements are sampled."""
        data = [1, 2, 3, 4, 5]
        for k in [0, 3, 5, 7]:
            sampled = mi.sample(data, k=k)
            actual = len(sampled)
            expected = min(k, len(data))
            self.assertEqual(actual, expected)

    def testStrict(self):
        data = ['1', '2', '3', '4', '5']
        self.assertEqual(set(mi.sample(data, 6, strict=False)), set(data))
        with self.assertRaises(ValueError):
            mi.sample(data, 6, strict=True)

    def testCounts(self):
        # Test with counts
        seed(0)
        iterable = ['red', 'blue']
        counts = [4, 2]
        k = 5
        actual = list(mi.sample(iterable, counts=counts, k=k))

        # Test without counts
        seed(0)
        decodedIterable = (['red'] * 4) + (['blue'] * 2)
        expected = list(mi.sample(decodedIterable, k=k))

        self.assertEqual(actual, expected)

    def testCountsAll(self):
        actual = Counter(mi.sample('uwxyz', 35, counts=(1, 0, 4, 10, 20)))
        expected = Counter({'u': 1, 'x': 4, 'y': 10, 'z': 20})
        self.assertEqual(actual, expected)

    def testSamplingEntireIterable(self):
        """If k=len(iterable), the sample contains the original elements."""
        data = ["a", 2, "a", 4, (1, 2, 3)]
        actual = set(mi.sample(data, k=len(data)))
        expected = set(data)
        self.assertEqual(actual, expected)

    def testScaleInvarianceOfWeights(self):
        """The probability of choosing element a_i is w_i / sum(weights).
        Scaling weights should not change the probability or outcome."""
        data = "abcdef"

        weights = list(range(1, len(data) + 1))
        seed(123)
        firstSample = mi.sample(data, k=2, weights=weights)

        # Scale the weights and sample again
        weightsScaled = [w / 1e10 for w in weights]
        seed(123)
        secondSample = mi.sample(data, k=2, weights=weightsScaled)

        self.assertEqual(firstSample, secondSample)

    def testInvarianceUnderPermutationsUnweighted(self):
        """The order of the data should not matter. This is a stochastic test,
        but it will fail in less than 1 / 10_000 cases."""

        # Create a data set and a reversed data set
        data = list(range(100))
        dataRev = list(reversed(data))

        # Sample each data set 10 times
        dataMeans = [mean(mi.sample(data, k=50)) for _ in range(10)]
        dataRevMeans = [mean(mi.sample(dataRev, k=50)) for _ in range(10)]

        # The difference in the means should be low, i.e. little bias
        differenceInMeans = abs(mean(dataMeans) - mean(dataRevMeans))

        # The observed largest difference in 10,000 simulations was 5.09599
        self.assertTrue(differenceInMeans < 5.1)

    def testInvarianceUnderPermutationsWeighted(self):
        """The order of the data should not matter. This is a stochastic test,
        but it will fail in less than 1 / 10_000 cases."""

        # Create a data set and a reversed data set
        data = list(range(1, 101))
        dataRev = list(reversed(data))

        # Sample each data set 10 times
        dataMeans = [
            mean(mi.sample(data, k=50, weights=data)) for _ in range(10)
        ]
        dataRevMeans = [
            mean(mi.sample(dataRev, k=50, weights=dataRev))
            for _ in range(10)
        ]

        # The difference in the means should be low, i.e. little bias
        differenceInMeans = abs(mean(dataMeans) - mean(dataRevMeans))

        # The observed largest difference in 10,000 simulations was 4.337999
        self.assertTrue(differenceInMeans < 4.4)

    def testErrorCases(self):
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
    def testBasic(self):
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
            key = kwargs.get('key', None)
            reverse = kwargs.get('reverse', False)
            strict = kwargs.get('strict', False)

            with self.subTest(
                iterable=iterable, key=key, reverse=reverse, strict=strict
            ):
                miResult = mi.isSorted(
                    map(BarelySortable, iterable),
                    key=key,
                    reverse=reverse,
                    strict=strict,
                )

                sortedIterable = sorted(iterable, key=key, reverse=reverse)
                if strict:
                    sortedIterable = list(mi.uniqueJustseen(sortedIterable))

                pyResult = iterable == sortedIterable

                self.assertEqual(miResult, expected)
                self.assertEqual(miResult, pyResult)


class CallbackIterTests(TestCase):
    def _target(self, cb=None, exc=None, wait=0):
        total = 0
        for i, c in enumerate('abc', 1):
            total += i
            if wait:
                sleep(wait)
            if cb:
                cb(i, c, intermediateTotal=total)
            if exc:
                raise exc('error in target')

        return total

    def testBasic(self):
        func = lambda callback=None: self._target(cb=callback, wait=0.02)
        with mi.callbackIter(func, waitSeconds=0.01) as it:
            # Execution doesn't start until we begin iterating
            self.assertFalse(it.done)

            # Consume everything
            self.assertEqual(
                list(it),
                [
                    ((1, 'a'), {'intermediateTotal': 1}),
                    ((2, 'b'), {'intermediateTotal': 3}),
                    ((3, 'c'), {'intermediateTotal': 6}),
                ],
            )

            # After consuming everything the future is done and the
            # result is available.
            self.assertTrue(it.done)
            self.assertEqual(it.result, 6)

        # This examines the internal state of the ThreadPoolExecutor. This
        # isn't documented, so may break in future Python versions.
        self.assertTrue(it._executor._shutdown)

    def testCallbackKwd(self):
        with mi.callbackIter(self._target, callbackKwd='cb') as it:
            self.assertEqual(
                list(it),
                [
                    ((1, 'a'), {'intermediateTotal': 1}),
                    ((2, 'b'), {'intermediateTotal': 3}),
                    ((3, 'c'), {'intermediateTotal': 6}),
                ],
            )

    def testPartialConsumption(self):
        func = lambda callback=None: self._target(cb=callback)
        with mi.callbackIter(func) as it:
            self.assertEqual(next(it), ((1, 'a'), {'intermediateTotal': 1}))

        self.assertTrue(it._executor._shutdown)

    def testAbort(self):
        func = lambda callback=None: self._target(cb=callback, wait=0.1)
        with mi.callbackIter(func) as it:
            self.assertEqual(next(it), ((1, 'a'), {'intermediateTotal': 1}))

        with self.assertRaises(mi.AbortThread):
            it.result

    def testNoResult(self):
        func = lambda callback=None: self._target(cb=callback)
        with mi.callbackIter(func) as it:
            with self.assertRaises(RuntimeError):
                it.result

    def testException(self):
        func = lambda callback=None: self._target(cb=callback, exc=ValueError)
        with mi.callbackIter(func) as it:
            self.assertEqual(
                next(it),
                ((1, 'a'), {'intermediateTotal': 1}),
            )

            with self.assertRaises(ValueError):
                it.result


class WindowedCompleteTests(TestCase):
    """Tests for ``windowed_complete()``"""

    def testBasic(self):
        actual = list(mi.windowedComplete([1, 2, 3, 4, 5], 3))
        expected = [
            ((), (1, 2, 3), (4, 5)),
            ((1,), (2, 3, 4), (5,)),
            ((1, 2), (3, 4, 5), ()),
        ]
        self.assertEqual(actual, expected)

    def testZeroLength(self):
        actual = list(mi.windowedComplete([1, 2, 3], 0))
        expected = [
            ((), (), (1, 2, 3)),
            ((1,), (), (2, 3)),
            ((1, 2), (), (3,)),
            ((1, 2, 3), (), ()),
        ]
        self.assertEqual(actual, expected)

    def testWrongLength(self):
        seq = [1, 2, 3, 4, 5]
        for n in (-10, -1, len(seq) + 1, len(seq) + 10):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    list(mi.windowedComplete(seq, n))

    def testEveryPartition(self):
        everyPartition = lambda seq: chain(
            *map(partial(mi.windowedComplete, seq), range(len(seq)))
        )

        seq = 'ABC'
        actual = list(everyPartition(seq))
        expected = [
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
        self.assertEqual(actual, expected)


class AllUniqueTests(TestCase):
    def testBasic(self):
        for iterable, expected in [
            ([], True),
            ([1, 2, 3], True),
            ([1, 1], False),
            ([1, 2, 3, 1], False),
            ([1, 2, 3, '1'], True),
        ]:
            with self.subTest(args=(iterable,)):
                self.assertEqual(mi.allUnique(iterable), expected)

    def testNonHashable(self):
        self.assertEqual(mi.allUnique([[1, 2], [3, 4]]), True)
        self.assertEqual(mi.allUnique([[1, 2], [3, 4], [1, 2]]), False)

    def testPartiallyHashable(self):
        self.assertEqual(mi.allUnique([[1, 2], [3, 4], (5, 6)]), True)
        self.assertEqual(
            mi.allUnique([[1, 2], [3, 4], (5, 6), [1, 2]]), False
        )
        self.assertEqual(
            mi.allUnique([[1, 2], [3, 4], (5, 6), (5, 6)]), False
        )

    def testKey(self):
        iterable = ['A', 'B', 'C', 'b']
        self.assertEqual(mi.allUnique(iterable, lambda x: x), True)
        self.assertEqual(mi.allUnique(iterable, str.lower), False)

    def testInfinite(self):
        self.assertEqual(mi.allUnique(mi.prepend(3, count())), False)


class NthProductTests(TestCase):
    def testBasic(self):
        iterables = ['ab', 'cdef', 'ghi']
        for index, expected in enumerate(product(*iterables)):
            actual = mi.nthProduct(index, *iterables)
            self.assertEqual(actual, expected)

    def testLong(self):
        actual = mi.nthProduct(1337, range(101), range(22), range(53))
        expected = (1, 3, 12)
        self.assertEqual(actual, expected)

    def testNegative(self):
        iterables = ['abc', 'de', 'fghi']
        for index, expected in enumerate(product(*iterables)):
            actual = mi.nthProduct(index - 24, *iterables)
            self.assertEqual(actual, expected)

    def testInvalidIndex(self):
        with self.assertRaises(IndexError):
            mi.nthProduct(24, 'ab', 'cde', 'fghi')

    def testRepeat(self):
        self.assertEqual(
            mi.nthProduct(1234, 'abcde', repeat=5),
            mi.nthProduct(1234, 'abcde', 'abcde', 'abcde', 'abcde', 'abcde'),
        )
        self.assertEqual(
            mi.nthProduct(123, 'AB', 'CD', 'EFG', repeat=2),
            mi.nthProduct(123, 'AB', 'CD', 'EFG', 'AB', 'CD', 'EFG'),
        )
        self.assertEqual(
            mi.nthProduct(123, iter('AB'), iter('CD'), iter('EFG'), repeat=2),
            mi.nthProduct(123, 'AB', 'CD', 'EFG', 'AB', 'CD', 'EFG'),
        )


class NthCombinationWithReplacementTests(TestCase):
    def testBasic(self):
        iterable = 'abcdefg'
        r = 4
        for index, expected in enumerate(
            combinations_with_replacement(iterable, r)
        ):
            actual = mi.nthCombinationWithReplacement(iterable, r, index)
            self.assertEqual(actual, expected)
        self.assertEqual(
            mi.nthCombinationWithReplacement('abcde', 7, 320),
            ('c', 'd', 'e', 'e', 'e', 'e', 'e'),
        )

    def testLong(self):
        actual = mi.nthCombinationWithReplacement(range(90), 4, 2000000)
        expected = (22, 65, 68, 81)
        self.assertEqual(actual, expected)

    def testInvalidR(self):
        with self.assertRaises(ValueError):
            mi.nthCombinationWithReplacement([], -1, 0)

    def testInvalidIndex(self):
        with self.assertRaises(IndexError):
            mi.nthCombinationWithReplacement('abcdefg', 3, -85)
        with self.assertRaises(IndexError):
            mi.nthCombinationWithReplacement('abcde', 7, 400)


class ValueChainTests(TestCase):
    def testEmpty(self):
        actual = list(mi.valueChain())
        expected = []
        self.assertEqual(actual, expected)

    def testSimple(self):
        actual = list(mi.valueChain(1, 2.71828, False, 'foo'))
        expected = [1, 2.71828, False, 'foo']
        self.assertEqual(actual, expected)

    def testMore(self):
        actual = list(mi.valueChain(b'bar', [1, 2, 3], 4, {'key': 1}))
        expected = [b'bar', 1, 2, 3, 4, 'key']
        self.assertEqual(actual, expected)

    def testEmptyLists(self):
        actual = list(mi.valueChain(1, 2, [], [3, 4]))
        expected = [1, 2, 3, 4]
        self.assertEqual(actual, expected)

    def testComplex(self):
        obj = object()
        actual = list(
            mi.valueChain(
                (1, (2, (3,))),
                ['foo', ['bar', ['baz']], 'tic'],
                {'key': {'foo': 1}},
                obj,
            )
        )
        expected = [1, (2, (3,)), 'foo', ['bar', ['baz']], 'tic', 'key', obj]
        self.assertEqual(actual, expected)


class ProductIndexTests(TestCase):
    def testBasic(self):
        iterables = ['ab', 'cdef', 'ghi']
        firstIndex = {}
        for index, element in enumerate(product(*iterables)):
            actual = mi.productIndex(element, *iterables)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testMultiplicity(self):
        iterables = ['ab', 'bab', 'cab']
        firstIndex = {}
        for index, element in enumerate(product(*iterables)):
            actual = mi.productIndex(element, *iterables)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testLong(self):
        actual = mi.productIndex((1, 3, 12), range(101), range(22), range(53))
        expected = 1337
        self.assertEqual(actual, expected)

    def testInvalidEmpty(self):
        with self.assertRaises(ValueError):
            mi.productIndex('', 'ab', 'cde', 'fghi')

    def testInvalidSmall(self):
        with self.assertRaises(ValueError):
            mi.productIndex('ac', 'ab', 'cde', 'fghi')

    def testInvalidLarge(self):
        with self.assertRaises(ValueError):
            mi.productIndex('achi', 'ab', 'cde', 'fghi')

    def testInvalidMatch(self):
        with self.assertRaises(ValueError):
            mi.productIndex('axf', 'ab', 'cde', 'fghi')

    def testIteratorInput(self):
        self.assertEqual(
            mi.productIndex(iter(['i', 'a']), iter('snicker'), iter('snack')),
            12,
        )

    def testRepeat(self):
        self.assertEqual(
            mi.productIndex([1, 2, 3, 4], range(10), repeat=4),
            mi.productIndex(
                [1, 2, 3, 4], range(10), range(10), range(10), range(10)
            ),
        )
        target = ['B', 'D', 'E', 'A', 'C', 'G']
        self.assertEqual(
            mi.productIndex(target, 'AB', 'CD', 'EFG', repeat=2),
            mi.productIndex(target, 'AB', 'CD', 'EFG', 'AB', 'CD', 'EFG'),
        )
        self.assertEqual(
            mi.productIndex(
                iter(target), iter('AB'), iter('CD'), iter('EFG'), repeat=2
            ),
            mi.productIndex(target, 'AB', 'CD', 'EFG', 'AB', 'CD', 'EFG'),
        )


class CombinationIndexTests(TestCase):
    def testRLessThanN(self):
        iterable = 'abcdefg'
        r = 4
        firstIndex = {}
        for index, element in enumerate(combinations(iterable, r)):
            actual = mi.combinationIndex(element, iterable)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testREqualToN(self):
        iterable = 'abcd'
        r = len(iterable)
        firstIndex = {}
        for index, element in enumerate(combinations(iterable, r=r)):
            actual = mi.combinationIndex(element, iterable)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testMultiplicity(self):
        iterable = 'abacba'
        r = 3
        firstIndex = {}
        for index, element in enumerate(combinations(iterable, r)):
            actual = mi.combinationIndex(element, iterable)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testNull(self):
        actual = mi.combinationIndex(tuple(), [])
        expected = 0
        self.assertEqual(actual, expected)

    def testLong(self):
        actual = mi.combinationIndex((2, 12, 35, 126), range(180))
        expected = 2000000
        self.assertEqual(actual, expected)

    def testInvalidOrder(self):
        with self.assertRaises(ValueError):
            mi.combinationIndex(tuple('acb'), 'abcde')

    def testInvalidLarge(self):
        with self.assertRaises(ValueError):
            mi.combinationIndex(tuple('abcdefg'), 'abcdef')

    def testInvalidMatch(self):
        with self.assertRaises(ValueError):
            mi.combinationIndex(tuple('axe'), 'abcde')


class CombinationWithReplacementIndexTests(TestCase):
    def testRLessThanN(self):
        iterable = 'abcdefg'
        r = 4
        firstIndex = {}
        for index, element in enumerate(
            combinations_with_replacement(iterable, r)
        ):
            actual = mi.combinationWithReplacementIndex(element, iterable)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testREqualToN(self):
        iterable = 'abcd'
        r = len(iterable)
        firstIndex = {}
        for index, element in enumerate(
            combinations_with_replacement(iterable, r=r)
        ):
            actual = mi.combinationWithReplacementIndex(element, iterable)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testMultiplicity(self):
        iterable = 'abacba'
        r = 3
        firstIndex = {}
        for index, element in enumerate(
            combinations_with_replacement(iterable, r)
        ):
            actual = mi.combinationWithReplacementIndex(element, iterable)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testNull(self):
        actual = mi.combinationWithReplacementIndex(tuple(), [])
        expected = 0
        self.assertEqual(actual, expected)

    def testLong(self):
        actual = mi.combinationWithReplacementIndex(
            (22, 65, 68, 81), range(90)
        )
        expected = 2000000
        self.assertEqual(actual, expected)

    def testInvalidOrder(self):
        with self.assertRaises(ValueError):
            mi.combinationWithReplacementIndex(tuple('acb'), 'abcde')

    def testInvalidLarge(self):
        with self.assertRaises(ValueError):
            mi.combinationWithReplacementIndex(tuple('abcdefg'), 'abcdef')

    def testInvalidMatch(self):
        with self.assertRaises(ValueError):
            mi.combinationWithReplacementIndex(tuple('axe'), 'abcde')


class PermutationIndexTests(TestCase):
    def testRLessThanN(self):
        iterable = 'abcdefg'
        r = 4
        firstIndex = {}
        for index, element in enumerate(permutations(iterable, r)):
            actual = mi.permutationIndex(element, iterable)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testREqualToN(self):
        iterable = 'abcd'
        firstIndex = {}
        for index, element in enumerate(permutations(iterable)):
            actual = mi.permutationIndex(element, iterable)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testMultiplicity(self):
        iterable = 'abacba'
        r = 3
        firstIndex = {}
        for index, element in enumerate(permutations(iterable, r)):
            actual = mi.permutationIndex(element, iterable)
            expected = firstIndex.setdefault(element, index)
            self.assertEqual(actual, expected)

    def testNull(self):
        actual = mi.permutationIndex(tuple(), [])
        expected = 0
        self.assertEqual(actual, expected)

    def testLong(self):
        actual = mi.permutationIndex((2, 12, 35, 126), range(180))
        expected = 11631678
        self.assertEqual(actual, expected)

    def testInvalidLarge(self):
        with self.assertRaises(ValueError):
            mi.permutationIndex(tuple('abcdefg'), 'abcdef')

    def testInvalidMatch(self):
        with self.assertRaises(ValueError):
            mi.permutationIndex(tuple('axe'), 'abcde')


class CountableTests(TestCase):
    def testEmpty(self):
        iterable = []
        it = mi.countable(iterable)
        self.assertEqual(it.itemsSeen, 0)
        self.assertEqual(list(it), [])

    def testBasic(self):
        iterable = '0123456789'
        it = mi.countable(iterable)
        self.assertEqual(it.itemsSeen, 0)
        self.assertEqual(next(it), '0')
        self.assertEqual(it.itemsSeen, 1)
        self.assertEqual(''.join(it), '123456789')
        self.assertEqual(it.itemsSeen, 10)


class ChunkedEvenTests(TestCase):
    """Tests for ``chunked_even()``"""

    def test0(self):
        self._testFinite('', 3, [])

    def test1(self):
        self._testFinite('A', 1, [['A']])

    def test4(self):
        self._testFinite('ABCD', 3, [['A', 'B'], ['C', 'D']])

    def test5(self):
        self._testFinite('ABCDE', 3, [['A', 'B', 'C'], ['D', 'E']])

    def test6(self):
        self._testFinite('ABCDEF', 3, [['A', 'B', 'C'], ['D', 'E', 'F']])

    def test7(self):
        self._testFinite(
            'ABCDEFG', 3, [['A', 'B', 'C'], ['D', 'E'], ['F', 'G']]
        )

    def _testFinite(self, seq, n, expected):
        # Check with and without `len()`
        self.assertEqual(list(mi.chunkedEven(seq, n)), expected)
        self.assertEqual(list(mi.chunkedEven(iter(seq), n)), expected)

    def testInfinite(self):
        for n in range(1, 5):
            k = 0

            def countWithAssert():
                for i in count():
                    # Look-ahead should be less than n^2
                    self.assertLessEqual(i, n * k + n * n)
                    yield i

            ls = mi.chunkedEven(countWithAssert(), n)
            while k < 2:
                self.assertEqual(next(ls), list(range(k * n, (k + 1) * n)))
                k += 1

    def testEvenness(self):
        for N in range(1, 50):
            for n in range(1, N + 2):
                lengths = []
                items = []
                for l in mi.chunkedEven(range(N), n):
                    L = len(l)
                    self.assertLessEqual(L, n)
                    self.assertGreaterEqual(L, 1)
                    lengths.append(L)
                    items.extend(l)
                self.assertEqual(items, list(range(N)))
                self.assertLessEqual(max(lengths) - min(lengths), 1)


class ZipBroadcastTests(TestCase):
    def testZip(self):
        for objects, zipped, strictOk in [
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
                self.assertEqual(list(mi.zipBroadcast(*objects)), zipped)

            # Raise an exception for strict=True
            with self.subTest(objects=objects, strict=True, zipped=zipped):
                if strictOk:
                    self.assertEqual(
                        list(mi.zipBroadcast(*objects, strict=True)),
                        zipped,
                    )
                else:
                    with self.assertRaises(ValueError):
                        list(mi.zipBroadcast(*objects, strict=True))

    def testScalarTypes(self):
        # Default: str and bytes are treated as scalar
        self.assertEqual(
            list(mi.zipBroadcast('ab', [1, 2, 3])),
            [('ab', 1), ('ab', 2), ('ab', 3)],
        )
        self.assertEqual(
            list(mi.zipBroadcast(b'ab', [1, 2, 3])),
            [(b'ab', 1), (b'ab', 2), (b'ab', 3)],
        )
        # scalar_types=None allows str and bytes to be treated as iterable
        self.assertEqual(
            list(mi.zipBroadcast('abc', [1, 2, 3], scalarTypes=None)),
            [('a', 1), ('b', 2), ('c', 3)],
        )
        # Use a custom type
        self.assertEqual(
            list(mi.zipBroadcast({'a': 'b'}, [1, 2, 3], scalarTypes=dict)),
            [({'a': 'b'}, 1), ({'a': 'b'}, 2), ({'a': 'b'}, 3)],
        )


class UniqueInWindowTests(TestCase):
    def testInvalidN(self):
        with self.assertRaises(ValueError):
            list(mi.uniqueInWindow([], 0))

    def testBasic(self):
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
                actual = list(mi.uniqueInWindow(iterable, n))
                self.assertEqual(actual, expected)

    def testKey(self):
        iterable = [0, 1, 3, 4, 5, 6, 7, 8, 9]
        n = 3
        key = lambda x: x // 3
        actual = list(mi.uniqueInWindow(iterable, n, key=key))
        expected = [0, 3, 6, 9]
        self.assertEqual(actual, expected)


class StrictlyNTests(TestCase):
    def testBasic(self):
        iterable = ['a', 'b', 'c', 'd']
        n = 4
        actual = list(mi.strictlyN(iter(iterable), n))
        expected = iterable
        self.assertEqual(actual, expected)

    def testTooShortDefault(self):
        iterable = ['a', 'b', 'c', 'd']
        n = 5
        with self.assertRaises(ValueError) as exc:
            list(mi.strictlyN(iter(iterable), n))

        self.assertEqual(
            'Too few items in iterable (got 4)', exc.exception.args[0]
        )

    def testTooLongDefault(self):
        iterable = ['a', 'b', 'c', 'd']
        n = 3
        with self.assertRaises(ValueError) as cm:
            list(mi.strictlyN(iter(iterable), n))

        self.assertEqual(
            'Too many items in iterable (got at least 4)',
            cm.exception.args[0],
        )

    def testTooShortCustom(self):
        callCount = 0

        def tooShort(itemCount):
            nonlocal callCount
            callCount += 1

        iterable = ['a', 'b', 'c', 'd']
        n = 6
        actual = []
        for item in mi.strictlyN(iter(iterable), n, tooShort=tooShort):
            actual.append(item)
        expected = ['a', 'b', 'c', 'd']
        self.assertEqual(actual, expected)
        self.assertEqual(callCount, 1)

    def testTooLongCustom(self):
        import logging

        iterable = ['a', 'b', 'c', 'd']
        n = 2
        tooLong = lambda itemCount: logging.warning(
            'Picked the first %s items', n
        )

        with self.assertLogs(level='WARNING') as cm:
            actual = list(mi.strictlyN(iter(iterable), n, tooLong=tooLong))

        self.assertEqual(actual, ['a', 'b'])
        self.assertIn('Picked the first 2 items', cm.output[0])


class DuplicatesEverSeenTests(TestCase):
    def testBasic(self):
        for iterable, expected in [
            ([], []),
            ([1, 2, 3], []),
            ([1, 1], [1]),
            ([1, 2, 1, 2], [1, 2]),
            ([1, 2, 3, '1'], []),
        ]:
            with self.subTest(args=(iterable,)):
                self.assertEqual(
                    list(mi.duplicatesEverseen(iterable)), expected
                )

    def testNonHashable(self):
        self.assertEqual(list(mi.duplicatesEverseen([[1, 2], [3, 4]])), [])
        self.assertEqual(
            list(mi.duplicatesEverseen([[1, 2], [3, 4], [1, 2]])), [[1, 2]]
        )

    def testPartiallyHashable(self):
        self.assertEqual(
            list(mi.duplicatesEverseen([[1, 2], [3, 4], (5, 6)])), []
        )
        self.assertEqual(
            list(mi.duplicatesEverseen([[1, 2], [3, 4], (5, 6), [1, 2]])),
            [[1, 2]],
        )
        self.assertEqual(
            list(mi.duplicatesEverseen([[1, 2], [3, 4], (5, 6), (5, 6)])),
            [(5, 6)],
        )

    def testKeyHashable(self):
        iterable = 'HEheHEhe'
        self.assertEqual(list(mi.duplicatesEverseen(iterable)), list('HEhe'))
        self.assertEqual(
            list(mi.duplicatesEverseen(iterable, str.lower)),
            list('heHEhe'),
        )

    def testKeyNonHashable(self):
        iterable = [[1, 2], [3, 0], [5, -2], [5, 6]]
        self.assertEqual(
            list(mi.duplicatesEverseen(iterable, lambda x: x)), []
        )
        self.assertEqual(
            list(mi.duplicatesEverseen(iterable, sum)), [[3, 0], [5, -2]]
        )

    def testKeyPartiallyHashable(self):
        iterable = [[1, 2], (1, 2), [1, 2], [5, 6]]
        self.assertEqual(
            list(mi.duplicatesEverseen(iterable, lambda x: x)), [[1, 2]]
        )
        self.assertEqual(
            list(mi.duplicatesEverseen(iterable, list)), [(1, 2), [1, 2]]
        )


class DuplicatesJustSeenTests(TestCase):
    def testBasic(self):
        for iterable, expected in [
            ([], []),
            ([1, 2, 3, 3, 2, 2], [3, 2]),
            ([1, 1], [1]),
            ([1, 2, 1, 2], []),
            ([1, 2, 3, '1'], []),
        ]:
            with self.subTest(args=(iterable,)):
                self.assertEqual(
                    list(mi.duplicatesJustseen(iterable)), expected
                )

    def testNonHashable(self):
        self.assertEqual(list(mi.duplicatesJustseen([[1, 2], [3, 4]])), [])
        self.assertEqual(
            list(
                mi.duplicatesJustseen(
                    [[1, 2], [3, 4], [3, 4], [3, 4], [1, 2]]
                )
            ),
            [[3, 4], [3, 4]],
        )

    def testPartiallyHashable(self):
        self.assertEqual(
            list(mi.duplicatesJustseen([[1, 2], [3, 4], (5, 6)])), []
        )
        self.assertEqual(
            list(
                mi.duplicatesJustseen(
                    [[1, 2], [3, 4], (5, 6), [1, 2], [1, 2]]
                )
            ),
            [[1, 2]],
        )
        self.assertEqual(
            list(
                mi.duplicatesJustseen(
                    [[1, 2], [3, 4], (5, 6), (5, 6), (5, 6)]
                )
            ),
            [(5, 6), (5, 6)],
        )

    def testKeyHashable(self):
        iterable = 'HEheHHHhEheeEe'
        self.assertEqual(list(mi.duplicatesJustseen(iterable)), list('HHe'))
        self.assertEqual(
            list(mi.duplicatesJustseen(iterable, str.lower)),
            list('HHheEe'),
        )

    def testKeyNonHashable(self):
        iterable = [[1, 2], [3, 0], [5, -2], [5, 6], [1, 2]]
        self.assertEqual(
            list(mi.duplicatesJustseen(iterable, lambda x: x)), []
        )
        self.assertEqual(
            list(mi.duplicatesJustseen(iterable, sum)), [[3, 0], [5, -2]]
        )

    def testKeyPartiallyHashable(self):
        iterable = [[1, 2], (1, 2), [1, 2], [5, 6], [1, 2]]
        self.assertEqual(
            list(mi.duplicatesJustseen(iterable, lambda x: x)), []
        )
        self.assertEqual(
            list(mi.duplicatesJustseen(iterable, list)), [(1, 2), [1, 2]]
        )

    def testNested(self):
        iterable = [[[1, 2], [1, 2]], [5, 6], [5, 6]]
        self.assertEqual(list(mi.duplicatesJustseen(iterable)), [[5, 6]])


class ClassifyUniqueTests(TestCase):
    def testBasic(self):
        self.assertEqual(
            list(mi.classifyUnique('mississippi')),
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

    def testNonHashable(self):
        self.assertEqual(
            list(mi.classifyUnique([[1, 2], [3, 4], [3, 4], [1, 2]])),
            [
                ([1, 2], True, True),
                ([3, 4], True, True),
                ([3, 4], False, False),
                ([1, 2], True, False),
            ],
        )

    def testPartiallyHashable(self):
        self.assertEqual(
            list(
                mi.classifyUnique(
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

    def testKeyHashable(self):
        iterable = 'HEheHHHhEheeEe'
        self.assertEqual(
            list(mi.classifyUnique(iterable)),
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
            list(mi.classifyUnique(iterable, str.lower)),
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

    def testKeyNonHashable(self):
        iterable = [[1, 2], [3, 0], [5, -2], [5, 6], [1, 2]]
        self.assertEqual(
            list(mi.classifyUnique(iterable, lambda x: x)),
            [
                ([1, 2], True, True),
                ([3, 0], True, True),
                ([5, -2], True, True),
                ([5, 6], True, True),
                ([1, 2], True, False),
            ],
        )
        self.assertEqual(
            list(mi.classifyUnique(iterable, sum)),
            [
                ([1, 2], True, True),
                ([3, 0], False, False),
                ([5, -2], False, False),
                ([5, 6], True, True),
                ([1, 2], True, False),
            ],
        )

    def testKeyPartiallyHashable(self):
        iterable = [[1, 2], (1, 2), [1, 2], [5, 6], [1, 2]]
        self.assertEqual(
            list(mi.classifyUnique(iterable, lambda x: x)),
            [
                ([1, 2], True, True),
                ((1, 2), True, True),
                ([1, 2], True, False),
                ([5, 6], True, True),
                ([1, 2], True, False),
            ],
        )
        self.assertEqual(
            list(mi.classifyUnique(iterable, list)),
            [
                ([1, 2], True, True),
                ((1, 2), False, False),
                ([1, 2], False, False),
                ([5, 6], True, True),
                ([1, 2], True, False),
            ],
        )

    def testVsUniqueEverseen(self):
        input = 'AAAABBBBCCDAABBB'
        output = [e for e, j, u in mi.classifyUnique(input) if u]
        self.assertEqual(output, ['A', 'B', 'C', 'D'])
        self.assertEqual(list(mi.uniqueEverseen(input)), output)

    def testVsUniqueEverseenKey(self):
        input = 'aAbACCc'
        output = [e for e, j, u in mi.classifyUnique(input, str.lower) if u]
        self.assertEqual(output, list('abC'))
        self.assertEqual(list(mi.uniqueEverseen(input, str.lower)), output)

    def testVsUniqueJustseen(self):
        input = 'AAAABBBCCDABB'
        output = [e for e, j, u in mi.classifyUnique(input) if j]
        self.assertEqual(output, list('ABCDAB'))
        self.assertEqual(list(mi.uniqueJustseen(input)), output)

    def testVsUniqueJustseenKey(self):
        input = 'AABCcAD'
        output = [e for e, j, u in mi.classifyUnique(input, str.lower) if j]
        self.assertEqual(output, list('ABCAD'))
        self.assertEqual(list(mi.uniqueJustseen(input, str.lower)), output)

    def testVsDuplicatesEverseen(self):
        input = [1, 2, 1, 2]
        output = [e for e, j, u in mi.classifyUnique(input) if not u]
        self.assertEqual(output, [1, 2])
        self.assertEqual(list(mi.duplicatesEverseen(input)), output)

    def testVsDuplicatesEverseenKey(self):
        input = 'HEheHEhe'
        output = [
            e for e, j, u in mi.classifyUnique(input, str.lower) if not u
        ]
        self.assertEqual(output, list('heHEhe'))
        self.assertEqual(
            list(mi.duplicatesEverseen(input, str.lower)), output
        )

    def testVsDuplicatesJustseen(self):
        input = [1, 2, 3, 3, 2, 2]
        output = [e for e, j, u in mi.classifyUnique(input) if not j]
        self.assertEqual(output, [3, 2])
        self.assertEqual(list(mi.duplicatesJustseen(input)), output)

    def testVsDuplicatesJustseenKey(self):
        input = 'HEheHHHhEheeEe'
        output = [
            e for e, j, u in mi.classifyUnique(input, str.lower) if not j
        ]
        self.assertEqual(output, list('HHheEe'))
        self.assertEqual(
            list(mi.duplicatesJustseen(input, str.lower)), output
        )


class LongestCommonPrefixTests(TestCase):
    def testBasic(self):
        iterables = [[1, 2], [1, 2, 3], [1, 2, 4]]
        self.assertEqual(list(mi.longestCommonPrefix(iterables)), [1, 2])

    def testIterators(self):
        iterables = iter([iter([1, 2]), iter([1, 2, 3]), iter([1, 2, 4])])
        self.assertEqual(list(mi.longestCommonPrefix(iterables)), [1, 2])

    def testNoIterables(self):
        iterables = []
        self.assertEqual(list(mi.longestCommonPrefix(iterables)), [])

    def testEmptyIterablesOnly(self):
        iterables = [[], [], []]
        self.assertEqual(list(mi.longestCommonPrefix(iterables)), [])

    def testIncludesEmptyIterables(self):
        iterables = [[1, 2], [1, 2, 3], [1, 2, 4], []]
        self.assertEqual(list(mi.longestCommonPrefix(iterables)), [])

    def testNonHashable(self):
        # See https://github.com/more-itertools/more-itertools/issues/603
        iterables = [[[1], [2]], [[1], [2], [3]], [[1], [2], [4]]]
        self.assertEqual(list(mi.longestCommonPrefix(iterables)), [[1], [2]])

    def testPrefixContainsElementsOfTheFirstIterable(self):
        iterables = [[[1], [2]], [[1], [2], [3]], [[1], [2], [4]]]
        prefix = list(mi.longestCommonPrefix(iterables))
        self.assertIs(prefix[0], iterables[0][0])
        self.assertIs(prefix[1], iterables[0][1])
        self.assertIsNot(prefix[0], iterables[1][0])
        self.assertIsNot(prefix[1], iterables[1][1])
        self.assertIsNot(prefix[0], iterables[2][0])
        self.assertIsNot(prefix[1], iterables[2][1])

    def testInfiniteIterables(self):
        prefix = mi.longestCommonPrefix([count(), count()])
        self.assertEqual(next(prefix), 0)
        self.assertEqual(next(prefix), 1)
        self.assertEqual(next(prefix), 2)

    def testContainsInfiniteIterables(self):
        iterables = [[0, 1, 2], count()]
        self.assertEqual(list(mi.longestCommonPrefix(iterables)), [0, 1, 2])


class IequalsTests(TestCase):
    def testBasic(self):
        self.assertTrue(mi.iequals("abc", iter("abc")))
        self.assertTrue(mi.iequals(range(3), [0, 1, 2]))
        self.assertFalse(mi.iequals("abc", [0, 1, 2]))

    def testNoIterables(self):
        self.assertTrue(mi.iequals())

    def testOneIterable(self):
        self.assertTrue(mi.iequals("abc"))

    def testMoreThanTwoIterable(self):
        self.assertTrue(mi.iequals("abc", iter("abc"), ['a', 'b', 'c']))
        self.assertFalse(mi.iequals("abc", iter("abc"), ['a', 'b', 'd']))

    def testOrderMatters(self):
        self.assertFalse(mi.iequals("abc", "acb"))

    def testNotEqualLengths(self):
        self.assertFalse(mi.iequals("abc", "ab"))
        self.assertFalse(mi.iequals("abc", "bc"))
        self.assertFalse(mi.iequals("aaa", "aaaa"))

    def testEmptyIterables(self):
        self.assertTrue(mi.iequals([], ""))

    def testNoneIsNotASentinel(self):
        # See https://stackoverflow.com/a/900444
        self.assertFalse(mi.iequals([1, 2], [1, 2, None]))
        self.assertFalse(mi.iequals([1, 2], [None, 1, 2]))

    def testNotIdenticalButEqual(self):
        self.assertTrue([1, True], [1.0, complex(1, 0)])

    def testFillvalueNotFakeable(self):
        # See https://github.com/more-itertools/more-itertools/issues/900
        self.assertFalse(mi.iequals([], [mock.ANY]))


class ConstrainedBatchesTests(TestCase):
    def testBasic(self):
        zen = [
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
                    (zen[0],),
                    (zen[1],),
                    (zen[2],),
                    (zen[3],),
                    (zen[4],),
                    (zen[5],),
                    (zen[6],),
                ],
            ),
            (
                61,
                [
                    (zen[0], zen[1]),
                    (zen[2],),
                    (zen[3], zen[4]),
                    (zen[5], zen[6]),
                ],
            ),
            (
                90,
                [
                    (zen[0], zen[1], zen[2]),
                    (zen[3], zen[4], zen[5]),
                    (zen[6],),
                ],
            ),
            (
                124,
                [(zen[0], zen[1], zen[2], zen[3]), (zen[4], zen[5], zen[6])],
            ),
            (
                150,
                [(zen[0], zen[1], zen[2], zen[3], zen[4]), (zen[5], zen[6])],
            ),
            (
                177,
                [(zen[0], zen[1], zen[2], zen[3], zen[4], zen[5]), (zen[6],)],
            ),
        ):
            with self.subTest(size=size):
                actual = list(mi.constrainedBatches(iter(zen), size))
                self.assertEqual(actual, expected)

    def testMaxCount(self):
        iterable = ['1', '1', '12345678', '12345', '12345']
        maxSize = 10
        maxCount = 2
        actual = list(mi.constrainedBatches(iterable, maxSize, maxCount))
        expected = [('1', '1'), ('12345678',), ('12345', '12345')]
        self.assertEqual(actual, expected)

    def testStrict(self):
        iterable = ['1', '123456789', '1']
        size = 8
        with self.assertRaises(ValueError):
            list(mi.constrainedBatches(iterable, size))

        actual = list(mi.constrainedBatches(iterable, size, strict=False))
        expected = [('1',), ('123456789',), ('1',)]
        self.assertEqual(actual, expected)

    def testGetLen(self):
        class Record(tuple):
            def totalSize(self):
                return sum(len(x) for x in self)

        record3 = Record(('1', '23'))
        record5 = Record(('1234', '1'))
        record10 = Record(('1', '12345678', '1'))
        record2 = Record(('1', '1'))
        iterable = [record3, record5, record10, record2]

        self.assertEqual(
            list(
                mi.constrainedBatches(
                    iterable, 10, getLen=lambda x: x.totalSize()
                )
            ),
            [(record3, record5), (record10,), (record2,)],
        )

    def testBadMax(self):
        with self.assertRaises(ValueError):
            list(mi.constrainedBatches([], 0))


class GrayProductTests(TestCase):
    def testBasic(self):
        self.assertEqual(
            tuple(mi.grayProduct(('a', 'b', 'c'), range(1, 3))),
            (("a", 1), ("b", 1), ("c", 1), ("c", 2), ("b", 2), ("a", 2)),
        )
        out = mi.grayProduct(('foo', 'bar'), (3, 4, 5, 6), ['quz', 'baz'])
        self.assertEqual(next(out), ('foo', 3, 'quz'))
        self.assertEqual(
            list(out),
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
        self.assertEqual(tuple(mi.grayProduct()), ((),))
        self.assertEqual(tuple(mi.grayProduct((1, 2))), ((1,), (2,)))

    def testErrors(self):
        with self.assertRaises(ValueError):
            list(mi.grayProduct((1, 2), ()))
        with self.assertRaises(ValueError):
            list(mi.grayProduct((1, 2), (2,)))

    def testVsProduct(self):
        iters = (
            ("a", "b"),
            range(3, 6),
            [None, None],
            {"i", "j", "k", "l"},
            "XYZ",
        )
        self.assertEqual(
            sorted(product(*iters)), sorted(mi.grayProduct(*iters))
        )

    def testRepeat(self):
        self.assertEqual(
            list(mi.grayProduct('ABC', repeat=5)),
            list(mi.grayProduct('ABC', 'ABC', 'ABC', 'ABC', 'ABC')),
        )
        self.assertEqual(
            list(mi.grayProduct('ABC', 'DE', repeat=5)),
            list(
                mi.grayProduct(
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
    def testNoIterables(self):
        self.assertEqual(tuple(mi.partialProduct()), ((),))

    def testEmptyIterable(self):
        self.assertEqual(tuple(mi.partialProduct('AB', '', 'CD')), ())

    def testOneIterable(self):
        # a single iterable should pass through
        self.assertEqual(
            tuple(mi.partialProduct('ABCD')),
            (
                ('A',),
                ('B',),
                ('C',),
                ('D',),
            ),
        )

    def testTwoIterables(self):
        self.assertEqual(
            list(mi.partialProduct('ABCD', [1])),
            [('A', 1), ('B', 1), ('C', 1), ('D', 1)],
        )
        expected = [
            ('A', 1),
            ('B', 1),
            ('C', 1),
            ('D', 1),
            ('D', 2),
            ('D', 3),
            ('D', 4),
        ]
        self.assertEqual(
            list(mi.partialProduct('ABCD', [1, 2, 3, 4])), expected
        )

    def testBasic(self):
        ones = [1, 2, 3]
        tens = [10, 20, 30, 40, 50]
        hundreds = [100, 200]

        expected = [
            (1, 10, 100),
            (2, 10, 100),
            (3, 10, 100),
            (3, 20, 100),
            (3, 30, 100),
            (3, 40, 100),
            (3, 50, 100),
            (3, 50, 200),
        ]

        actual = list(mi.partialProduct(ones, tens, hundreds))
        self.assertEqual(actual, expected)

    def testUnevenLengthIterables(self):
        # this is also the docstring example
        expected = [
            ('A', 'C', 'D'),
            ('B', 'C', 'D'),
            ('B', 'C', 'E'),
            ('B', 'C', 'F'),
        ]

        self.assertEqual(list(mi.partialProduct('AB', 'C', 'DEF')), expected)

    def testRepeat(self):
        self.assertEqual(
            list(mi.partialProduct('ABC', repeat=5)),
            list(mi.partialProduct('ABC', 'ABC', 'ABC', 'ABC', 'ABC')),
        )
        self.assertEqual(
            list(mi.partialProduct('ABC', 'DE', repeat=5)),
            list(
                mi.partialProduct(
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
    def testBasic(self) -> None:
        result = list(islice(mi.iterate(lambda x: 2 * x, start=1), 10))
        expected = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
        self.assertEqual(result, expected)

    def testFuncControlsIterationStop(self) -> None:
        def func(num):
            if num > 100:
                raise StopIteration
            return num * 2

        result = list(islice(mi.iterate(func, start=1), 10))
        expected = [1, 2, 4, 8, 16, 32, 64, 128]
        self.assertEqual(result, expected)


class TakewhileInclusiveTests(TestCase):
    def testBasic(self) -> None:
        result = list(mi.takewhileInclusive(lambda x: x < 5, [1, 4, 6, 4, 1]))
        expected = [1, 4, 6]
        self.assertEqual(result, expected)

    def testEmptyIterator(self) -> None:
        result = list(mi.takewhileInclusive(lambda x: True, []))
        expected = []
        self.assertEqual(result, expected)

    def testCollatzSequence(self) -> None:
        isEven = lambda n: n % 2 == 0
        start = 11
        result = list(
            mi.takewhileInclusive(
                lambda n: n != 1,
                mi.iterate(
                    lambda n: n // 2 if isEven(n) else 3 * n + 1, start
                ),
            )
        )
        expected = [11, 34, 17, 52, 26, 13, 40, 20, 10, 5, 16, 8, 4, 2, 1]
        self.assertEqual(result, expected)


class OuterProductTests(TestCase):
    def testBasic(self) -> None:
        greetings = ['Hello', 'Goodbye']
        names = ['Alice', 'Bob', 'Carol']
        greet = lambda greeting, name: f'{greeting}, {name}!'
        result = list(mi.outerProduct(greet, greetings, names))
        expected = [
            ('Hello, Alice!', 'Hello, Bob!', 'Hello, Carol!'),
            ('Goodbye, Alice!', 'Goodbye, Bob!', 'Goodbye, Carol!'),
        ]
        self.assertEqual(result, expected)


class IterSuppressTests(TestCase):
    class Producer:
        def __init__(self, exc, dieEarly=False):
            self.exc = exc
            self.pos = 0
            self.dieEarly = dieEarly

        def __iter__(self):
            if self.dieEarly:
                raise self.exc

            return self

        def __next__(self):
            ret = self.pos
            if self.pos >= 5:
                raise self.exc
            self.pos += 1
            return ret

    def testNoError(self):
        iterator = range(5)
        actual = list(mi.iterSuppress(iterator, RuntimeError))
        expected = [0, 1, 2, 3, 4]
        self.assertEqual(actual, expected)

    def testRaisesError(self):
        iterator = self.Producer(ValueError)
        with self.assertRaises(ValueError):
            list(mi.iterSuppress(iterator, RuntimeError))

    def testSuppression(self):
        iterator = self.Producer(ValueError)
        actual = list(mi.iterSuppress(iterator, RuntimeError, ValueError))
        expected = [0, 1, 2, 3, 4]
        self.assertEqual(actual, expected)

    def testEarlySuppression(self):
        iterator = self.Producer(ValueError, dieEarly=True)
        actual = list(mi.iterSuppress(iterator, RuntimeError, ValueError))
        expected = []
        self.assertEqual(actual, expected)


class FilterMapTests(TestCase):
    def testNoIterables(self):
        actual = list(mi.filterMap(lambda _: None, []))
        expected = []
        self.assertEqual(actual, expected)

    def testFilter(self):
        actual = list(mi.filterMap(lambda _: None, [1, 2, 3]))
        expected = []
        self.assertEqual(actual, expected)

    def testMap(self):
        actual = list(mi.filterMap(lambda x: x + 1, [1, 2, 3]))
        expected = [2, 3, 4]
        self.assertEqual(actual, expected)

    def testFilterMap(self):
        actual = list(
            mi.filterMap(
                lambda x: int(x) if x.isnumeric() else None,
                ['1', 'a', '2', 'b', '3'],
            )
        )
        expected = [1, 2, 3]
        self.assertEqual(actual, expected)


class PowersetOfSetsTests(TestCase):
    def testSimple(self):
        iterable = [0, 1, 2]
        actual = list(mi.powersetOfSets(iterable))
        expected = [set(), {0}, {1}, {2}, {0, 1}, {0, 2}, {1, 2}, {0, 1, 2}]
        self.assertEqual(actual, expected)

    def testHashCount(self):
        hashCount = 0

        class Str(str):
            def __hash__(trueSelf):
                nonlocal hashCount
                hashCount += 1
                return super.__hash__(trueSelf)

        iterable = map(Str, 'ABBBCDD')
        self.assertEqual(len(list(mi.powersetOfSets(iterable))), 128)
        self.assertLessEqual(hashCount, 14)

    def testBaseset(self):
        iterable = [0, 1, 2]
        for kind in (set, frozenset):
            ps = list(mi.powersetOfSets(iterable, baseset=kind))
            self.assertEqual(set(map(type, ps)), {kind})

        # Verify that an actual set can be formed.
        ps = set(mi.powersetOfSets('abc', baseset=frozenset))
        self.assertIn({'a', 'b'}, ps)


class JoinMappingTests(TestCase):
    def testBasic(self):
        salaryMap = {'e1': 12, 'e2': 23, 'e3': 34}
        deptMap = {'e1': 'eng', 'e2': 'sales', 'e3': 'eng'}
        serviceMap = {'e1': 5, 'e2': 9, 'e3': 2}
        fieldToMap = {
            'salary': salaryMap,
            'dept': deptMap,
            'service': serviceMap,
        }
        expected = {
            'e1': {'salary': 12, 'dept': 'eng', 'service': 5},
            'e2': {'salary': 23, 'dept': 'sales', 'service': 9},
            'e3': {'salary': 34, 'dept': 'eng', 'service': 2},
        }
        self.assertEqual(dict(mi.joinMappings(**fieldToMap)), expected)

    def testEmpty(self):
        self.assertEqual(dict(mi.joinMappings()), {})


class DiscreteFourierTransformTests(TestCase):
    def testBasic(self):
        # Example calculation from:
        # https://en.wikipedia.org/wiki/Discrete_Fourier_transform#Example
        xarr = [1, 2 - 1j, -1j, -1 + 2j]
        Xarr = [2, -2 - 2j, -2j, 4 + 4j]
        self.assertTrue(all(map(cmath.isclose, mi.dft(xarr), Xarr)))
        self.assertTrue(all(map(cmath.isclose, mi.idft(Xarr), xarr)))

    def testRoundtrip(self):
        for _ in range(1_000):
            N = randrange(35)
            xarr = [complex(random(), random()) for i in range(N)]
            Xarr = list(mi.dft(xarr))
            assert all(map(cmath.isclose, mi.idft(Xarr), xarr))


class DoubleStarMapTests(TestCase):
    def testConstruction(self):
        iterable = [{'price': 1.23}, {'price': 42}, {'price': 0.1}]
        actual = list(mi.doublestarmap('{price:.2f}'.format, iterable))
        expected = ['1.23', '42.00', '0.10']
        self.assertEqual(actual, expected)

    def testIdentity(self):
        iterable = [{'x': 1}, {'x': 2}, {'x': 3}]
        actual = list(mi.doublestarmap(lambda x: x, iterable))
        expected = [1, 2, 3]
        self.assertEqual(actual, expected)

    def testAdding(self):
        iterable = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
        actual = list(mi.doublestarmap(lambda a, b: a + b, iterable))
        expected = [3, 7]
        self.assertEqual(actual, expected)

    def testMismatchFunctionSmaller(self):
        iterable = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
        with self.assertRaises(TypeError):
            list(mi.doublestarmap(lambda a: a, iterable))

    def testMismatchFunctionDifferent(self):
        iterable = [{'a': 1}, {'a': 2}]
        with self.assertRaises(TypeError):
            list(mi.doublestarmap(lambda x: x, iterable))

    def testMismatchFunctionLarger(self):
        iterable = [{'a': 1}, {'a': 2}]
        with self.assertRaises(TypeError):
            list(mi.doublestarmap(lambda a, b: a + b, iterable))

    def testNoMapping(self):
        iterable = [1, 2, 3, 4]
        with self.assertRaises(TypeError):
            list(mi.doublestarmap(lambda x: x, iterable))

    def testEmpty(self):
        actual = list(mi.doublestarmap(lambda x: x, []))
        expected = []
        self.assertEqual(actual, expected)


class ArgMinArgMaxTests(TestCase):
    def testBasic(self):
        for i, iterable, expectedMin, expectedMax in (
            (1, [10, 2, 20, 5, 17, 4], 1, 2),
            (2, [10, -2, -20, 5, 17, 4], 2, 4),
            (3, [10, 10, 20, 10], 0, 2),
            (4, [30, 30, 20, 30], 2, 0),
        ):
            with self.subTest(i=i):
                self.assertEqual(mi.argmin(iterable), expectedMin)
                self.assertEqual(mi.argmax(iterable), expectedMax)

    def testKey(self):
        for i, iterable, key, expectedMin, expectedMax in (
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
                self.assertEqual(mi.argmin(iterable, key=key), expectedMin)
                self.assertEqual(mi.argmax(iterable, key=key), expectedMax)


class ExtractTests(TestCase):
    def testBasics(self):
        extract = mi.extract
        data = 'abcdefghijklmnopqrstuvwxyz'

        # Test iterator inputs, increasing and decreasing indices, and repeats.
        self.assertEqual(
            list(extract(iter(data), iter([7, 4, 11, 11, 14]))),
            ['h', 'e', 'l', 'l', 'o'],
        )

        # Empty indices
        self.assertEqual(list(extract(iter(data), iter([]))), [])

        # Result is an iterator
        iterator = extract('abc', [0, 1, 2])
        self.assertTrue(hasattr(iterator, '__next__'))

        # Error cases

        with self.assertRaises(TypeError):
            list(extract(None, []))  # Non-iterable data source
        with self.assertRaises(TypeError):
            list(extract(data, None))  # Non-iterable indices
        with self.assertRaises(ValueError):
            list(extract(data, [0.0, 1.0, 2.0]))  # Non-integer indices
        with self.assertRaises(ValueError):
            list(extract(data, [1, 2, -3]))  # Negative indices
        with self.assertRaises(IndexError):
            list(extract(data, [1, 2, len(data)]))  # Indices out of range

    def testNegativeOneBug(self):
        # When the lowest index was exactly -1, it matched the initial
        # iterator_position of -1 giving a zero advance step.
        extract = mi.extract

        with self.assertRaises(ValueError):
            list(extract('abcdefg', [1, 2, -1]))

    def testNoneValueBug(self):
        # The buffer used to be a list with unused slots marked with None.
        # The mark got conflated with None values in the data stream.
        extract = mi.extract
        data = ['a', 'b', 'None', 'c', 'd']
        self.assertEqual(list(extract(data, range(5))), data)

    def testAllOrderings(self):
        # Thorough test for all cases of five indices to detect
        # obscure corner case bugs.
        extract = mi.extract

        data = 'abcdefg'
        for indices in product(range(6), repeat=5):
            with self.subTest(indices=indices):
                actual = tuple(extract(data, indices))
                expected = itemgetter(*indices)(data)
                self.assertEqual(actual, expected)

    def testEarlyFree(self):
        # No references are held for skipped values or for previously
        # emitted values regardless of how long they were in the buffer.

        extract = mi.extract

        class TrackDels(str):
            def __del__(self):
                dead.add(str(self))

        dead = set()
        iterator = extract(map(TrackDels, 'ABCDEF'), [3, 2, 4, 5])

        value = next(iterator)
        gc.collect()  # Force collection on PyPy.
        self.assertEqual(value, 'D')  #  Returns D.  Buffered C is alive.
        self.assertEqual(dead, {'A', 'B'})  # A and B are dead.

        value = next(iterator)
        gc.collect()  # Force collection on PyPy
        self.assertEqual(value, 'C')  #  Returns C.

        value = next(iterator)
        gc.collect()  # Force collection on PyPy
        self.assertEqual(value, 'E')  #  Returns E.
        self.assertEqual(dead, {'A', 'B', 'D', 'C'})  # D and C are now dead.

    def testMonotonic(self):
        collatz = mi.iterate(lambda x: 3 * x + 1 if x % 2 == 1 else x // 2, 42)
        indices = count(0, 2)
        self.assertEqual(
            mi.take(3, mi.extract(collatz, indices, monotonic=True)),
            [42, 64, 16],
        )
        self.assertEqual(next(collatz), 8)
        self.assertEqual(next(indices), 6)

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

    def testLazyConsumption(self):
        extract = mi.extract

        inputStream = mi.peekable(iter('ABCDEFGHIJKLM'))
        iterator = extract(inputStream, [4, 2, 10])

        self.assertEqual(next(iterator), 'E')  # C is still buffered
        self.assertEqual(inputStream.peek(), 'F')

        self.assertEqual(next(iterator), 'C')
        self.assertEqual(inputStream.peek(), 'F')

        # Infinite input
        self.assertEqual(
            list(extract(count(), [5, 7, 3, 9, 4])), [5, 7, 3, 9, 4]
        )


class TestSerialize(TestCase):
    def testConcurrentCalls(self):
        result = 0
        resultLock = Lock()

        def producer(limit):
            'Non-concurrent producer. A generator version of range(limit).'
            for x in range(limit):
                yield x

        def consumer(counter):
            'Concurrent data consumer'
            nonlocal result
            total = 0
            for x in counter:
                total += x
            with resultLock:
                result += total

        limit = 10**6
        counter = mi.serialize(producer(limit))
        workers = [Thread(target=consumer, args=[counter]) for _ in range(10)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()

        self.assertEqual(result, limit * (limit - 1) // 2)


class TestSynchronized(TestCase):
    def testConcurrentCalls(self):
        unique = 10  # Number of distinct counters
        repetitions = 5  # Number of times each counter is used
        limit = 100  # Calls per counter per repetition

        @mi.synchronized
        def atomicCounter():
            # This is a generator so that non-concurrent calls are detectable.
            # To make calls while running more likely, this code uses random
            # time delays.
            i = 0
            while True:
                yield i
                nextI = i + 1
                sleep(random() / 1000)
                i = nextI

        def consumer(counter):
            for i in range(limit):
                next(counter)

        uniqueCounters = [atomicCounter() for _ in range(unique)]
        counters = uniqueCounters * repetitions
        workers = [
            Thread(target=consumer, args=[counter]) for counter in counters
        ]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
        self.assertEqual(
            {next(counter) for counter in uniqueCounters},
            {limit * repetitions},
        )


class TestConcurrentTee(TestCase):
    def testConcurrentConsumers(self):
        result = 0
        resultLock = Lock()

        def producer(limit):
            'Non-concurrent producer. A generator version of range(limit).'
            for x in range(limit):
                yield x

        def consumer(iterator):
            'Concurrent data consumer'
            nonlocal result
            reconstructed = [x for x in iterator]
            if reconstructed == list(range(limit)):
                with resultLock:
                    result += 1

        limit = 10**5
        numThreads = 100
        nonConcurrentSource = producer(limit)
        tees = mi.concurrentTee(nonConcurrentSource, n=numThreads)

        # Verify that locks are shared
        self.assertEqual(len({id(tObj.lock) for tObj in tees}), 1)

        # Run the consumers
        workers = [Thread(target=consumer, args=[tObj]) for tObj in tees]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()

        # Verify that every consumer received 100% of the  data (no dups or drops).
        self.assertEqual(result, len(tees))

        # Corner case
        nonConcurrentSource = producer(limit)
        tees = mi.concurrentTee(nonConcurrentSource, n=0)  # Zero n
        self.assertEqual(tees, ())

        # Error cases
        with self.assertRaises(ValueError):
            nonConcurrentSource = producer(limit)
            mi.concurrentTee(nonConcurrentSource, n=-1)  # Negative n
