import curses
import typing

import gitdiff

class UiCurses:
    def __init__(self):
        self.stdscr = None
        self.filelist_column_width: int = 24

        self.pad_filelist = None
        self.pad_diff = None

        self.filelist: gitdiff.FileList = []
        self.selected_file: typing.Optional[str] = None

    def start(self, stdscr) -> None:
        self.stdscr = stdscr

        self.pad_filelist = curses.newpad(curses.LINES, self.filelist_column_width)
        self.pad_diff = curses.newpad(curses.LINES, curses.COLS - self.filelist_column_width)

        stdscr.erase()
        stdscr.refresh()

        self.update_filelist(gitdiff.get_filenames())
        self.update_diff(gitdiff.get_file_diff(self.filelist[0][0]))

        while True:
            self.input()

    def input(self) -> None:
        self.stdscr.getkey()

    def update_filelist(self, filelist: gitdiff.FileList) -> None:
        self.pad_filelist.erase()

        idx = 0
        for fname, added, removed in filelist:
            self.pad_filelist.addstr(idx, 0, f'{added} {removed} {fname}')
            idx += 1

        self.pad_filelist.refresh(0, 0, 0, 0, curses.LINES, self.filelist_column_width)

        self.filelist = filelist[:]

    def update_diff(self, diff: typing.List[str]) -> None:
        self.pad_diff.erase()

        idx = 0
        for line in diff:
            self.pad_diff.addstr(idx, 0, line)
            idx += 1

        self.pad_diff.refresh(
            0, 0,
            0, self.filelist_column_width,
            curses.LINES, curses.COLS - self.filelist_column_width
        )

def initialize(ui: UiCurses) -> None:
    curses.wrapper(ui.start)
