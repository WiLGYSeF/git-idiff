import curses
import typing

from ..gitdiff import GitFile
from . import colors
from .pad import CursesPad
from .utils import StrAttrFormat, addnstrattrfmt

class FileList(CursesPad):
    def __init__(self, win: curses.window, column_width: int):
        self._column_width: int = column_width

        lines, _ = win.getmaxyx()

        super().__init__(win,
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
            attr = curses.A_REVERSE if idx == selected_file_idx else curses.A_NORMAL
            addnstrattrfmt(self.pad, idx, 0, _gitfile_to_saf(file, attr, max_x), max_x)
            idx += 1

        self.refresh(self.y, 0)

def _gitfile_to_saf(file: GitFile, attr: int, max_x: int) -> StrAttrFormat:
    status, insertions, deletions, fname = _gitfile_to_entry(file, max_x)
    leftpad = ' ' * (max_x - len(status) - len(insertions) - len(deletions) - len(fname) - 2)

    return StrAttrFormat(
        f'{{status}} {{insertions}} {{deletions}}{leftpad}{fname}',
        {
            'status': (status, _status_color(status) | attr),
            'insertions': (insertions, curses.color_pair(colors.COLOR_ADD) | attr),
            'deletions': (deletions, curses.color_pair(colors.COLOR_REMOVE) | attr),
        },
        attr
    )

def _gitfile_to_entry(file: GitFile, max_x: int) -> typing.Tuple[str, str, str, str]:
    status = file.status
    added_str = str(file.insertions) if file.insertions is not None else '-'
    removed_str = str(file.deletions) if file.deletions is not None else '-'
    fname = file.filename

    total_length = len(f'{status} {added_str} {removed_str} {fname}')
    if total_length > max_x:
        fname = '##' + fname[
            max(len(fname) - (max_x - len(f'{status} {added_str} {removed_str} ##')), 0)
            :
        ]

    return (status, added_str, removed_str, fname)

def _status_color(status: str) -> int:
    colormap = {
        'A': colors.COLOR_ADD,
        'C': colors.COLOR_CHANGE,
        'D': colors.COLOR_REMOVE,
        'M': 0,
        'R': colors.COLOR_CHANGE,
        'T': colors.COLOR_CHANGE,
        'U': colors.COLOR_REMOVE,
        'X': 0
    }
    return curses.color_pair(colormap.get(status, 0))
