import curses
import typing

import gitdiff
from ui.pad import CursesPad

class CursesUi:
    COLOR_ADD = 1
    COLOR_REMOVE = 2
    COLOR_SECTION = 3

    def __init__(self, diff_args: typing.Optional[typing.List[str]] = None):
        self.diff_args: typing.List[str] = diff_args if diff_args is not None else []

        self.stdscr = None
        self.filelist_column_width: int = 24

        self.pad_filelist: typing.Optional[CursesPad] = None
        self.pad_diff: typing.Optional[CursesPad] = None

        self.filelist: gitdiff.FileList = []
        self.diff_contents: typing.List[str] = []

        self.selected_file: typing.Optional[str] = None
        self.selected_file_idx: int = -1
        self.diff_linenum: int = 1

    def run(self, stdscr) -> None:
        self.stdscr = stdscr

        curses.curs_set(False)

        curses.use_default_colors()
        curses.init_pair(CursesUi.COLOR_ADD, curses.COLOR_GREEN, -1)
        curses.init_pair(CursesUi.COLOR_REMOVE, curses.COLOR_RED, -1)
        curses.init_pair(CursesUi.COLOR_SECTION, curses.COLOR_CYAN, -1)

        self.pad_filelist = CursesPad(curses,
            height = curses.LINES,
            width = self.filelist_column_width,
            offset_y = 0,
            offset_x = 0
        )
        self.pad_diff = CursesPad(curses,
            height = curses.LINES,
            width = curses.COLS - self.filelist_column_width,
            offset_y = 0,
            offset_x = self.filelist_column_width
        )

        stdscr.erase()
        stdscr.refresh()

        self.filelist = gitdiff.get_filenames(self.diff_args)
        self.update_filelist()

        self._select_file(0)

        while True:
            c = self.stdscr.getch()
            if c < 256:
                ch = chr(c)
                if ch == 'n':
                    self.select_next_file()
                elif ch == 'p':
                    self.select_prev_file()
                elif ch == 'q':
                    break
            elif c == curses.KEY_UP:
                self.pad_diff.scroll(-1, 0)
            elif c == curses.KEY_DOWN:
                self.pad_diff.scroll(1, 0)
            elif c == curses.KEY_LEFT:
                self.pad_diff.scroll(0, -1)
            elif c == curses.KEY_RIGHT:
                self.pad_diff.scroll(0, 1)
            elif c == curses.KEY_RESIZE:
                pass

    def select_next_file(self) -> bool:
        if self.selected_file_idx == len(self.filelist) - 1:
            return False
        self._select_file(self.selected_file_idx + 1)
        return True

    def select_prev_file(self) -> bool:
        if self.selected_file_idx == 0:
            return False
        self._select_file(self.selected_file_idx - 1)
        return True

    def _select_file(self, idx: int) -> None:
        self.selected_file_idx = idx
        self.selected_file = self.filelist[self.selected_file_idx][0]

        self.diff_contents = gitdiff.get_file_diff(self.selected_file, self.diff_args)
        self.update_filelist()
        self.update_diff()

    def update_filelist(self) -> None:
        self.pad_filelist.pad.erase()

        max_y, max_x = self.pad_filelist.pad.getmaxyx()
        if len(self.filelist) >= max_y:
            self.pad_filelist.pad.resize(len(self.filelist) + 1, max_x)

        # create a right border and decrease max_x to account for it
        self.pad_filelist.pad.border(
            ' ', 0, ' ', ' ',
            ' ', curses.ACS_VLINE, ' ', curses.ACS_VLINE
        )
        max_x -= 1

        idx = 0
        for fname, added, removed in self.filelist:
            total_length = len(f'{added} {removed} {fname}')
            length = 0

            if total_length > max_x:
                fname = '...' + fname[len(fname) - (max_x - total_length) - 3:]

            def write(s, attr=curses.A_NORMAL):
                nonlocal length

                if idx == self.selected_file_idx:
                    attr |= curses.A_REVERSE

                self.pad_filelist.pad.addstr(idx, length, s, attr)
                length += len(s)

            write(str(added), curses.color_pair(CursesUi.COLOR_ADD))
            write(' ')
            write(str(removed), curses.color_pair(CursesUi.COLOR_REMOVE))
            write(' ' + fname)
            write(' ' * (max_x - length))
            idx += 1

        self.pad_filelist.refresh(0, 0)

    def update_diff(self) -> None:
        self.pad_diff.pad.erase()

        max_y, max_x = self.pad_diff.pad.getmaxyx()
        longest_line = max(( len(line) for line in self.diff_contents ))
        if len(self.diff_contents) >= max_y or longest_line >= max_x:
            self.pad_diff.pad.resize(len(self.diff_contents) + 1, max(longest_line + 1, max_x))

        idx = 0
        for line in self.diff_contents:
            if len(line) == 0:
                idx += 1
                continue

            attr = curses.A_NORMAL
            if line[0] == '+':
                attr = curses.color_pair(CursesUi.COLOR_ADD)
            elif line[0] == '-':
                attr = curses.color_pair(CursesUi.COLOR_REMOVE)
            elif line[0] == '@':
                attr = curses.color_pair(CursesUi.COLOR_SECTION)

            self.pad_diff.pad.addstr(idx, 0, line, attr)
            idx += 1

        self.pad_diff.refresh(0, 0)

def curses_initialize(cui: CursesUi) -> None:
    curses.wrapper(cui.run)
