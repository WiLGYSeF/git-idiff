import curses
import typing

from ..gitdiff import GitDiff
from . import colors
from .pad import CursesPad

class DiffPad(CursesPad):
    def __init__(self, win: curses.window, gitdiff: GitDiff, filelist_column_width: int):
        self.gitdiff: GitDiff = gitdiff

        lines, columns = win.getmaxyx()

        super().__init__(win,
            height = lines - 1,
            width = columns - filelist_column_width,
            offset_y = 0,
            offset_x = filelist_column_width
        )

    def update(self,
        diff_headers: typing.List[str],
        diff_contents: typing.List[str],
        diff_lines: int,
        diff_longest_line: int
    ) -> None:
        self.pad.erase()

        max_y, max_x = self.pad.getmaxyx()
        if diff_lines != max_y or diff_longest_line != max_x:
            self.pad.resize(
                max(diff_lines + 1, self._height),
                max(diff_longest_line + 1, self._width)
            )

        idx = 0
        for line in diff_headers:
            if len(line) == 0:
                idx += 1
                continue

            self.pad.addstr(idx, 0, line, curses.color_pair(colors.COLOR_HEADER))
            idx += 1

        colormap = {
            '+': curses.color_pair(colors.COLOR_ADD),
            '-': curses.color_pair(colors.COLOR_REMOVE),
            '@': curses.color_pair(colors.COLOR_SECTION)
        }

        for line in diff_contents:
            if len(line) == 0:
                idx += 1
                continue

            self.pad.addstr(idx, 0, line, colormap.get(line[0], curses.A_NORMAL))
            idx += 1

        self.refresh(self.y, self.x)
