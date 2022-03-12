import json
import os
import typing
import unittest

from src.git_idiff.gitdiff import GitDiff, GitFile

ARGS = 'args'
EXPECTED = 'expected'
VALUE = 'value'

MOCKED_DATA_DIR = os.path.join(os.path.dirname(__file__), 'mocked_data')
MOCKED_DIFF_DIR = os.path.join(MOCKED_DATA_DIR, 'diff')
MOCKED_STAT_DIR = os.path.join(MOCKED_DATA_DIR, 'status')

class GitDiffTest(unittest.TestCase):
    def test_get_diff(self):
        entries = [
            {
                ARGS: ['62a4472', '8ef1477'],
            },
            {
                ARGS: ['-M05', '3382256', 'c04fa3b'],
            },
            {
                ARGS: ['empty'],
            }
        ]

        for entry in entries:
            args = entry[ARGS]
            with self.subTest(args=args):
                gitdiff = GitDiff(args)
                files = gitdiff._process_diff(_get_mocked_diff_data(args))

                self.assertResultsEqual(
                    _get_mocked_diff_results(args),
                    _gitfiles_to_result(files),
                    check_status = False
                )

    def test_get_statuses(self):
        entries = [
            {
                ARGS: ['62a4472', '8ef1477'],
            },
            {
                ARGS: ['-M05', '3382256', 'c04fa3b'],
            },
            {
                ARGS: ['empty'],
            }
        ]

        for entry in entries:
            args = entry[ARGS]
            with self.subTest(args=args):
                gitdiff = GitDiff(args)
                files = gitdiff._process_diff(_get_mocked_diff_data(args))
                gitdiff._process_statuses(files, _get_mocked_status_data(args))

                self.assertResultsEqual(
                    _get_mocked_diff_results(args),
                    _gitfiles_to_result(files),
                    check_status = True
                )

    def assertResultsEqual(self, expected, actual, check_status=True):
        idx = 0
        for file in expected['gitfiles']:
            self.assertGitFileResultEqual(
                file,
                actual['gitfiles'][idx],
                check_status = check_status
            )
            idx += 1

    def assertGitFileResultEqual(self, expected, actual, check_status=True):
        self.assertEqual(expected['filename'], actual['filename'])
        self.assertEqual(expected['old_filename'], actual['old_filename'])
        self.assertEqual(expected['insertions'], actual['insertions'])
        self.assertEqual(expected['deletions'], actual['deletions'])
        self.assertListEqual(expected['headers'], actual['headers'])
        self.assertListEqual(expected['content'], actual['content'])

        if check_status:
            self.assertEqual(expected['status'], actual['status'])
            self.assertEqual(expected['score'], actual['score'])

def _get_mocked_diff_data(args: typing.List[str]) -> bytes:
    with open(os.path.join(MOCKED_DIFF_DIR, ' '.join(args)) + '.txt', 'rb') as file:
        return file.read()

def _get_mocked_status_data(args: typing.List[str]) -> bytes:
    with open(os.path.join(MOCKED_STAT_DIR, ' '.join(args)) + '.txt', 'rb') as file:
        return file.read()

def _get_mocked_diff_results(args: typing.List[str]) -> typing.Dict[str, typing.Any]:
    with open(os.path.join(MOCKED_DIFF_DIR, ' '.join(args)) + '.json', 'r') as file:
        return json.loads(file.read())

def _gitfiles_to_result(files: typing.List[GitFile]) -> typing.Dict[str, typing.Any]:
    return {
        'gitfiles': [ _gitfile_to_dict(file) for file in files ]
    }

def _gitfile_to_dict(file: GitFile) -> typing.Dict[str, typing.Any]:
    return {
        'filename': file.filename,
        'old_filename': file.old_filename,
        'insertions': file.insertions,
        'deletions': file.deletions,
        'headers': file.headers,
        'content': file.content,
        'status': file.status,
        'score': file.score
    }
