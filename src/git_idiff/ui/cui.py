import curses
import typing

from gitdiff import GitDiff, GitFile
from ui.colors import init_colors
from ui.diff import DiffPad
from ui.filelist import FileList
from ui.pad import CursesPad

class CursesUi:
    FILELIST_SCROLL_OFFSET = 1

    CURSES_BUTTON5_PRESSED = 0x00200000 # thanks python

    def __init__(self, diff_args: typing.Optional[typing.List[str]] = None):
        self.gitdiff: GitDiff = GitDiff(diff_args)

        self.stdscr = None
        self.filelist_column_width: int = 24

        self.pad_filelist: FileList = None
        self.pad_diff: DiffPad = None
        self.pad_statusbar: CursesPad = None

        self.filelist: typing.List[GitFile] = []
        self.total_insertions: int = 0
        self.total_deletions: int = 0

        self.diff_headers: typing.List[str] = []
        self.diff_contents: typing.List[str] = []

        self.selected_file: typing.Optional[str] = None
        self.selected_file_idx: int = -1

    def run(self, stdscr) -> None:
        self.stdscr = stdscr
        lines, columns = stdscr.getmaxyx()

        curses.curs_set(False)
        curses.mousemask(-1)
        init_colors()

        self.pad_filelist = FileList(stdscr, self.filelist_column_width)
        self.pad_diff = DiffPad(stdscr, self.gitdiff, self.filelist_column_width)
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
        self.filelist = self.gitdiff.get_filenames()
        self.total_insertions = 0
        self.total_deletions = 0

        for file in self.filelist:
            if file.insertions is not None:
                self.total_insertions += file.insertions
            if file.deletions is not None:
                self.total_deletions += file.deletions

        self.update_filelist()
        self.update_statusbar()

    def select_next_file(self) -> bool:
        if self.selected_file_idx == len(self.filelist) - 1:
            return False

        self._select_file(self.selected_file_idx + 1)
        if self.selected_file_idx - self.pad_filelist.y >= self.pad_filelist.height - 1 - CursesUi.FILELIST_SCROLL_OFFSET:
            self.pad_filelist.scroll(1, 0)
        return True

    def select_prev_file(self) -> bool:
        if self.selected_file_idx == 0:
            return False

        self._select_file(self.selected_file_idx - 1)
        if self.selected_file_idx - self.pad_filelist.y <= CursesUi.FILELIST_SCROLL_OFFSET:
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
        self.diff_headers, self.diff_contents = self.gitdiff.get_file_diff(self.selected_file)

    def toggle_filelist(self) -> None:
        if self.pad_filelist.visible:
            self.pad_filelist.visible = False
            self.pad_diff.offset_x -= self.filelist_column_width
            self.pad_diff.width += self.filelist_column_width

            self.pad_filelist.pad.erase()
            self.pad_filelist.refresh(0, 0)
        else:
            self.pad_filelist.visible = True
            self.pad_diff.offset_x += self.filelist_column_width
            self.pad_diff.width -= self.filelist_column_width

            self.update_filelist()

        self.update_diff()

    def update_filelist(self) -> None:
        self.pad_filelist.update(self.filelist, self.selected_file_idx)

    def update_diff(self) -> None:
        self.pad_diff.update(
            self.diff_headers,
            self.diff_contents,
            self.diff_lines(),
            self.diff_longest_line()
        )

    def update_statusbar(self) -> None:
        self.pad_statusbar.pad.erase()

        _, max_x = self.pad_statusbar.pad.getmaxyx()

        diff_longest_line = self.diff_longest_line()
        diff_linenum = min(self.diff_lines(), self.pad_diff.height + self.pad_diff.y)
        diff_colnum = min(diff_longest_line, self.pad_diff.width + self.pad_diff.x)

        leftstring = f' {self.selected_file_idx + 1} / {len(self.filelist)} files  +{self.total_insertions}  -{self.total_deletions}'
        centerstring = ' '
        rightstring = f'({diff_linenum}, {diff_colnum}) / ({self.diff_lines()}, {diff_longest_line}) '

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

    def diff_lines(self) -> int:
        return len(self.diff_headers) + len(self.diff_contents)

    def diff_longest_line(self) -> int:
        return max(
            max( len(line) for line in self.diff_headers ),
            max( len(line) for line in self.diff_contents )
        ) if self.diff_lines() != 0 else 0

def curses_initialize(cui: CursesUi) -> None:
    curses.wrapper(cui.run)