import unittest

from src.git_idiff.ui.utils import StrAttrFormat

INITIAL = 'initial'
ADD_LIST = 'add-list'
EXPECTED = 'expected'
EXPECTED_STR = 'expected-str'

class UtilsTest(unittest.TestCase):
    def test_strattrformat_add(self):
        entries = [
            {
                INITIAL: StrAttrFormat('this is', {
                    'repl': ('asdf', 0)
                }),
                ADD_LIST: [' a ', 'test'],
                EXPECTED: StrAttrFormat('this is a test', {
                    'repl': ('asdf', 0)
                })
            },
            {
                INITIAL: StrAttrFormat('this is', {
                    'repl': ('1234', 67)
                }),
                ADD_LIST: [
                    ' a ',
                    StrAttrFormat('test', {
                        'newval': ('aaaa', 4)
                    })
                ],
                EXPECTED: StrAttrFormat('this is a test', {
                    'repl': ('1234', 67),
                    'newval': ('aaaa', 4)
                })
            },
            {
                INITIAL: StrAttrFormat('this is', {
                    'repl': ('1234', 67)
                }),
                ADD_LIST: [
                    StrAttrFormat('test', {
                        'repl': ('aaaa', 4)
                    })
                ],
                EXPECTED: ValueError()
            },
            {
                INITIAL: StrAttrFormat('this is', {
                    'repl': ('1234', 67)
                }, 4),
                ADD_LIST: [
                    StrAttrFormat('test', {
                        'newval': ('aaaa', 4)
                    }, 1)
                ],
                EXPECTED: ValueError()
            }
        ]

        for entry in entries:
            initial = entry[INITIAL]
            add_list = entry[ADD_LIST]
            expected = entry[EXPECTED]

            with self.subTest(
                initial_format = initial.format,
                initial_values = initial.values,
                add_list = add_list,
            ):
                if not isinstance(expected, Exception):
                    result = initial + add_list[0]
                    for i in range(1, len(add_list)):
                        result += add_list[i]

                    self.assertEqual(expected.format, result.format)
                    self.assertSetEqual(set(expected.values.keys()), set(result.values.keys()))

                    for key in expected.values:
                        self.assertTupleEqual(expected.values[key], result.values[key])
                else:
                    with self.assertRaises(type(expected)):
                        result = initial.copy()
                        for add in add_list:
                            result += add

    def test_strattrformat_iter(self):
        entries = [
            {
                INITIAL: StrAttrFormat('this is {repl}', {
                    'repl': ('asdf', 0)
                }),
                EXPECTED: [
                    ('this is ', 0),
                    ('asdf', 0)
                ],
                EXPECTED_STR: 'this is asdf'
            },
            {
                INITIAL: StrAttrFormat('this {repl} is {repl}', {
                    'repl': ('asdf', 3)
                }, 4),
                EXPECTED: [
                    ('this ', 4),
                    ('asdf', 3),
                    (' is ', 4),
                    ('asdf', 3)
                ],
                EXPECTED_STR: 'this asdf is asdf'
            },
            {
                INITIAL: StrAttrFormat(r'this \{repl} {w} is', {
                    'repl': ('asdf', 7),
                    'w': ('zz', 4)
                }),
                EXPECTED: [
                    ('this \\', 0),
                    ('asdf', 7),
                    (' ', 0),
                    ('zz', 4),
                    (' is', 0)
                ],
                EXPECTED_STR: r'this \asdf zz is'
            },
            {
                INITIAL: StrAttrFormat('{repl}{w}{repl}', {
                    'repl': ('asdf', 0),
                    'w': ('', 4)
                }),
                EXPECTED: [
                    ('asdf', 0),
                    ('', 4),
                    ('asdf', 0)
                ],
                EXPECTED_STR: 'asdfasdf'
            },
            {
                INITIAL: StrAttrFormat('{a{repl}}{{repl}}', {
                    'repl': ('asdf', 5)
                }),
                EXPECTED: [
                    ('{a', 0),
                    ('asdf', 5),
                    ('}{', 0),
                    ('asdf', 5),
                    ('}', 0)
                ],
                EXPECTED_STR: '{aasdf}{asdf}'
            },
            {
                INITIAL: StrAttrFormat('abc{nonexisting}def', {
                    'repl': ('asdf', 0)
                }),
                EXPECTED: KeyError(),
                EXPECTED_STR: None
            }
        ]

        for entry in entries:
            initial = entry[INITIAL]
            expected = entry[EXPECTED]
            expected_str = entry[EXPECTED_STR]

            with self.subTest(
                initial_format = initial.format,
                initial_values = initial.values,
            ):
                if not isinstance(expected, Exception):
                    idx = 0
                    for val in initial:
                        self.assertTupleEqual(expected[idx], val)
                        idx += 1

                    self.assertEqual(expected_str, str(initial))
                    self.assertEqual(len(expected_str), len(initial))
                else:
                    with self.assertRaises(type(expected)):
                        list(initial)
