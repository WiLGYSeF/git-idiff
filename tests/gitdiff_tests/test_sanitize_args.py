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
                EXPECTED: ['this', '-', 'is', '--']
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
                self.assertListEqual(entry[REMOVED], gitdiff.removed_args)

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
                self.assertListEqual(entry[REMOVED], gitdiff.removed_args)

    def test_sanitize_args_whitelist(self):
        entries = [
            {
                ARGS: ['--not-whitelisted', '--cached', '--text', '--not-wl'],
                EXPECTED: ['--cached', '--text'],
                REMOVED: ['--not-whitelisted', '--not-wl']
            }
        ]

        for entry in entries:
            args = entry[ARGS]
            with self.subTest(args=args):
                gitdiff = GitDiff(args)
                self.assertListEqual(entry[EXPECTED], gitdiff.args)
                self.assertListEqual(entry[REMOVED], gitdiff.removed_args)

    def test_sanitize_args_src_dst_prefix(self):
        entries = [
            {
                ARGS: ['--src-prefix=y'],
                EXPECTED: ('y', None)
            },
            {
                ARGS: ['--dst-prefix=z'],
                EXPECTED: (None, 'z')
            }
        ]

        for entry in entries:
            args = entry[ARGS]
            expected = entry[EXPECTED]

            with self.subTest(args=args):
                gitdiff = GitDiff(args)
                src, dst = expected
                if src is not None:
                    self.assertEqual(src, gitdiff.src_prefix)
                if dst is not None:
                    self.assertEqual(dst, gitdiff.dst_prefix)
