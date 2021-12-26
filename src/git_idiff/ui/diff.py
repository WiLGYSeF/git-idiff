import curses
import typing

from gitdiff import GitDiff
import ui.colors
from ui.pad import CursesPad

class DiffPad(CursesPad):
    def __init__(self, window: curses.window, gitdiff: GitDiff, filelist_column_width: int):
        self.gitdiff: GitDiff = gitdiff

        lines, columns = window.getmaxyx()

        super().__init__(window,
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

            if self.gitdiff.has_prefix():
                self.pad.addstr(idx, 0, self.gitdiff.line_prefix_str)
                self.pad.addstr(
                    idx, len(self.gitdiff.line_prefix_str),
                    self.gitdiff.noprefix(line),
                    curses.color_pair(ui.colors.COLOR_HEADER)
                )
            else:
                self.pad.addstr(idx, 0, line, curses.color_pair(ui.colors.COLOR_HEADER))
            idx += 1

        for line in diff_contents:
            if len(line) == 0:
                idx += 1
                continue

            noprefix = self.gitdiff.noprefix(line)
            attr = curses.A_NORMAL

            if noprefix[0] == '+':
                attr = curses.color_pair(ui.colors.COLOR_ADD)
            elif noprefix[0] == '-':
                attr = curses.color_pair(ui.colors.COLOR_REMOVE)
            elif noprefix[0] == '@':
                attr = curses.color_pair(ui.colors.COLOR_SECTION)

            if self.gitdiff.has_prefix():
                self.pad.addstr(idx, 0, self.gitdiff.line_prefix_str)
                self.pad.addstr(idx, len(self.gitdiff.line_prefix_str), noprefix, attr)
            else:
                self.pad.addstr(idx, 0, line, attr)
            idx += 1

        self.refresh(self.y, self.x)
