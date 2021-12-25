import curses
import typing

import gitdiff

class UiCurses:
    COLOR_ADD = 1
    COLOR_REMOVE = 2
    COLOR_SECTION = 3

    def __init__(self):
        self.stdscr = None
        self.filelist_column_width: int = 24

        self.pad_filelist = None
        self.pad_filelist_y: int = 0
        self.pad_filelist_x: int = 0

        self.pad_diff = None
        self.pad_diff_y: int = 0
        self.pad_diff_x: int = 0

        self.filelist: gitdiff.FileList = []
        self.selected_file: typing.Optional[str] = None
        self.diff_linenum: int = 1

    def start(self, stdscr) -> None:
        self.stdscr = stdscr

        curses.curs_set(False)

        curses.use_default_colors()
        curses.init_pair(UiCurses.COLOR_ADD, curses.COLOR_GREEN, -1)
        curses.init_pair(UiCurses.COLOR_REMOVE, curses.COLOR_RED, -1)
        curses.init_pair(UiCurses.COLOR_SECTION, curses.COLOR_CYAN, -1)

        self.pad_filelist = curses.newpad(curses.LINES, self.filelist_column_width)
        self.pad_diff = curses.newpad(curses.LINES, curses.COLS - self.filelist_column_width)

        stdscr.erase()
        stdscr.refresh()

        self.update_filelist(gitdiff.get_filenames())
        self.update_diff(gitdiff.get_file_diff(self.filelist[0][0]))

        while True:
            c = self.input()
            if c < 256:
                ch = chr(c)
                if ch in 'Qq':
                    break
            elif c == curses.KEY_UP:
                self.refresh_diff(self.pad_diff_y - 1, self.pad_diff_x)
            elif c == curses.KEY_DOWN:
                self.refresh_diff(self.pad_diff_y + 1, self.pad_diff_x)
            elif c == curses.KEY_LEFT:
                self.refresh_diff(self.pad_diff_y, self.pad_diff_x - 1)
            elif c == curses.KEY_RIGHT:
                self.refresh_diff(self.pad_diff_y, self.pad_diff_x + 1)
            elif c == curses.KEY_RESIZE:
                pass

    def input(self) -> int:
        return self.stdscr.getch()

    def update_filelist(self, filelist: gitdiff.FileList) -> None:
        self.pad_filelist.erase()

        max_y, max_x = self.pad_filelist.getmaxyx()
        if len(filelist) >= max_y:
            self.pad_filelist.resize(len(filelist) + 1, max_x)

        # create a right border and decrease max_x to account for it
        self.pad_filelist.border(
            ' ', 0, ' ', ' ',
            ' ', curses.ACS_VLINE, ' ', curses.ACS_VLINE
        )
        max_x -= 1

        idx = 0
        for fname, added, removed in filelist:
            total_length = len(f'{added} {removed} {fname}')
            length = 0

            if total_length > max_x:
                fname = '...' + fname[len(fname) - (max_x - total_length) - 3:]

            def write(s, attr=None):
                nonlocal length
                self.pad_filelist.addstr(
                    idx, length,
                    s,
                    attr if attr is not None else curses.A_NORMAL
                )
                length += len(s)

            write(str(added), curses.color_pair(UiCurses.COLOR_ADD))
            write(' ')
            write(str(removed), curses.color_pair(UiCurses.COLOR_REMOVE))
            write(' ' + fname)
            idx += 1

        self.refresh_filelist(0, 0)
        self.filelist = filelist[:]

    def refresh_filelist(self, y: int, x: int) -> None:
        self.pad_filelist.refresh(
            y, x,
            0, 0,
            curses.LINES - 1, min(self.filelist_column_width, curses.COLS - 1)
        )
        self.pad_filelist_y = y
        self.pad_filelist_x = x

    def update_diff(self, diff: typing.List[str]) -> None:
        self.pad_diff.erase()

        max_y, max_x = self.pad_diff.getmaxyx()
        longest_line = max(( len(line) for line in diff ))
        if len(diff) >= max_y or longest_line >= max_x:
            self.pad_diff.resize(len(diff) + 1, max(longest_line + 1, max_x))

        idx = 0
        for line in diff:
            if len(line) == 0:
                idx += 1
                continue

            attr = None
            if line[0] == '+':
                attr = curses.color_pair(UiCurses.COLOR_ADD)
            elif line[0] == '-':
                attr = curses.color_pair(UiCurses.COLOR_REMOVE)
            elif line[0] == '@':
                attr = curses.color_pair(UiCurses.COLOR_SECTION)

            self.pad_diff.addstr(idx, 0, line, attr if attr is not None else curses.A_NORMAL)
            idx += 1

        self.refresh_diff(0, 0)
        self.diff_linenum = 1

    def refresh_diff(self, y: int, x: int) -> None:
        self.pad_diff.refresh(
            y, x,
            0, self.filelist_column_width,
            curses.LINES - 1, curses.COLS - 1
        )
        self.pad_diff_y = y
        self.pad_diff_x = x

def initialize(ui: UiCurses) -> None:
    curses.wrapper(ui.start)
