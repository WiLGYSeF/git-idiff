import curses
import typing

from gitdiff import GitFile
import ui.colors
from ui.pad import CursesPad
from ui.utils import StrAttrFormat, addnstrattrfmt

class FileList(CursesPad):
    def __init__(self, window: curses.window, column_width: int):
        self._column_width: int = column_width

        lines, _ = window.getmaxyx()

        super().__init__(window,
            height = lines - 1,
            width = self._column_width,
            offset_y = 0,
            offset_x = 0
        )

    @property
    def column_width(self) -> int:
        return self._column_width

    @column_width.setter
    def column_width(self, val: int) -> None:
        val = max(val, 1)

        if val != self._column_width:
            self._column_width = val

            max_y, _ = self.pad.getmaxyx()
            self.resize(max_y, val)

    def update(self, filelist, selected_file_idx) -> None:
        self.pad.erase()

        max_y, max_x = self.pad.getmaxyx()
        if len(filelist) >= max_y:
            self.pad.resize(len(filelist) + 1, max_x)

        # create a right border and decrease max_x to account for it
        self.pad.border(
            ' ', 0, ' ', ' ',
            ' ', curses.ACS_VLINE, ' ', curses.ACS_VLINE
        )
        max_x -= 1

        idx = 0
        for file in filelist:
            insertions, deletions, fname = _gitfile_to_entry(file, max_x)
            leftpad = " " * (max_x - len(insertions) - len(deletions) - len(fname) - 1)
            attr = curses.A_REVERSE if idx == selected_file_idx else curses.A_NORMAL

            addnstrattrfmt(self.pad, idx, 0, StrAttrFormat(
                f'{{insertions}} {{deletions}}{leftpad}{fname}',
                {
                    'insertions': (insertions, curses.color_pair(ui.colors.COLOR_ADD) | attr),
                    'deletions': (deletions, curses.color_pair(ui.colors.COLOR_REMOVE) | attr),
                },
                attr
            ), max_x)
            idx += 1

        self.refresh(self.y, 0)

def _gitfile_to_entry(file: GitFile, max_x: int) -> typing.Tuple[str, str, str]:
    added_str = str(file.insertions) if file.insertions is not None else '-'
    removed_str = str(file.deletions) if file.deletions is not None else '-'
    fname = file.filename

    total_length = len(f'{added_str} {removed_str} {fname}')
    if total_length > max_x:
        fname = '##' + fname[
            max(len(fname) - (max_x - len(f'{added_str} {removed_str} ##')), 0)
            :
        ]

    return (added_str, removed_str, fname)
