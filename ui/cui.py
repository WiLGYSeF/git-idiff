import curses
import typing

import gitdiff
from ui.pad import CursesPad

class CursesUi:
    COLOR_ADD = 1
    COLOR_REMOVE = 2
    COLOR_SECTION = 3

    CURSES_BUTTON5_PRESSED = 0x00200000 # thanks python

    def __init__(self, diff_args: typing.Optional[typing.List[str]] = None):
        self.diff_args: typing.List[str] = diff_args if diff_args is not None else []

        self.stdscr = None
        self.filelist_column_width: int = 24
        self.filelist_scroll_offset: int = 0

        self.pad_filelist: typing.Optional[CursesPad] = None
        self.pad_diff: typing.Optional[CursesPad] = None
        self.pad_statusbar: typing.Optional[CursesPad] = None

        self.filelist: gitdiff.FileList = []
        self.total_insertions: int = 0
        self.total_deletions: int = 0

        self.diff_contents: typing.List[str] = []

        self.selected_file: typing.Optional[str] = None
        self.selected_file_idx: int = -1
        self.filelist_visible: bool = True

    def run(self, stdscr) -> None:
        self.stdscr = stdscr
        lines, columns = stdscr.getmaxyx()

        curses.curs_set(False)
        curses.mousemask(-1)

        curses.use_default_colors()
        curses.init_pair(CursesUi.COLOR_ADD, curses.COLOR_GREEN, -1)
        curses.init_pair(CursesUi.COLOR_REMOVE, curses.COLOR_RED, -1)
        curses.init_pair(CursesUi.COLOR_SECTION, curses.COLOR_CYAN, -1)

        self.pad_filelist = CursesPad(stdscr,
            height = lines - 1,
            width = self.filelist_column_width,
            offset_y = 0,
            offset_x = 0
        )
        self.pad_diff = CursesPad(stdscr,
            height = lines - 1,
            width = columns - self.filelist_column_width,
            offset_y = 0,
            offset_x = self.filelist_column_width
        )
        self.pad_statusbar = CursesPad(stdscr,
            height = 2,
            width = columns,
            offset_y = lines - 1,
            offset_x = 0
        )

        stdscr.erase()
        stdscr.refresh()

        self.get_files()
        self._select_file(0)

        while True:
            c = self.stdscr.getch()
            if c < 256:
                ch = chr(c)
                if ch == 'f':
                    self.toggle_filelist()
                elif ch == 'n':
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
            elif c == curses.KEY_PPAGE:
                self.pad_diff.scroll(-self.pad_diff.height, 0)
            elif c == curses.KEY_NPAGE:
                self.pad_diff.scroll(self.pad_diff.height, 0)
            elif c == curses.KEY_HOME:
                self.pad_diff.refresh(self.pad_diff.y, 0)
            elif c == curses.KEY_END:
                self.pad_diff.refresh(self.pad_diff.y, self.pad_diff.pad.getmaxyx()[1])
            elif c == curses.KEY_MOUSE:
                _, x, y, _, state = curses.getmouse()
                if self.pad_filelist.pad.enclose(y, x):
                    if state & curses.BUTTON1_CLICKED:
                        self._select_file(self.pad_filelist.y + y)
                    elif state & curses.BUTTON4_PRESSED:
                        self.select_prev_file()
                    elif state & CursesUi.CURSES_BUTTON5_PRESSED:
                        self.select_next_file()
                elif self.pad_diff.pad.enclose(y, x):
                    if state & curses.BUTTON4_PRESSED:
                        if state & curses.BUTTON_SHIFT:
                            self.pad_diff.scroll(0, -5)
                        else:
                            self.pad_diff.scroll(-5, 0)
                    elif state & CursesUi.CURSES_BUTTON5_PRESSED:
                        if state & curses.BUTTON_SHIFT:
                            self.pad_diff.scroll(0, 5)
                        else:
                            self.pad_diff.scroll(5, 0)
            elif c == curses.KEY_RESIZE:
                pass

            self.update_statusbar()

    def get_files(self) -> None:
        self.filelist = gitdiff.get_filenames(self.diff_args)
        self.update_filelist()
        self.update_statusbar()

    def select_next_file(self) -> bool:
        if self.selected_file_idx == len(self.filelist) - 1:
            return False

        self._select_file(self.selected_file_idx + 1)
        if self.selected_file_idx - self.pad_filelist.y >= self.pad_filelist.height - 1 - self.filelist_scroll_offset:
            self.pad_filelist.scroll(1, 0)
        return True

    def select_prev_file(self) -> bool:
        if self.selected_file_idx == 0:
            return False

        self._select_file(self.selected_file_idx - 1)
        if self.selected_file_idx - self.pad_filelist.y <= self.filelist_scroll_offset:
            self.pad_filelist.scroll(-1, 0)
        return True

    def _select_file(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.filelist):
            return

        self.selected_file_idx = idx
        self.selected_file = self.filelist[self.selected_file_idx][0]

        self.get_file_diff()

        self.update_filelist()
        self.update_diff()
        self.update_statusbar()

    def get_file_diff(self) -> None:
        self.diff_contents = gitdiff.get_file_diff(self.selected_file, self.diff_args)

    def toggle_filelist(self) -> None:
        if self.filelist_visible:
            self.filelist_visible = False
            self.pad_diff.offset_x -= self.filelist_column_width
            self.pad_diff.width += self.filelist_column_width

            self.pad_filelist.pad.erase()
            self.pad_filelist.refresh(0, 0)
        else:
            self.filelist_visible = True
            self.pad_diff.offset_x += self.filelist_column_width
            self.pad_diff.width -= self.filelist_column_width

            self.update_filelist()

        self.update_diff()

    def update_filelist(self) -> None:
        if not self.filelist_visible:
            return

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

        self.total_insertions = 0
        self.total_deletions = 0

        idx = 0
        for file in self.filelist:
            fname = file.filename
            added = file.insertions
            removed = file.deletions

            if added is not None:
                added_str = str(added)
                self.total_insertions += added
            else:
                added_str = '-'

            if removed is not None:
                removed_str = str(removed)
                self.total_deletions += removed

            total_length = len(f'{added_str} {removed_str} {fname}')
            length = 0

            if total_length > max_x:
                fname = '##' + fname[
                    max(len(fname) - (max_x - len(f'{added_str} {removed_str} ##')), 0)
                    :
                ]

            def write(val, attr=curses.A_NORMAL):
                nonlocal length

                if idx == self.selected_file_idx:
                    attr |= curses.A_REVERSE

                if length + len(val) >= max_x:
                    val = val[len(val) - (max_x - length):]
                if len(val) > 0:
                    self.pad_filelist.pad.addstr(idx, length, val, attr)
                    length += len(val)

            write(added_str, curses.color_pair(CursesUi.COLOR_ADD))
            write(' ')
            write(removed_str, curses.color_pair(CursesUi.COLOR_REMOVE))
            write(' ')
            write(fname)
            write(' ' * (max_x - length))
            idx += 1

        self.pad_filelist.refresh(self.pad_filelist.y, 0)

    def update_diff(self) -> None:
        self.pad_diff.pad.erase()

        max_y, max_x = self.pad_diff.pad.getmaxyx()
        longest_line = self.diff_longest_line()
        if len(self.diff_contents) != max_y or longest_line != max_x:
            self.pad_diff.refresh(0, 0)
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

    def update_statusbar(self) -> None:
        self.pad_statusbar.pad.erase()

        _, max_x = self.pad_statusbar.pad.getmaxyx()

        diff_longest_line = self.diff_longest_line()
        diff_linenum = min(len(self.diff_contents), self.pad_diff.height + self.pad_diff.y)
        diff_colnum = min(diff_longest_line, self.pad_diff.width + self.pad_diff.x)

        leftstring = f' {self.selected_file_idx + 1} / {len(self.filelist)} files  +{self.total_insertions}  -{self.total_deletions}'
        centerstring = ' '
        rightstring = f'({diff_linenum}, {diff_colnum}) / ({len(self.diff_contents)}, {diff_longest_line}) '

        leftcenter_pad = ' ' * (
            (max_x - (len(leftstring) + len(centerstring) + len(rightstring))) // 2
        )
        centerright_pad = ' ' * (
            max_x - (len(leftstring) + len(centerstring) + len(rightstring) + len(leftcenter_pad))
        )

        self.pad_statusbar.pad.addstr(
            0, 0,
            (leftstring + leftcenter_pad + centerstring + centerright_pad + rightstring)[:max_x],
            curses.A_REVERSE
        )

        self.pad_statusbar.refresh(0, 0)

    def diff_longest_line(self) -> int:
        if len(self.diff_contents) == 0:
            return 0
        return max( len(line) for line in self.diff_contents )

def curses_initialize(cui: CursesUi) -> None:
    curses.wrapper(cui.run)
