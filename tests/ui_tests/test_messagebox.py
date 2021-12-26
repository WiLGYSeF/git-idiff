import unittest

from src.git_idiff.ui.messagebox import MessageBox

MESSAGE = 'message'
WIDTH = 'width'
EXPECTED = 'expected'

class MessageBoxTest(unittest.TestCase):
    def test_box_msd(self):
        entries = [
            {
                MESSAGE: [
                    'this',
                    '0123456789012345 yeetus',
                    'asdfgad'
                ],
                WIDTH: 10,
                EXPECTED: [
                    'this',
                    '0123456789',
                    '012345 yee',
                    'tus',
                    'asdfgad'
                ]
            },
            {
                MESSAGE: [
                    'thistest',
                    'aaa'
                ],
                WIDTH: 4,
                EXPECTED: [
                    'this',
                    'test',
                    'aaa'
                ]
            },
        ]

        for entry in entries:
            message = entry[MESSAGE]
            width = entry[WIDTH]
            with self.subTest(message=message, width=width):
                self.assertListEqual(
                    entry[EXPECTED],
                    MessageBox.box_msg(message, width)
                )
