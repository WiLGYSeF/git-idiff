import unittest

from src.git_idiff.gitdiff import GitDiff

ARGS = 'args'
EXPECTED = 'expected'
VALUE = 'value'
REMOVED = 'removed'

class SanitizeArgsTest(unittest.TestCase):
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
            args = entry[ARGS]
            with self.subTest(args=args):
                gitdiff = GitDiff(args)
                self.assertListEqual(entry[EXPECTED], gitdiff.args)

    def test_sanitize_args_whitelist_single(self):
        entries = [
            {
                ARGS: ['this', '-Q', 'is', '-QQ', 'a'],
                EXPECTED: ['this', 'is', 'a'],
                REMOVED: ['-Q', '-Q', '-Q']
            },
            {
                ARGS: ['-RQw'],
                EXPECTED: ['-Rw'],
                REMOVED: ['-Q']
            },
            {
                ARGS: ['-Qw'],
                EXPECTED: ['-w'],
                REMOVED: ['-Q']
            },
            {
                ARGS: ['-RQ'],
                EXPECTED: ['-R'],
                REMOVED: ['-Q']
            }
        ]

        for entry in entries:
            args = entry[ARGS]
            with self.subTest(args=args):
                gitdiff = GitDiff(args)
                self.assertListEqual(entry[EXPECTED], gitdiff.args)
                self.assertListEqual(entry[REMOVED], gitdiff._removed_args)

    def test_sanitize_args_whitelist_single_param(self):
        entries = [
            {
                ARGS: ['-QM5X'],
                EXPECTED: ['-M5X'],
                REMOVED: ['-Q']
            },
            {
                ARGS: ['-RQwM'],
                EXPECTED: ['-RwM'],
                REMOVED: ['-Q']
            },
            {
                ARGS: ['-RXw'],
                EXPECTED: ['-R'],
                REMOVED: ['-Xw']
            }
        ]

        for entry in entries:
            args = entry[ARGS]
            with self.subTest(args=args):
                gitdiff = GitDiff(args)
                self.assertListEqual(entry[EXPECTED], gitdiff.args)
                self.assertListEqual(entry[REMOVED], gitdiff._removed_args)

    def test_sanitize_args_whitelist(self):
        entries = [
            {
                ARGS: ['--not-whitelisted', '--cached', '--text', '--not-wl'],
                EXPECTED: ['--cached', '--text'],
                REMOVED: ['--not-whitelisted', '--not-wl']
            }
        ]

        for entry in entries:
            gitdiff = GitDiff(entry[ARGS])
            with self.subTest(args=entry[ARGS]):
                self.assertListEqual(entry[EXPECTED], gitdiff.args)
                self.assertListEqual(entry[REMOVED], gitdiff._removed_args)

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
            args = entry[ARGS]
            expected = entry[EXPECTED]

            with self.subTest(args=args):
                gitdiff = GitDiff(args)
                self.assertEqual(expected, gitdiff.line_prefix)
                self.assertEqual(len(expected) != 0, gitdiff.has_prefix())

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
            args = entry[ARGS]
            with self.subTest(args=args):
                gitdiff = GitDiff(args)
                self.assertEqual(entry[EXPECTED], gitdiff.noprefix(entry[VALUE]))
