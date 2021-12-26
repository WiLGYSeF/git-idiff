import unittest

from src.git_idiff.gitdiff import GitDiff

ARGS = 'args'
EXPECTED = 'expected'
VALUE = 'value'

class GitDiffTest(unittest.TestCase):
    def test_sanitize_args(self):
        entries = [
            {
                ARGS: ['this', 'is', 'a', 'test'],
                EXPECTED: ['this', 'is', 'a', 'test']
            },
            {
                ARGS: ['this', '-', 'is', '--', 'a', 'test'],
                EXPECTED: ['this', '-', 'is']
            }
        ]

        for entry in entries:
            gitdiff = GitDiff(entry[ARGS])
            with self.subTest(args=entry[ARGS]):
                self.assertListEqual(entry[EXPECTED], gitdiff.args)

    def test_sanitize_args_whitelist_single(self):
        entries = [
            {
                ARGS: ['this', '-X', 'is', '-XX', 'a'],
                EXPECTED: ['this', 'is', 'a']
            },
            {
                ARGS: ['-RXw'],
                EXPECTED: ['-Rw']
            },
            {
                ARGS: ['-Xw'],
                EXPECTED: ['-w']
            },
            {
                ARGS: ['-RX'],
                EXPECTED: ['-R']
            }
        ]

        for entry in entries:
            gitdiff = GitDiff(entry[ARGS])
            with self.subTest(args=entry[ARGS]):
                self.assertListEqual(entry[EXPECTED], gitdiff.args)

    def test_sanitize_args_whitelist_single_param(self):
        entries = [
            {
                ARGS: ['-XM5X'],
                EXPECTED: ['-M5X']
            },
            {
                ARGS: ['-RXwM'],
                EXPECTED: ['-RwM']
            }
        ]

        for entry in entries:
            gitdiff = GitDiff(entry[ARGS])
            with self.subTest(args=entry[ARGS]):
                self.assertListEqual(entry[EXPECTED], gitdiff.args)

    def test_sanitize_args_whitelist(self):
        entries = [
            {
                ARGS: ['--not-whitelisted', '--cached', '--text', '--not-whitelisted'],
                EXPECTED: ['--cached', '--text']
            }
        ]

        for entry in entries:
            gitdiff = GitDiff(entry[ARGS])
            with self.subTest(args=entry[ARGS]):
                self.assertListEqual(entry[EXPECTED], gitdiff.args)

    def test_sanitize_args_line_prefix(self):
        entries = [
            {
                ARGS: ['--line-prefix=a'],
                EXPECTED: 'a'
            },
            {
                ARGS: ['--line-prefix=ab c'],
                EXPECTED: 'ab c'
            },
            {
                ARGS: ['--line-prefix=a', '--line-prefix=b'],
                EXPECTED: 'b'
            },
            {
                ARGS: [],
                EXPECTED: ''
            },
        ]

        for entry in entries:
            gitdiff = GitDiff(entry[ARGS])
            with self.subTest(args=entry[ARGS]):
                self.assertEqual(entry[EXPECTED], gitdiff.line_prefix_str)
                self.assertEqual(len(entry[EXPECTED]) != 0, gitdiff.has_prefix())

    def test_noprefix(self):
        entries = [
            {
                ARGS: ['--line-prefix=a'],
                VALUE: 'abc',
                EXPECTED: 'bc'
            },
            { # is this test valid?
                ARGS: ['--line-prefix=b'],
                VALUE: 'abc',
                EXPECTED: 'bc'
            },
            {
                ARGS: [],
                VALUE: 'abc',
                EXPECTED: 'abc'
            },
        ]

        for entry in entries:
            gitdiff = GitDiff(entry[ARGS])
            with self.subTest(args=entry[ARGS]):
                self.assertEqual(entry[EXPECTED], gitdiff.noprefix(entry[VALUE]))
