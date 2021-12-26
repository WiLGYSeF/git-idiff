import unittest

from src.git_idiff.ui.vector import Vector

INITIAL = 'initial'
VAL = 'val'
EXPECTED = 'expected'

class VectorTest(unittest.TestCase):
    def test_vector_add(self):
        entries = [
            {
                INITIAL: Vector(5, 1),
                VAL: Vector(4, -2),
                EXPECTED: Vector(9, -1)
            },
        ]

        for entry in entries:
            initial = entry[INITIAL]
            vec = entry[VAL]
            expected = entry[EXPECTED]

            with self.subTest(initial=initial, vec=vec):
                self.assertEqual(expected, initial + vec)

                copy = initial.copy()
                copy += vec
                self.assertEqual(expected, copy)

                self.assertEqual(expected, initial.copy().add(vec)) # pylint: disable=no-value-for-parameter
                self.assertEqual(expected, initial.copy().add(vec.y, vec.x)) # pylint: disable=no-value-for-parameter

    def test_vector_sub(self):
        entries = [
            {
                INITIAL: Vector(5, 1),
                VAL: Vector(4, -2),
                EXPECTED: Vector(1, 3)
            },
        ]

        for entry in entries:
            initial = entry[INITIAL]
            vec = entry[VAL]
            expected = entry[EXPECTED]

            with self.subTest(initial=initial, vec=vec):
                self.assertEqual(expected, initial - vec)

                copy = initial.copy()
                copy -= vec
                self.assertEqual(expected, copy)

                self.assertEqual(expected, initial.copy().sub(vec)) # pylint: disable=no-value-for-parameter
                self.assertEqual(expected, initial.copy().sub(vec.y, vec.x)) # pylint: disable=no-value-for-parameter

    def test_vector_mul(self):
        entries = [
            {
                INITIAL: Vector(5, 1),
                VAL: 3,
                EXPECTED: Vector(15, 3)
            },
        ]

        for entry in entries:
            initial = entry[INITIAL]
            val = entry[VAL]
            expected = entry[EXPECTED]

            with self.subTest(initial=initial, val=val):
                self.assertEqual(expected, initial * val)

                copy = initial.copy()
                copy *= val
                self.assertEqual(expected, copy)

                self.assertEqual(expected, initial.copy().mul(val))

    def test_vector_floordiv(self):
        entries = [
            {
                INITIAL: Vector(15, 10),
                VAL: 3,
                EXPECTED: Vector(5, 3)
            },
        ]

        for entry in entries:
            initial = entry[INITIAL]
            val = entry[VAL]
            expected = entry[EXPECTED]

            with self.subTest(initial=initial, val=val):
                self.assertEqual(expected, initial // val)

                copy = initial.copy()
                copy //= val
                self.assertEqual(expected, copy)

                self.assertEqual(expected, initial.copy().floordiv(val))

    def test_vector_neg(self):
        entries = [
            {
                INITIAL: Vector(15, -10),
                EXPECTED: Vector(-15, 10)
            },
        ]

        for entry in entries:
            initial = entry[INITIAL]
            expected = entry[EXPECTED]

            with self.subTest(initial=initial):
                self.assertEqual(expected, -initial.copy())
                self.assertEqual(expected, initial.copy().neg())

    def test_vector_abs(self):
        entries = [
            {
                INITIAL: Vector(15, -10),
                EXPECTED: Vector(15, 10)
            },
        ]

        for entry in entries:
            initial = entry[INITIAL]
            expected = entry[EXPECTED]

            with self.subTest(initial=initial):
                self.assertEqual(expected, abs(initial.copy()))
                self.assertEqual(expected, initial.copy().abs())

    def test_vector_eq_ne(self):
        entries = [
            {
                INITIAL: Vector(15, -10),
                VAL: Vector(15, -10),
                EXPECTED: True
            },
            {
                INITIAL: Vector(15, -10),
                VAL: Vector(6, 70),
                EXPECTED: False
            },
            {
                INITIAL: Vector(15, -10),
                VAL: Vector(15, 6),
                EXPECTED: False
            },
            {
                INITIAL: Vector(15, -10),
                VAL: 1234,
                EXPECTED: False
            },
        ]

        for entry in entries:
            initial = entry[INITIAL]
            val = entry[VAL]
            expected = entry[EXPECTED]

            with self.subTest(initial=initial, val=val):
                self.assertEqual(expected, initial == val)
                self.assertEqual(not expected, initial != val)

    def test_vector_str(self):
        entries = [
            {
                INITIAL: Vector(15, -10),
                EXPECTED: '<15, -10>'
            },
        ]

        for entry in entries:
            initial = entry[INITIAL]
            expected = entry[EXPECTED]

            with self.subTest(initial=initial):
                self.assertEqual(expected, str(initial))

    def test_vector_bool(self):
        entries = [
            {
                INITIAL: Vector(15, -10),
                EXPECTED: True
            },
            {
                INITIAL: Vector(-15, -10),
                EXPECTED: True
            },
            {
                INITIAL: Vector(0, 0),
                EXPECTED: False
            },
        ]

        for entry in entries:
            initial = entry[INITIAL]
            expected = entry[EXPECTED]

            with self.subTest(initial=initial):
                self.assertEqual(expected, bool(initial))
