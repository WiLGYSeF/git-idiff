import curses
import unittest

from src.git_idiff.gitdiff import GitFile
from src.git_idiff.ui.filelist import _gitfile_to_saf, _gitfile_to_entry
from ..testutils import patch

GITFILE = 'gitfile'
MAX_X = 'max_x'
EXPECTED = 'expected'

class FileListTest(unittest.TestCase):
    def test_gitfile_to_saf(self):
        entries = [
            {
                GITFILE: GitFile('test', None, 5, 2),
                MAX_X: 12,
                EXPECTED: 'X 5 2   test'
            },
            {
                GITFILE: GitFile('testasdf', None, 5, 2),
                MAX_X: 10,
                EXPECTED: 'X 5 2 ##df'
            },
            {
                GITFILE: GitFile('test', None, 15, 2),
                MAX_X: 3,
                EXPECTED: 'X 1'
            },
            {
                GITFILE: GitFile('test', None, None, None),
                MAX_X: 12,
                EXPECTED: 'X - -   test'
            },
        ]

        for entry in entries:
            file = entry[GITFILE]
            max_x = entry[MAX_X]
            with self.subTest(gitfile=file, max_x=max_x):
                with patch(curses, 'color_pair', lambda x: 0):
                    self.assertEqual(
                        entry[EXPECTED],
                        str(_gitfile_to_saf(file, 0, max_x))[:max_x]
                    )

    def test_gitfile_to_entry(self):
        entries = [
            {
                GITFILE: GitFile('test', None, 5, 2),
                MAX_X: 12,
                EXPECTED: ('X', '5', '2', 'test')
            },
            {
                GITFILE: GitFile('testasdf', None, 5, 2),
                MAX_X: 10,
                EXPECTED: ('X', '5', '2', '##df')
            },
            {
                GITFILE: GitFile('test', None, 5, 2),
                MAX_X: 3,
                EXPECTED: ('X', '5', '2', '##')
            },
            {
                GITFILE: GitFile('test', None, None, None),
                MAX_X: 12,
                EXPECTED: ('X', '-', '-', 'test')
            },
        ]

        for entry in entries:
            with self.subTest(gitfile=entry[GITFILE], max_x=entry[MAX_X]):
                self.assertTupleEqual(
                    entry[EXPECTED],
                    _gitfile_to_entry(entry[GITFILE], entry[MAX_X])
                )
