import unittest

from src.git_idiff.gitdiff import GitDiff

ARGS = 'args'
EXPECTED = 'expected'
VALUE = 'value'

class GitDiffTest(unittest.TestCase):
    def test_sanitize_args(self):
        ENTRIES = [
            {
                ARGS: ['this', 'is', 'a', 'test'],
                EXPECTED: ['this', 'is', 'a', 'test']
            },
            {
                ARGS: ['this', '-', 'is', '--', 'a', 'test'],
                EXPECTED: ['this', '-', 'is']
            }
        ]

        for entry in ENTRIES:
            gitdiff = GitDiff(entry[ARGS])
            self.assertListEqual(entry[EXPECTED], gitdiff.args)

    def test_sanitize_args_whitelist_single(self):
        ENTRIES = [
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

        for entry in ENTRIES:
            gitdiff = GitDiff(entry[ARGS])
            self.assertListEqual(entry[EXPECTED], gitdiff.args)

    def test_sanitize_args_whitelist(self):
        ENTRIES = [
            {
                ARGS: ['--not-whitelisted', '--cached', '--text', '--not-whitelisted'],
                EXPECTED: ['--cached', '--text']
            }
        ]

        for entry in ENTRIES:
            gitdiff = GitDiff(entry[ARGS])
            self.assertListEqual(entry[EXPECTED], gitdiff.args)

    def test_sanitize_args_line_prefix(self):
        ENTRIES = [
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

        for entry in ENTRIES:
            gitdiff = GitDiff(entry[ARGS])
            self.assertEqual(entry[EXPECTED], gitdiff.line_prefix_str)
            self.assertEqual(len(entry[EXPECTED]) != 0, gitdiff.has_prefix())

    def test_noprefix(self):
        ENTRIES = [
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

        for entry in ENTRIES:
            gitdiff = GitDiff(entry[ARGS])
            self.assertEqual(entry[EXPECTED], gitdiff.noprefix(entry[VALUE]))
