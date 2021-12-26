import unittest

from src.git_idiff.gitdiff import GitFile
from src.git_idiff.ui.filelist import _gitfile_to_entry

GITFILE = 'gitfile'
MAX_X = 'max_x'
EXPECTED = 'expected'

class FileListTest(unittest.TestCase):
    def test_gitfile_to_entry(self):
        entries = [
            {
                GITFILE: GitFile('test', None, 5, 2),
                MAX_X: 10,
                EXPECTED: ('5', '2', 'test')
            },
            {
                GITFILE: GitFile('testasdf', None, 5, 2),
                MAX_X: 10,
                EXPECTED: ('5', '2', '##asdf')
            },
            {
                GITFILE: GitFile('test', None, 5, 2),
                MAX_X: 3,
                EXPECTED: ('5', '2', '##')
            },
            {
                GITFILE: GitFile('test', None, None, None),
                MAX_X: 10,
                EXPECTED: ('-', '-', 'test')
            },
        ]

        for entry in entries:
            with self.subTest(gitfile=entry[GITFILE], max_x=entry[MAX_X]):
                self.assertTupleEqual(
                    entry[EXPECTED],
                    _gitfile_to_entry(entry[GITFILE], entry[MAX_X])
                )
