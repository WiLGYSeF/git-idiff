import curses
import typing

from gitdiff import GitFile
from ui.colors import COLOR_ADD, COLOR_REMOVE
from ui.pad import CursesPad

class FileList(CursesPad):
    def __init__(self, window: curses.window, column_width: int):
        self.column_width: int = column_width

        lines, _ = window.getmaxyx()

        super().__init__(window,
            height = lines - 1,
            width = self.column_width,
            offset_y = 0,
            offset_x = 0
        )

        self.visible: bool = True

    def update(self, filelist, selected_file_idx) -> None:
        if not self.visible:
            return

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
            length = 0

            def write(val, attr=curses.A_NORMAL):
                nonlocal length

                if idx == selected_file_idx:
                    attr |= curses.A_REVERSE

                if length + len(val) >= max_x:
                    val = val[len(val) - (max_x - length):]
                if len(val) > 0:
                    self.pad.addstr(idx, length, val, attr)
                    length += len(val)

            write(insertions, curses.color_pair(COLOR_ADD))
            write(' ')
            write(deletions, curses.color_pair(COLOR_REMOVE))
            write(' ')
            write(' ' * (max_x - length - len(fname)))
            write(fname)
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
