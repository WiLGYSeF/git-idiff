import curses

from . import colors
from .diff import DiffPad
from .pad import CursesPad
from .utils import StrAttrFormat, addnstrattrfmt

class StatusBar(CursesPad):
    def __init__(self, win: curses.window):
        lines, columns = win.getmaxyx()

        super().__init__(win,
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

        leftstr = StrAttrFormat(
            f' {selected_file_idx + 1} / {filelist_len} files  {{insertions}}  {{deletions}}',
            {
                'insertions': (
                    f'+{total_insertions}',
                    curses.color_pair(colors.COLOR_ADD) | curses.A_REVERSE
                ),
                'deletions': (
                    f'-{total_deletions}',
                    curses.color_pair(colors.COLOR_REMOVE) | curses.A_REVERSE
                ),
            },
            curses.A_REVERSE
        )
        centerstr = ' '
        rightstr = f'({diff_linenum}, {diff_colnum}) / ({diff_lines}, {diff_longest_line}) '

        width = min(self._width, max_x)
        leftcenter_pad = ' ' * (
            (width - (len(leftstr) + len(centerstr) + len(rightstr))) // 2
        )
        centerright_pad = ' ' * (
            width - (len(leftstr) + len(centerstr) + len(rightstr) + len(leftcenter_pad))
        )

        addnstrattrfmt(
            self.pad,
            0, 0,
            leftstr + leftcenter_pad + centerstr + centerright_pad + rightstr,
            width
        )

        self.refresh(0, 0)
