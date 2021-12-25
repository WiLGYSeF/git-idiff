import curses
import typing

import ui.colors
from ui.diff import DiffPad
from ui.pad import CursesPad

class StatusBar(CursesPad):
    def __init__(self, stdscr):
        lines, columns = stdscr.getmaxyx()

        super().__init__(stdscr,
            height = 2,
            width = columns,
            offset_y = lines - 1,
            offset_x = 0
        )

    def update(self,
        pad_diff: DiffPad,
        diff_lines: int,
        diff_longest_line: int,
        selected_file_idx: int,
        filelist_len: int,
        total_insertions: int,
        total_deletions: int
    ) -> None:
        self.pad.erase()

        _, max_x = self.pad.getmaxyx()

        diff_linenum = min(diff_lines, pad_diff.height + pad_diff.y)
        diff_colnum = min(diff_longest_line, pad_diff.width + pad_diff.x)

        leftstr = f' {selected_file_idx + 1} / {filelist_len} files  +{total_insertions}  -{total_deletions}'
        centerstr = ' '
        rightstr = f'({diff_linenum}, {diff_colnum}) / ({diff_lines}, {diff_longest_line}) '

        leftcenter_pad = ' ' * (
            (max_x - (len(leftstr) + len(centerstr) + len(rightstr))) // 2
        )
        centerright_pad = ' ' * (
            max_x - (len(leftstr) + len(centerstr) + len(rightstr) + len(leftcenter_pad))
        )

        self.pad.addstr(
            0, 0,
            (leftstr + leftcenter_pad + centerstr + centerright_pad + rightstr)[:max_x],
            curses.A_REVERSE
        )

        self.refresh(0, 0)